/**
 * 交互式命令行聊天工具
 * 支持流式输出、多轮对话、模型切换
 *
 * 使用: npm run chat
 */

// .env 由 zenmux.js 自动加载
import readline from "node:readline";
import { chatCompletionStream, getAvailableModels } from "./zenmux.js";

const MODEL = process.env.ZENMUX_DEFAULT_MODEL || "openai/gpt-4o";

function createRL() {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
}

function ask(rl, question) {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
}

function printDivider(char = "─", length = 50) {
  console.log(char.repeat(length));
}

async function main() {
  console.clear();
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║           ZenMux AI 命令行聊天工具               ║");
  console.log("╠══════════════════════════════════════════════════╣");
  console.log(`║  模型: ${MODEL.padEnd(42)}║`);
  console.log("║  输入 /help 查看命令   输入 exit 退出            ║");
  console.log("╚══════════════════════════════════════════════════╝");
  console.log("");

  const rl = createRL();
  const messages = [];

  // 可选的系统提示
  const systemPrompt = await ask(rl, "系统提示词 (可选，直接回车跳过): ");
  if (systemPrompt.trim()) {
    messages.push({ role: "system", content: systemPrompt.trim() });
  }
  console.log("");

  while (true) {
    const input = await ask(rl, "你: ");

    // 命令处理
    if (input.toLowerCase() === "exit" || input.toLowerCase() === "quit") {
      console.log("\n再见！👋");
      break;
    }

    if (input === "/help") {
      console.log(`
命令列表:
  /help     - 显示此帮助信息
  /clear    - 清空对话历史
  /models   - 查看可用模型列表
  /model    - 查看当前模型
  /history  - 查看对话历史
  exit      - 退出程序
`);
      continue;
    }

    if (input === "/clear") {
      messages.length = 0;
      console.log("✅ 对话历史已清空\n");
      continue;
    }

    if (input === "/models") {
      console.log("\n可用模型列表:");
      const models = getAvailableModels();
      models.forEach((m) => {
        const marker = m.id === MODEL ? " ← 当前" : "";
        console.log(`  [${m.provider}] ${m.name}  (${m.id})${marker}`);
      });
      console.log("");
      continue;
    }

    if (input === "/model") {
      console.log(`当前模型: ${MODEL}\n`);
      continue;
    }

    if (input === "/history") {
      console.log("\n对话历史:");
      if (messages.length === 0) {
        console.log("  (空)");
      } else {
        messages.forEach((m, i) => {
          console.log(`  [${i}] ${m.role}: ${m.content.substring(0, 80)}${m.content.length > 80 ? "..." : ""}`);
        });
      }
      console.log("");
      continue;
    }

    if (!input.trim()) continue;

    // 发送消息
    messages.push({ role: "user", content: input });

    process.stdout.write("\nAI: ");
    try {
      const result = await chatCompletionStream({
        model: MODEL,
        messages,
        onChunk: (text) => {
          process.stdout.write(text);
        },
      });

      console.log("\n");
      messages.push({ role: "assistant", content: result.content });

      // 显示 token 用量
      if (result.usage) {
        console.log(
          `[Tokens: ${result.usage.prompt_tokens} 输入 + ${result.usage.completion_tokens} 输出 = ${result.usage.total_tokens} 总计]\n`
        );
      }
    } catch (err) {
      console.log(`\n❌ 错误: ${err.message}\n`);
      messages.pop(); // 移除失败的用户消息
    }
  }

  rl.close();
}

main().catch((err) => {
  console.error("启动失败:", err.message);
  process.exit(1);
});
