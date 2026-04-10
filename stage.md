# Step 2: 工具调用

## 新增功能
已添加 5 个工具:
- get_weather: 获取天气 (stub)
- read: 读取 workspace/ 文件
- write: 写入 workspace/ 文件
- patch: 修补文件
- exec: 执行命令 (需确认)

## #tag 用法
在输入中使用 #tag 动态注入工具:
- `#basic` - 全部 5 个工具
- `#read` - 读取工具
- `#write` - 写入工具
- `#patch` - 修补工具
- `#exec` - 执行工具

示例: "写一个 fib.py #basic"

## 运行
```bash
python main.py
```