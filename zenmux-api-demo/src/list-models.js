/**
 * 查看 ZenMux 常用模型列表
 *
 * 使用: npm run models
 */

import { getAvailableModels } from "./zenmux.js";

console.log("╔══════════════════════════════════════════════════════════════════╗");
console.log("║                   ZenMux 可用模型列表                            ║");
console.log("╚══════════════════════════════════════════════════════════════════╝\n");

const models = getAvailableModels();

// 按 provider 分组
const grouped = {};
models.forEach((m) => {
  if (!grouped[m.provider]) grouped[m.provider] = [];
  grouped[m.provider].push(m);
});

for (const [provider, list] of Object.entries(grouped)) {
  console.log(`📦 ${provider}`);
  console.log("─".repeat(56));
  list.forEach((m) => {
    console.log(`   ${m.name.padEnd(25)} ${m.id}`);
  });
  console.log("");
}

console.log(`共 ${models.length} 个模型`);
console.log("\n💡 在 .env 中设置 ZENMUX_DEFAULT_MODEL 可切换默认模型");
