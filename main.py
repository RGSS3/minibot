import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from tools import TOOLS, TOOL_GROUPS, get_tool_schemas

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
MODEL = "openrouter/free"
URL = f"{API_BASE}/chat/completions"
MAX_TOOL_LOOP = 30

TOOL_SCHEMAS = get_tool_schemas()


def parse_input_with_tools(user_input):
    """解析输入中的 #tag 并返回 (clean_input, tools)"""
    import re
    tags = re.findall(r"#(\w+)", user_input)
    if not tags:
        return user_input, []
    clean = re.sub(r"#\w+", "", user_input).strip()
    tools = []
    for tag in tags:
        if tag in TOOL_GROUPS:
            tools.extend(TOOL_GROUPS[tag])
    return clean, list(set(tools))


def build_system_prompt(tools_used):
    if not tools_used:
        return "你是一个智能助手。"
    tool_list = "\n".join(f"- {name}: {TOOL_SCHEMAS[name]['description']}" for name in tools_used)
    return f"""你是一个智能助手，可以使用以下工具来帮助用户。

## 工具

{tool_list}

## 工作目录
所有文件操作都在 workspace/ 目录下。

<environment_details>
Current time: {datetime.now().isoformat()}
</environment_details>"""

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
        tool_schemas = [{"type": "function", "function": TOOL_SCHEMAS[name]} for name in tools if name in TOOL_SCHEMAS]
        payload["tools"] = tool_schemas
    resp = requests.post(
        URL,
        headers=HEADERS,
        json=payload,
        stream=True,
    )
    finish_reason = None
    current_tc_id = None
    current_tc_name = None
    current_tc_args = ""
    for line in resp.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
                    reasoning = get_reasoning(chunk)
                    if reasoning:
                        yield {"type": "reasoning", "content": reasoning}
                    content = get_content(chunk)
                    if content:
                        yield {"type": "normal", "content": content}
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if delta.get("tool_calls"):
                        for tc in delta["tool_calls"]:
                            tc_id = tc.get("id")
                            tc_func = tc.get("function", {})
                            tc_name = tc_func.get("name", "")
                            tc_args_chunk = tc_func.get("arguments", "")
                            if tc_id and tc_name:
                                if current_tc_id and current_tc_name:
                                    yield {"type": "tool_call", "content": {"id": current_tc_id, "function": {"name": current_tc_name, "arguments": current_tc_args}}}
                                current_tc_id = tc_id
                                current_tc_name = tc_name
                                current_tc_args = tc_args_chunk
                            elif tc_args_chunk:
                                current_tc_args += tc_args_chunk
                except json.JSONDecodeError:
                    pass
    if current_tc_id and current_tc_name:
        yield {"type": "tool_call", "content": {"id": current_tc_id, "function": {"name": current_tc_name, "arguments": current_tc_args}}}
    yield {"type": "finish", "reason": finish_reason}


def main():
    print("MiniBot (输入 exit 退出)")
    while True:
        user_input = input("\n> ")
        if user_input.lower() == "exit":
            break
        
        clean_input, requested_tools = parse_input_with_tools(user_input)
        if not clean_input:
            continue
        
        tools_used = set(requested_tools)
        messages = [{"role": "system", "content": build_system_prompt(tools_used)}]
        messages.append({"role": "user", "content": clean_input})
        
        loop_count = 0
        while loop_count < MAX_TOOL_LOOP:
            loop_count += 1
            print("\n助手: ", end="")
            full_content = ""
            mode = ""
            tool_calls = []
            finish_reason = None
            for item in stream_response(messages, tools=list(tools_used)):
                if item["type"] == "finish":
                    finish_reason = item["reason"]
                elif item["type"] == "reasoning":
                    if mode != "reasoning":
                        print("\n🤔 ", end="", flush=True)
                        mode = "reasoning"
                    print(item["content"].replace("\n", "\n>> "), end="", flush=True)
                    full_content += item["content"]
                elif item["type"] == "tool_call":
                    tc_data = item["content"]
                    if isinstance(tc_data, dict) and "function" in tc_data:
                        tool_calls.append(tc_data)
                        func_name = tc_data["function"].get("name")
                        if func_name:
                            tools_used.add(func_name)
                else:
                    if mode != "normal":
                        print("\n", flush=True)
                        mode = "normal"
                    print(item["content"], end="", flush=True)
                    full_content += item["content"]
            print()
            messages.append({"role": "assistant", "content": full_content})
            
            if not tool_calls or (finish_reason and finish_reason.lower() == "stop"):
                break
            for tc in tool_calls:
                name = tc["function"]["name"]
                args_str = tc["function"].get("arguments", "{}")
                if not args_str:
                    args_str = "{}"
                args = json.loads(args_str)
                print(f"\n[调用工具] {name}")
                print(f"[工具参数] {args}")
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