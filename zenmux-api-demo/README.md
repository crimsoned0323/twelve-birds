# ZenMux API Demo

一个使用 ZenMux AI API 网关的示例项目，支持调用 200+ 大模型。

## 项目结构

```
zenmux-api-demo/
├── src/
│   ├── zenmux.js       # API 客户端核心模块
│   ├── index.js         # 一次性调用示例
│   ├── chat.js          # 交互式命令行聊天工具
│   └── list-models.js   # 查看可用模型列表
├── .env.example         # 环境变量示例
├── package.json
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd zenmux-api-demo
npm install
```

### 2. 配置 API Key

```bash
# 复制 .env.example 为 .env
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

编辑 `.env` 文件，填入你的 ZenMux API Key:
```
ZENMUX_API_KEY=sk-ai-v1-your-api-key-here
ZENMUX_DEFAULT_MODEL=openai/gpt-4o
```

### 3. 运行示例

```bash
# 一次性调用示例 (非流式 + 流式)
npm start

# 交互式命令行聊天工具
npm run chat

# 查看可用模型列表
npm run models
```

## 功能说明

### 核心模块 (`src/zenmux.js`)

- `chatCompletion()` - 非流式聊天补全
- `chatCompletionStream()` - 流式 SSE 聊天补全
- `getAvailableModels()` - 获取常用模型列表

### 交互式聊天 (`npm run chat`)

支持命令:
- `/help` - 查看帮助
- `/models` - 查看可用模型
- `/model` - 查看当前模型
- `/history` - 查看对话历史
- `/clear` - 清空对话历史
- `exit` - 退出

### 支持的模型

| 厂商 | 模型 | ID |
|------|------|-----|
| OpenAI | GPT-5 | openai/gpt-5 |
| OpenAI | GPT-4o | openai/gpt-4o |
| OpenAI | GPT-4.1 | openai/gpt-4.1 |
| OpenAI | o4-mini | openai/o4-mini |
| Anthropic | Claude Opus 4 | anthropic/claude-opus-4-20250514 |
| Anthropic | Claude Sonnet 4 | anthropic/claude-sonnet-4-20250514 |
| Google | Gemini 2.5 Pro | google/gemini-2.5-pro |
| Google | Gemini 2.5 Flash | google/gemini-2.5-flash |
| DeepSeek | DeepSeek V3 | deepseek/deepseek-chat |
| DeepSeek | DeepSeek R1 | deepseek/deepseek-r1 |
| Meta | Llama 4 Maverick | meta-llama/llama-4-maverick |
| Alibaba | Qwen3 235B | qwen/qwen3-235b-a22b |

## ZenMux 特性

- **统一 API**: 兼容 OpenAI Chat Completions 协议
- **智能路由**: 自动选择最优模型供应商
- **模型保险**: 降低大模型幻觉风险
- **200+ 模型**: 一个 API Key 访问所有主流模型

## 文档

- [ZenMux 官方文档](https://zenmux.ai/docs)
- [API 参考](https://zenmux.ai/docs/api/overview.html)

## License

MIT
