# MiniBot MVP 设计文档

## 项目概述
- 基础循环对话 CLI 工具
- 使用 pure `requests` 库调用 OpenRouter API
- 无需 OpenAI SDK 或其他 SDK 依赖

## 环境变量 (.env)
```
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_API_KEY=your-api-key-here
```

## 依赖
- requests
- python-dotenv
- pydantic

## 功能
1. 基础循环对话 (stdin/stdout)
2. SSE 流式响应输出
3. 支持中文输入输出
4. 动态工具注入 (#tag)
5. 工具调用循环 (max 30)

## 工具
- get_weather: 获取天气 (stub)
- read: 读取 workspace/ 文件
- write: 写入 workspace/ 文件
- patch: 修补文件
- exec: 执行命令 (需确认)

## Milestones
1. [x] 用 `requests` 实现基础对话 + 流式输出 + reasoning 显示
2. [x] 5 个工具 + #tag 动态注入 + 工具调用循环
3. [ ] 下一步...