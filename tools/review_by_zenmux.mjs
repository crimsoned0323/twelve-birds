#!/usr/bin/env node
/**
 * 十二飞鸟 · ZenMux 剧本审核工具
 * 用大模型批量检查剧本文件的: 日语残留 / 角色红线 / 事实一致性 / 格式问题
 *
 * 用法: node review_by_zenmux.mjs [文件路径或目录] [选项]
 *   node review_by_zenmux.mjs ../文字剧本/Day3剧本.txt          # 审核单个文件
 *   node review_by_zenmux.mjs ../文字剧本/                       # 审核目录下所有文件
 *   node review_by_zenmux.mjs ../文字剧本/ --model deepseek/deepseek-chat  # 指定模型
 */

import { readFileSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { resolve, basename, extname, join } from "node:path";
import { chatCompletion } from "../zenmux-api-demo/src/zenmux.js";

// ============================================================
// 配置
// ============================================================
const DEFAULT_MODEL = process.env.ZENMUX_DEFAULT_MODEL || "anthropic/claude-sonnet-4-20250514";
const BATCH_SIZE = 3;        // 并发数
const MAX_TOKENS = 16000;

// ============================================================
// 审核 Prompt
// ============================================================
const REVIEW_SYSTEM = `你是「十二飞鸟」Galgame 项目的剧本审核员。故事发生在2025年日本大阪。
请严格检查以下内容，逐项报告：

【审核清单】
1. 日语残留: 是否出现了平假名、片假名、日文特有词汇(如「ありがとう」「ママ」「さようなら」等)？车牌号、地名中的假名也算。
   ⚠️ 注意: "大麦茶""关西""大阪""奈良""章鱼烧"等中文常用词不算日语残留。
2. 角色红线: 是否违背了以下角色的设定红线？
   - 白鹤姬·雪代: 前期(Day 1-15)不能对主角表露真情实感；语调永远平稳，不能失态；禁用感叹号
   - 早莺姬·南梨: 男友死前不能彻底清醒/觉醒；淤青不能写成每天都有
   - 青鹭姬·星野葵: 永远不能表现愤怒、哭泣或失控；不能写错她的复仇动机(为雪鹤姬而非自己)
   - 神鸦姬·紫: 第二次(及之后)的占卜不能预测成真；认真时必须有"收起嬉笑"的过渡
   - 双雀姬·瞳: Day 16前不能说出完整长句
   - 诡鹀姬·春奈: Day 41前不能让任何人看到素颜
   - 巢燕姬·景子: 女儿名字必须是小澪；14岁(不是幼儿)；不能做伤害女儿的事
   - 雏鹃姬·育子: Day 15前不能过于自信/成熟；必须记得"妈妈不知道她退学"
3. 格式问题: 是否缺少事件分割标记(==========)？地点标记(#)？Speaker标签(【】)？
4. 事实一致: 是否与已建立的设定矛盾？(例如增田死因是当场死亡不是植物人、佐藤警衔是警部补)
5. 主角台词: 是否超过15字？是否使用了省略号(……)开头？

【输出格式】
请严格按以下JSON格式输出(不要包含markdown标记):
{
  "文件": "文件名",
  "问题数": N,
  "问题详情": [
    {"类型": "日语残留/角色红线/格式/事实/台词", "位置": "大致行号或引用", "描述": "问题描述"},
    ...
  ],
  "通过项": ["通过的项目列表"],
  "备注": "一句话总结"
}
如果没有任何问题，问题详情返回空数组，通过项列出所有通过的项目。`;

// ============================================================
// 核心: 审核单个文件
// ============================================================
async function reviewSingleFile(filePath, model) {
  const fileName = basename(filePath);
  const content = readFileSync(filePath, "utf-8");

  // 截断过长文件(保留头尾)
  const maxLen = 60000;
  let text;
  if (content.length > maxLen) {
    const head = content.slice(0, maxLen * 0.7);
    const tail = content.slice(-maxLen * 0.3);
    text = head + "\n\n... [中间省略] ...\n\n" + tail;
  } else {
    text = content;
  }

  const messages = [
    { role: "system", content: REVIEW_SYSTEM },
    { role: "user", content: `请审核以下剧本文件:\n\n文件: ${fileName}\n内容:\n${text}` },
  ];

  try {
    const result = await chatCompletion({
      model,
      messages,
      options: { max_tokens: MAX_TOKENS, temperature: 0.1 },
    });

    const reply = result.choices[0].message.content;

    // 尝试解析 JSON
    let parsed;
    try {
      // 清理可能的 markdown 包裹
      const jsonStr = reply.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
      parsed = JSON.parse(jsonStr);
    } catch {
      // 无法解析JSON时返回原始文本
      return { 文件: fileName, 问题数: -1, 原始回复: reply.slice(0, 500), 备注: "JSON解析失败" };
    }

    return parsed;
  } catch (err) {
    return { 文件: fileName, 问题数: -1, 错误: err.message, 备注: "API调用失败" };
  }
}

// ============================================================
// 批量审核目录
// ============================================================
async function reviewDirectory(dirPath, model) {
  const allFiles = [];
  function scan(dir) {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        if (!["结局", "BE18"].includes(entry)) scan(full);
      } else if (entry.endsWith(".txt") && entry.startsWith("Day")) {
        allFiles.push(full);
      }
    }
  }
  scan(dirPath);

  // 按文件名排序
  allFiles.sort((a, b) => {
    const na = parseInt(basename(a).match(/Day(\d+)/)?.[1] || "0");
    const nb = parseInt(basename(b).match(/Day(\d+)/)?.[1] || "0");
    return na - nb;
  });

  console.log(`🔍 找到 ${allFiles.length} 个文件，模型: ${model}`);
  console.log(`📦 每批 ${BATCH_SIZE} 个并发\n`);

  const results = [];
  let totalProblems = 0;

  // 分批并发
  for (let i = 0; i < allFiles.length; i += BATCH_SIZE) {
    const batch = allFiles.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(allFiles.length / BATCH_SIZE);

    process.stdout.write(`  [${batchNum}/${totalBatches}] 审核中: ${batch.map(basename).join(", ")}... `);

    const batchResults = await Promise.all(
      batch.map((f) => reviewSingleFile(f, model))
    );

    for (const r of batchResults) {
      results.push(r);
      if (r.问题数 > 0) totalProblems += r.问题数;
    }

    const batchProblems = batchResults.reduce((sum, r) => sum + (r.问题数 > 0 ? r.问题数 : 0), 0);
    console.log(`✅ (${batchProblems}个问题)`);
  }

  return { results, totalProblems, totalFiles: allFiles.length };
}

