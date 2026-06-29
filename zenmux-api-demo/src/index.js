/**
 * ZenMux API 一次性调用示例
 *
 * 使用: npm start
 */

// .env 由 zenmux.js 自动加载
import { chatCompletion, chatCompletionStream } from "./zenmux.js";

const MODEL = process.env.ZENMUX_DEFAULT_MODEL || "openai/gpt-4o";

async function nonStreamExample() {
  console.log("=== 非流式调用示例 ===\n");

  const result = await chatCompletion({
    messages: [
      { role: "system", content: "你是一个简洁、友好的AI助手。" },
      { role: "user", content: "用一句话介绍你自己" },
    ],
    options: {
      temperature: 0.7,
      max_tokens: 100,
    },
  });

  console.log("回复:", result.choices[0].message.content);
  console.log("模型:", result.model);
  console.log("用量:", result.usage);
}

async function streamExample() {
  console.log("\n=== 流式调用示例 ===\n");

  process.stdout.write("AI: ");
  const result = await chatCompletionStream({
    messages: [
      { role: "user", content: "写一首关于编程的短诗（4句）" },
    ],
    onChunk: (text) => {
      process.stdout.write(text);
    },
    options: {
      temperature: 0.9,
    },
  });

  console.log("\n");
  if (result.usage) {
    console.log(`[Tokens: ${result.usage.total_tokens} 总计]`);
  }
}

async function main() {
  console.log("╔════════════════════════════════════════╗");
  console.log(`║     ZenMux API Demo - ${MODEL}       ║`);
  console.log("╚════════════════════════════════════════╝\n");

  try {
    await nonStreamExample();
    await streamExample();
  } catch (err) {
    console.error("调用失败:", err.message);
  }
}

main();
