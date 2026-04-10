# 快速开始

## 安装依赖
```bash
pip install -r requirements.txt
```

## 配置 API Key
1. 访问 https://openrouter.ai/ 注册账号
2. 获取 API Key
3. 将 Key 填入 `.env` 文件的 `OPENAI_API_KEY`

## 代理配置
如果使用 Clash Verge 等代理工具，需要在 `.env` 中手动配置代理(假设你的是7897端口):
```
https_proxy=http://127.0.0.1:7897
http_proxy=http://127.0.0.1:7897
```

## 运行
```bash
python main.py
```