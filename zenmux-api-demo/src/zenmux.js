/**
 * ZenMux API 客户端
 * 兼容 OpenAI Chat Completions 协议
 * 零依赖 —— 手动加载 .env
 */

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// 手动加载 .env 文件（零依赖）
const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(__dirname, "..", ".env");
try {
  const envContent = readFileSync(envPath, "utf-8");
  for (const line of envContent.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIdx = trimmed.indexOf("=");
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const value = trimmed.slice(eqIdx + 1).trim();
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
} catch {
  // .env 文件不存在时静默跳过
}

const BASE_URL = "https://zenmux.ai/api/v1";

function getConfig() {
  const apiKey = process.env.ZENMUX_API_KEY;
  if (!apiKey) {
    throw new Error("请在 .env 文件中设置 ZENMUX_API_KEY");
  }
  return {
    apiKey,
    defaultModel: process.env.ZENMUX_DEFAULT_MODEL || "openai/gpt-4o",
    siteUrl: process.env.ZENMUX_SITE_URL || "http://localhost:3000",
    siteName: process.env.ZENMUX_SITE_NAME || "ZenMux-Demo",
  };
}

/**
 * 发送聊天补全请求（非流式）
 */
export async function chatCompletion({ model, messages, options = {} }) {
  const config = getConfig();

  const body = {
    model: model || config.defaultModel,
    messages,
    ...options,
  };

  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": config.siteUrl,
      "X-Title": config.siteName,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      `ZenMux API 错误 [${response.status}]: ${error.error?.message || response.statusText}`
    );
  }

  return response.json();
}

/**
 * 发送聊天补全请求（流式 SSE）
 */
export async function chatCompletionStream({
  model,
  messages,
  onChunk,
  options = {},
}) {
  const config = getConfig();

  const body = {
    model: model || config.defaultModel,
    messages,
    stream: true,
    ...options,
  };

  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": config.siteUrl,
      "X-Title": config.siteName,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      `ZenMux API 错误 [${response.status}]: ${error.error?.message || response.statusText}`
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";
  let finishReason = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      const data = trimmed.slice(6);
      if (data === "[DONE]") continue;

      try {
        const parsed = JSON.parse(data);
        const choice = parsed.choices?.[0];

        if (choice?.delta?.content) {
          fullContent += choice.delta.content;
          if (onChunk) onChunk(choice.delta.content);
        }

        if (choice?.finish_reason) {
          finishReason = choice.finish_reason;
        }

        // 记录 usage 信息（通常在最后一个 chunk 中）
        if (parsed.usage) {
          return {
            content: fullContent,
            finishReason,
            usage: parsed.usage,
            model: parsed.model,
          };
        }
      } catch {
        // 跳过解析失败的行
      }
    }
  }

  return {
    content: fullContent,
    finishReason,
  };
}

/**
 * 获取可用模型列表（简化版，返回常用模型）
 */
export function getAvailableModels() {
  return [
    { id: "openai/gpt-5.4", name: "GPT-5.4", provider: "OpenAI" },
    { id: "openai/gpt-5", name: "GPT-5", provider: "OpenAI" },
    { id: "openai/gpt-4o", name: "GPT-4o", provider: "OpenAI" },
    { id: "openai/gpt-4.1", name: "GPT-4.1", provider: "OpenAI" },
    { id: "openai/o4-mini", name: "o4-mini", provider: "OpenAI" },
    { id: "anthropic/claude-opus-4-20250514", name: "Claude Opus 4", provider: "Anthropic" },
    { id: "anthropic/claude-sonnet-4-20250514", name: "Claude Sonnet 4", provider: "Anthropic" },
    { id: "google/gemini-2.5-pro", name: "Gemini 2.5 Pro", provider: "Google" },
    { id: "google/gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Google" },
    { id: "deepseek/deepseek-chat", name: "DeepSeek V3", provider: "DeepSeek" },
    { id: "deepseek/deepseek-r1", name: "DeepSeek R1", provider: "DeepSeek" },
    { id: "meta-llama/llama-4-maverick", name: "Llama 4 Maverick", provider: "Meta" },
    { id: "qwen/qwen3-235b-a22b", name: "Qwen3 235B", provider: "Alibaba" },
  ];
}
