import requests
import json
import traceback
import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAIError, RateLimitError, OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type


# # Get path to .env in parent directory
# env_path = Path(__file__).resolve().parent.parent / "api" / ".env"

# # Load it
# load_dotenv(dotenv_path=env_path)


api_key = st.secrets["api"]["OPENAI_API_KEY"]

# Initialize OpenAI client with your API key
client = OpenAI(api_key=api_key )
                




def ask_llama3_stream_false(prompt: str, model: str = "llama3.1") -> str:
    url = "http://localhost:11434/api/chat"
    response = requests.post(url, json={
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }, headers={"Content-Type": "application/json"})

    response.raise_for_status()
    return response.json()["message"]["content"].strip()



def ask_llama3(prompt: str, model="llama3.1"):
    url = "http://localhost:11434/api/generate"
    response = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True,
    )

    full_text = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                full_text += data.get("response", "")
            except json.JSONDecodeError:
                continue  # Skip malformed lines (rare)

    return full_text

def ask_mistral(prompt: str, model="mistral"):
    url = "http://localhost:11434/api/generate"
    response = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True,
    )

    full_text = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                full_text += data.get("response", "")
            except json.JSONDecodeError:
                continue  # Skip malformed lines (rare)

    return full_text




import tiktoken

# OpenAI context limits per model
MODEL_LIMITS = {
    "o4-mini": {"context": 200_000, "output": 100_000},
    "gpt-4o": {"context": 128_000, "output": 16_384},
    "gpt-3.5-turbo": {"context": 16_000, "output": 4_096},
    "gpt-4.1-nano-2025-04-14": {"context": 1_047_576, "output": 32_768},
    "gpt-oss-120b": {"context": 131_072, "output": 131_072}
}

def count_tokens(text: str, model) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def get_max_tokens(prompt: str, model: str) -> int:
    input_tokens = count_tokens(prompt, model)
    context_limit = MODEL_LIMITS.get(model, {}).get("context", 200_000)
    output_limit = MODEL_LIMITS.get(model, {}).get("output", 100_000)

    max_available = context_limit - input_tokens
    return min(max_available, output_limit, 48_000)  # Add a safe cap

@retry(
    wait=wait_random_exponential(min=30, max=60),  # wait 1–60s between retries
    stop=stop_after_attempt(10),  # try up to 5 times
    retry=retry_if_exception_type(RateLimitError),  # only retry on rate limit
    reraise=True  # re-raises final exception if all retries fail
)



def ask_openai_sync(prompt: str, model: str = "gpt-oss-120b") -> str:
    try:
        input_tokens = count_tokens(prompt, model)
        max_tokens = get_max_tokens(prompt, model)

        print(f"📥 Input Tokens: {input_tokens}")
        print(f"📤 Max Output Tokens: {max_tokens}")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_completion_tokens=max_tokens
        )

        output = response.choices[0].message.content.strip()
        output_tokens = count_tokens(output, model)

        print(f"✅ Output Tokens: {output_tokens}")
        return output

    except OpenAIError as e:
        print(f"🚫 OpenAI API error: {e}")
        traceback.print_exc()
        raise  # Reraise for tenacity to catch and retry

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return f"❌ Unexpected Error: {e}"


def ask_openai_chat_streaming(messages: list, model: str = "gpt-oss-120b"):
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token
    except Exception as e:
        yield f"\n❌ Error: {e}"
