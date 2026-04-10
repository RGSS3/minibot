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

## 功能
1. 基础循环对话 (stdin/stdout)
2. SSE 流式响应输出
3. 支持中文输入输出

## Milestones
1. [x] 用 `requests` 实现基础循环对话 (~30-40行)
2. [ ] 支持基本工具和MCP
3. [ ] 考虑带着guardrails和harness的工具循环