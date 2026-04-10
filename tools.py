import os
from pydantic import BaseModel, Field


class GetWeatherParams(BaseModel):
    """获取天气信息"""
    pass


def get_weather(params: GetWeatherParams) -> str:
    """获取当前天气（stub）"""
    return "以太风 (Elona meme)"


class ReadParams(BaseModel):
    """读取文件内容"""
    filename: str = Field(..., description="文件名")
    start: int = Field(default=1, ge=1, description="起始行号")
    count: int = Field(default=10, ge=1, le=50, description="读取行数")


def read(params: ReadParams) -> str:
    """读取 workspace/{filename} 的内容"""
    filepath = os.path.join("workspace", params.filename)
    if not os.path.exists(filepath):
        return f"文件不存在: {params.filename}"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        total = len(lines)
        start = params.start - 1
        end = start + params.count
        selected = lines[start:end]
        result = "".join(selected)
        if end < total:
            result += f"\n... 还有 {total - end} 行"
        return result
    except Exception as e:
        return f"读取失败: {e}"


class WriteParams(BaseModel):
    """写入文件内容"""
    filename: str = Field(..., description="文件名")
    content: str = Field(..., max_length=32768, description="文件内容（按行）")


def write(params: WriteParams) -> str:
    """写入 workspace/{filename}"""
    lines = params.content.split("\n")
    if len(lines) > 50:
        return f"错误: 行数超过50行（当前{len(lines)}行）"
    filepath = os.path.join("workspace", params.filename)
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(params.content)
        return f"已写入 {params.filename}（{len(lines)}行）"
    except Exception as e:
        return f"写入失败: {e}"


class PatchParams(BaseModel):
    """修补文件内容"""
    filename: str = Field(..., description="文件名")
    old_str: str = Field(..., description="原字符串")
    new_str: str = Field(..., description="新字符串")


def patch(params: PatchParams) -> str:
    """修补 workspace/{filename} 中的内容"""
    filepath = os.path.join("workspace", params.filename)
    if not os.path.exists(filepath):
        return f"文件不存在: {params.filename}"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(params.old_str)
        if count == 0:
            return "错误: 找不到目标字符串"
        if count > 1:
            return f"错误: 目标字符串出现{count}次，不唯一"
        new_content = content.replace(params.old_str, params.new_str, 1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"已修补 {params.filename}"
    except Exception as e:
        return f"修补失败: {e}"


class ExecParams(BaseModel):
    """执行命令"""
    cmd: str = Field(..., description="命令（保留用于approval扩展）")
    args: list[str] = Field(default_factory=list, description="命令参数数组")
    path: str = Field(default="workspace", description="工作目录")


def exec_(params: ExecParams) -> str:
    """执行命令并返回结果（同步接口，需要用户确认）"""
    cmd_str = params.cmd + " " + " ".join(params.args)
    print(f"\n[执行命令] {cmd_str} (cwd: {params.path})")
    confirm = input("确认执行? (y/n): ")
    if confirm.lower() != "y":
        return "用户取消执行"
    import subprocess
    result = subprocess.run(
        cmd_str,
        shell=True,
        cwd=params.path,
        capture_output=True,
        text=True,
    )
    return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\n返回码: {result.returncode}"


TOOLS = {
    "get_weather": (get_weather, GetWeatherParams),
    "read": (read, ReadParams),
    "write": (write, WriteParams),
    "patch": (patch, PatchParams),
    "exec": (exec_, ExecParams),
}


def get_tool_schemas():
    """获取所有工具的 schema"""
    schemas = {}
    for name, (func, model_cls) in TOOLS.items():
        schemas[name] = {
            "description": func.__doc__.strip(),
            "parameters": model_cls.model_json_schema(),
        }
    return schemas