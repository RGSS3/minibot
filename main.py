import os
import sys
import json
import requests
from dotenv import load_dotenv
from tools import TOOLS, get_tool_schemas

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
MODEL = "openrouter/free"
URL = f"{API_BASE}/chat/completions"

TOOL_SCHEMAS = get_tool_schemas()

SYSTEM_PROMPT = f"""你是一个智能助手，可以使用以下工具来帮助用户。

## 工具

{json.dumps(TOOL_SCHEMAS, indent=2, ensure_ascii=False)}

## 工作目录
所有文件操作都在 workspace/ 目录下。"""

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

    

def stream_response(messages, tools=None):
    payload = {"model": MODEL, "messages": messages, "stream": True}
    if tools:
        payload["tools"] = [{"type": "function", "function": s} for s in TOOL_SCHEMAS.values()]
    resp = requests.post(
        URL,
        headers=HEADERS,
        json=payload,
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
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if delta.get("tool_calls"):
                        for tc in delta["tool_calls"]:
                            yield {"type": "tool_call", "content": tc}
                except json.JSONDecodeError:
                    pass


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("MiniBot (输入 exit 退出)")
    while True:
        user_input = input("\n> ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        
        while True:
            print("\n助手: ", end="")
            full_content = ""
            mode = ""
            tool_calls = []
            for item in stream_response(messages, tools=True):
                if item["type"] == "reasoning":
                    if mode != "reasoning":
                        print("\n🤔 ", end="", flush=True)
                        mode = "reasoning"
                    print(item["content"].replace("\n", "\n>> "), end="", flush=True)
                    full_content += item["content"]
                elif item["type"] == "tool_call":
                    tool_calls.append(item["content"])
                else:
                    if mode != "normal":
                        print("\n", flush=True)
                        mode = "normal"
                    print(item["content"], end="", flush=True)
                    full_content += item["content"]
            print()
            messages.append({"role": "assistant", "content": full_content})
            
            if not tool_calls:
                break
            for tc in tool_calls:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                print(f"\n[调用工具] {name}")
                func, param_cls = TOOLS[name]
                validated = param_cls(**args)
                result = func(validated)
                print(f"[工具返回] {result}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result
                })


if __name__ == "__main__":
    main()