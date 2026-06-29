/**
 * GPT 总评 v5 剧本
 * 提取代表性样本 → ZenMux API → GPT 评审报告
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chatCompletion } from "./zenmux.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, "..", "..");
const MODEL = process.env.ZENMUX_DEFAULT_MODEL || "openai/gpt-4o";

// ============================================================
// 1. 读取设定文档（上下文）
// ============================================================
const settingPath = resolve(PROJECT_ROOT, "设定文档", "设定和核心角色.txt");
const setting = readFileSync(settingPath, "utf-8");

// ============================================================
// 2. 读取 v5 剧本并提取代表性样本
// ============================================================
const v5Path = resolve(PROJECT_ROOT, "十二飞鸟_全剧本合集_v5.txt");
const v5Raw = readFileSync(v5Path, "utf-8");
const v5Lines = v5Raw.split("\n");

// 找到各 Day 的起始行号
function findDayStarts(lines) {
  const dayStarts = {};
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^={5,}\s*Day\s+(\d+)\s/g);
    if (m) {
      const day = parseInt(m[0].match(/\d+/)[0]);
      if (!dayStarts[day]) dayStarts[day] = i;
    }
  }
  return dayStarts;
}

const dayStarts = findDayStarts(v5Lines);
console.log(`v5 总行数: ${v5Lines.length}`);
console.log(`找到 Day 标记: ${Object.keys(dayStarts).length} 个`);

// 提取策略：选取关键段落
function extractRange(start, end) {
  return v5Lines.slice(start, end).join("\n");
}

const samples = [];

// A. Day 1-3（开篇）
const d1 = dayStarts[1] || 0;
const d4 = dayStarts[4] || d1 + 300;
samples.push({ label: "【样本A】Day 1-3 开篇", text: extractRange(d1, d4) });

// B. Day 13-17（第一批未遂节点链）
const d13 = dayStarts[13] || d1;
const d18 = dayStarts[18] || d13 + 500;
samples.push({ label: "【样本B】Day 13-17 含未遂节点链（巢燕/白鹤/青鹭/诡鹀/双雀/银鹮）", text: extractRange(d13, d18) });

// C. Day 25-30（中盘+未遂节点链密集区）
const d25 = dayStarts[25] || d18;
const d31 = dayStarts[31] || d25 + 600;
samples.push({ label: "【样本C】Day 25-30 中盘含未遂节点链（诡鹀素颜/银鹮遗忘本子/神鸦无味道/双雀手掌朝上）", text: extractRange(d25, d31) });

// D. Day 37-43（高潮+未遂节点链+分叉点）
const d37 = dayStarts[37] || d31;
const d44 = dayStarts[44] || d37 + 800;
samples.push({ label: "【样本D】Day 37-43 高潮含未遂节点链（神鸦水流/诡鹀你觉得我像谁/银鹮被划掉/双雀黑暗里的字）+ Day43分叉", text: extractRange(d37, d44) });

// E. Day 55-59（结局路线）
const d55 = dayStarts[55] || d44;
const d60 = dayStarts[60] || v5Lines.length;
samples.push({ label: "【样本E】Day 55-59 结局路线", text: extractRange(d55, d60) });

// 统计样本大小
let totalChars = 0;
for (const s of samples) {
  totalChars += s.text.length;
  console.log(`  ${s.label}: ${s.text.length} 字`);
}
console.log(`样本总字数: ${totalChars}`);

// ============================================================
// 3. 构建 GPT 评审 prompt
// ============================================================
const systemPrompt = `你是一位资深的互动叙事游戏剧本评审专家，擅长恋爱悬疑/视觉小说类型的剧本分析。
你将收到一部名为《十二飞鸟》的互动恋爱悬疑游戏剧本的代表性样本（共5段，覆盖开篇/中盘/高潮/结局）以及项目设定文档。

请基于以下维度进行全面专业的总评：

1. **总体印象**（10分制评分+一句话总结）
2. **叙事架构**（60天时间轴/双线叙事/四结局分支/23种BE的设计合理性）
3. **角色塑造**（12位核心角色的防线崩塌弧成熟度、未遂节点链的微裂痕质量、角色声音一致性）
4. **感官沉浸**（嗅觉优先描写/短句节奏/情感克制/是否达到行业标杆"媚肉之香"的水准）
5. **亲密度节奏**（未遂节点链对"退让→收回"模式的执行质量、裂痕信号是否"极其微小"）
6. **悬疑张力**（毒品案×连环杀人案双线/Day43分叉点/BE触发逻辑）
7. **具体亮点**（至少5个，引用原文）
8. **具体问题**（分P0/P1/P2三级，每级至少2个，引用原文）
9. **改进建议**（可操作的优先级排序）
10. **对标评估**（与"媚肉之香"的五维度对比：感官密度/亲密度节奏/张力节奏/角色吸引力/玩家能动性）

评审要求：
- 引用原文时标注【样本X】和具体段落
- 评分要有依据，不可泛泛而谈
- 问题要具体到行/段落级别
- 改进建议要可操作
- 全文用中文，专业但不晦涩`;

const userContent = `# 《十二飞鸟》v5 全剧本合集 GPT 总评请求

## 项目基本信息
- 类型：互动恋爱悬疑游戏剧本（卧底题材）
- 规模：60天游戏进度，27种结局（23 BE + 4 TE），20,215行
- 主角：黑羽哲也（卧底警察，异常敏锐嗅觉，极度寡言≤15字/句）
- 背景：日本大阪风俗俱乐部，毒品案×连环杀人案双线
- v5新增：10角色31个未遂节点链（防线崩塌弧微裂痕，精确插入Day13~40）

---

## 设定文档（上下文）

${setting}

---

## 剧本代表性样本（5段）

${samples.map(s => `\n### ${s.label}\n\n${s.text}`).join("\n\n---\n\n")}

---

请基于以上材料进行全面专业的总评。`;

console.log(`\nSystem prompt: ${systemPrompt.length} 字`);
console.log(`User content: ${userContent.length} 字`);
console.log(`总输入: ${(systemPrompt.length + userContent.length)} 字 ≈ ${Math.round((systemPrompt.length + userContent.length) / 4)} tokens`);
console.log(`\n正在调用 ${MODEL} ...`);

// ============================================================
// 4. 调用 ZenMux API
// ============================================================
try {
  const result = await chatCompletion({
    model: MODEL,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userContent },
    ],
    options: {
      temperature: 0.7,
      max_tokens: 8000,
    },
  });

  const content = result.choices[0].message.content;
  const usage = result.usage;
  const modelUsed = result.model;

  console.log(`\n${"=".repeat(60)}`);
  console.log(`GPT 总评完成！`);
  console.log(`模型: ${modelUsed}`);
  console.log(`Token 用量: prompt=${usage?.prompt_tokens || "?"} / completion=${usage?.completion_tokens || "?"} / total=${usage?.total_tokens || "?"}`);
  console.log(`回复长度: ${content.length} 字`);
  console.log(`${"=".repeat(60)}\n`);

  // 输出到控制台
  console.log(content);

  // 保存报告
  const reportPath = resolve(PROJECT_ROOT, "GPT_v5_剧本总评报告.md");
  const reportHeader = `# 《十二飞鸟》v5 全剧本合集 GPT 总评报告\n\n> 评审模型: ${modelUsed}  \n> 评审日期: 2026-06-30  \n> 评审对象: 十二飞鸟_全剧本合集_v5.txt (20,215行 / 1,131KB)  \n> Token 用量: ${usage?.total_tokens || "?"} (prompt=${usage?.prompt_tokens || "?"}, completion=${usage?.completion_tokens || "?"})  \n> 样本覆盖: Day 1-3 / Day 13-17 / Day 25-30 / Day 37-43 / Day 55-59\n\n---\n\n`;
  writeFileSync(reportPath, reportHeader + content, "utf-8");
  console.log(`\n报告已保存至: ${reportPath}`);

} catch (err) {
  console.error("调用失败:", err.message);
  process.exit(1);
}