// ============================================================
// 主入口
// ============================================================
async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log("用法: node review_by_zenmux.mjs <文件路径|目录路径> [--model 模型ID]");
    console.log("示例:");
    console.log("  node review_by_zenmux.mjs ../文字剧本/Day3剧本.txt");
    console.log("  node review_by_zenmux.mjs ../文字剧本/ --model deepseek/deepseek-chat");
    process.exit(0);
  }

  const targetPath = resolve(args[0]);
  const modelIdx = args.indexOf("--model");
  const model = modelIdx >= 0 ? args[modelIdx + 1] : DEFAULT_MODEL;

  console.log("🦅 十二飞鸟 · ZenMux 剧本审核");
  console.log("=" .repeat(50));
  console.log(`📁 目标: ${targetPath}`);
  console.log(`🤖 模型: ${model}\n`);

  const isDir = statSync(targetPath).isDirectory();
  const report = isDir
    ? await reviewDirectory(targetPath, model)
    : { results: [await reviewSingleFile(targetPath, model)], totalProblems: 0, totalFiles: 1 };

  // 输出报告
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const reportPath = resolve(`../_pipeline_output/review_zenmux_${timestamp}.json`);

  // 确保目录存在
  const { mkdirSync } = await import("node:fs");
  mkdirSync(resolve("../_pipeline_output"), { recursive: true });

  writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");

  // 汇总
  console.log("\n" + "=".repeat(50));
  console.log("📊 审核汇总");
  console.log("=".repeat(50));

  if (isDir) {
    console.log(`  审核文件: ${report.totalFiles} 个`);
    console.log(`  发现问题: ${report.totalProblems} 处`);
    console.log(`  详细报告: ${reportPath}`);

    // 列出有问题的文件
    const problemFiles = report.results.filter((r) => r.问题数 > 0);
    if (problemFiles.length > 0) {
      console.log(`\n  ⚠️ 有问题的文件 (${problemFiles.length}个):`);
      for (const pf of problemFiles) {
        console.log(`    - ${pf.文件}: ${pf.问题数}个问题`);
      }
    } else {
      console.log("\n  ✅ 未发现问题！");
    }
  } else {
    const r = report.results[0];
    if (r.问题数 > 0) {
      console.log(`  ⚠️ ${r.文件}: ${r.问题数}个问题`);
      if (r.问题详情) {
        for (const d of r.问题详情) {
          console.log(`    [${d.类型}] ${d.描述}`);
        }
      }
    } else {
      console.log(`  ✅ ${r.文件}: 通过审核`);
    }
  }
}

main().catch((err) => {
  console.error("❌ 执行失败:", err.message);
  process.exit(1);
});
