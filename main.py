import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
MODEL = "openrouter/free"
URL = f"{API_BASE}/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/RGSS3/minibot",
    "X-Title": "MiniBot",
}

def get_content(chunk):
    return chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

REASONING_KEYS = ["reasoning", "reasoning_content"]
def get_reasoning(chunk):
    delta = chunk.get("choices", [{}])[0].get("delta", {})
    for key in REASONING_KEYS: 
        if key in delta:
            return delta[key]
    return None

    

def stream_response(messages):
    resp = requests.post(
        URL,
        headers=HEADERS,
        json={"model": MODEL, "messages": messages, "stream": True},
        stream=True,
    )
    for line in resp.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    reasoning = get_reasoning(chunk)
                    if reasoning:
                        yield {"type": "reasoning", "content": reasoning}
                    content = get_content(chunk)
                    if content:
                        yield {"type": "normal", "content": content}
                except json.JSONDecodeError:
                    pass


def main():
    messages = []
    print("MiniBot (输入 exit 退出)")
    while True:
        user_input = input("\n> ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        print("\n助手: ", end="")
        full_content = ""
        mode = ""
        for item in stream_response(messages):
            if item["type"] == "reasoning":
                if mode != "reasoning":
                    print("\n🤔 ", end="", flush=True)
                    mode = "reasoning"
                print(item["content"].replace("\n", "\n>> "), end="", flush=True)
                full_content += item["content"]
            else:
                if mode != "normal":
                    print("\n", flush=True)
                    mode = "normal"
                print(item["content"], end="", flush=True)
                full_content += item["content"]
        print()
        messages.append({"role": "assistant", "content": full_content})


if __name__ == "__main__":
    main()