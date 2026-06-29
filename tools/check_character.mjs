#!/usr/bin/env node
/**
 * 十二飞鸟 · 角色一致性检查工具
 * 从所有剧本中提取指定角色的全部对话和行动，交由 ZenMux 大模型判断一致性
 *
 * 用法: node check_character.mjs <角色名> [选项]
 *   node check_character.mjs 白鹤姬
 *   node check_character.mjs 巢燕姬 --model anthropic/claude-sonnet-4-20250514
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync } from "node:fs";
import { resolve, basename, join } from "node:path";
import { chatCompletion } from "../zenmux-api-demo/src/zenmux.js";

const SCRIPT_DIR = resolve("../文字剧本");
const DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514";

// ============================================================
// 角色红线定义
// ============================================================
const REDLINES = {
  "白鹤姬": `- 白鹤姬·桂原雪代（一月/头牌）:
    * 语调永远平稳，不能失态，不能用感叹号
    * 前期(Day 1-15)不能对主角表露真情实感
    * Day 38台风夜是她唯一一次坦白过去
    * 她是真正的反派(不是卧底)，在毒品网络21年
    * Day 60晚宴不是阴谋而是她的夺权机会
    * ❌ 不能让她在Day 60前心软、送纸条、提前预警主角`,

  "早莺姬": `- 早莺姬·小野南梨（二月）:
    * 男友癌症末期，坚信"他病好了会变回以前"
    * 手臂淤青是偶尔的(男友化疗失控时)，不是每天都有
    * Day 36她离开俱乐部回老家
    * ❌ 男友死前不能彻底清醒/觉醒`,

  "巢燕姬": `- 巢燕姬·谷川景子（三月/单亲母亲）:
    * 女儿小澪·14岁(初中二年级)，不是幼儿
    * 从不掩饰"为女儿工作"的动机
    * 小澪父亲是村上的手下林田秀人
    * Day 34-37黑田议员危机线
    * ❌ 不能写错女儿名字或年龄`,

  "青鹭姬": `- 青鹭姬·星野葵（四月/医学生）:
    * 京都医科大学高材生，资助人是已死的雪鹤姬
    * 用"极乐"成分提取毒药，制裁恶人
    * 冷静知性，永远不情绪化
    * ❌ 不能表现愤怒、哭泣或失控
    * ❌ 复仇动机是为雪鹤姬，不是为自己`,

  "黄鹂姬": `- 黄鹂姬·日向夏实（五月/前偶像）:
    * Solar Flare前成员，雪鹤姬自杀第一发现人
    * 笑容是面具，独处时"关掉开关"
    * Day 37黄鹂宣言: "如果组织要查卧底——说是我"
    * ❌ 非独处场合不能卸下笑容(除非极端情境)`,

  "神鸦姬": `- 神鸦姬·神乐坂紫（六月/占卜师）:
    * 每日第一次占卜极准，第二次起必定错误
    * 父母车祸双亡，吉普赛占卜师给了塔罗牌和乌鸦
    * ❌ 第二次(及之后)的占卜不能预测成真
    * ❌ 认真时必须先有"收起嬉笑"的过渡`,

  "朱雀姬": `- 朱雀姬·Linda（七月/俄罗斯混血）:
    * Interpol国际刑警，来查跨国毒品线
    * Day 36才向主角坦白Interpol身份
    * 热情张扬，享受卧底身份
    * ❌ Day 25前不能主动暴露Interpol身份`,

  "夜鸢姬": `- 夜鸢姬·美咲蔷薇（八月/SM女王）:
    * 拥有黑皮书记录情报
    * 信息从不免费——要价且越来越贵
    * Day 32第一次免费("算投资")
    * 六年前雪代让她进门——这是她还情报的深层动机`,

  "双雀姬": `- 双雀姬·濑户彩&瞳（九月/姐妹）:
    * 马戏团出身，主动来俱乐部攒钱
    * 瞳几乎丧失独立人格(Day 16前几乎不说话)
    * Day 39彩讲述马戏团往事
    * ❌ 不能把姐妹写成"被卖来的"`,

  "雏鹃姬": `- 雏鹃姬·芦田育子（十月/16岁）:
    * 被骗来，签了债务契约
    * Day 38台风夜告白—提出"初夜献给主角"
    * Day 44把唇膏放进南梨空柜子
    * ❌ Day 15前不能过于自信/成熟
    * ❌ "妈妈不知道她退学"必须保持`,

  "银鹮姬": `- 银鹮姬·神宫寺丽莎（十一月/前投行）:
    * 引入Phoenix Coin虚拟货币
    * 欠地下钱庄的钱，Day 40离开大阪
    * Day 60远程操作金融绞杀
    * ❌ 不能和毒品网络直接交易`,

  "诡鹀姬": `- 诡鹀姬·木岛春奈（十二月/模仿师）:
    * 无人见过素颜(Day 51第一次给黑羽看)
    * 性格顽皮喜欢搞怪，内心善良
    * Day 35模仿所有12飞鸟
    * ❌ Day 41前不能露出素颜
    * ❌ 严肃情境也不能失去恶作剧底色`,

  "小林莉香": `- 小林莉香（女友/澳洲留学生）:
    * 在澳洲留学(商科)，和主角是北海道青梅竹马
    * Day 42前不能出现在日本
    * 仅通过LINE/视频通话/短信出现
    * 向往上流生活，担心警察主角养不起她`,
};

const ROLE_CHINESE = {
  "白鹤姬": "白鹤姬·桂原雪代",
  "早莺姬": "早莺姬·小野南梨",
  "巢燕姬": "巢燕姬·谷川景子",
  "青鹭姬": "青鹭姬·星野葵",
  "黄鹂姬": "黄鹂姬·日向夏实",
  "神鸦姬": "神鸦姬·神乐坂紫",
  "朱雀姬": "朱雀姬·Linda",
  "夜鸢姬": "夜鸢姬·美咲蔷薇",
  "双雀姬": "双雀姬·濑户彩&瞳",
  "雏鹃姬": "雏鹃姬·芦田育子",
  "银鹮姬": "银鹮姬·神宫寺丽莎",
  "诡鹀姬": "诡鹀姬·木岛春奈",
  "小林莉香": "小林莉香",
};

// ============================================================
// 从剧本中提取一个角色的全部台词和行动
// ============================================================
function extractCharacterLines(characterName, filePath) {
  const content = readFileSync(filePath, "utf-8");
  const shortName = characterName.replace(/姬$/, "");

  // 匹配模式: 【角色名】或【角色名·本名】开头的台词
  const patterns = [
    new RegExp(`【${characterName}[·•].*?】\\n([\\s\\S]*?)(?=\\n【|\\n==========|\\n$|$)`, "g"),
    new RegExp(`【${shortName}[·•]?.*?】\\n([\\s\\S]*?)(?=\\n【|\\n==========|\\n$|$)`, "g"),
    new RegExp(`【${shortName}】\\n([\\s\\S]*?)(?=\\n【|\\n==========|\\n$|$)`, "g"),
  ];

  // 也匹配旁白中提及角色的段落
  const narPattern = new RegExp(
    `【旁白】\\n([\\s\\S]*?${characterName}[\\s\\S]*?)(?=\\n【|\\n==========|\\n$|$)`,
    "g"
  );

  const lines = [];
  for (const pat of patterns) {
    for (const match of content.matchAll(pat)) {
      lines.push(match[1].trim());
    }
  }

  // 抽取旁白相关(前15条)
  const narLines = [];
  for (const match of content.matchAll(narPattern)) {
    narLines.push(match[1].trim());
    if (narLines.length >= 15) break;
  }

  return { lines, narLines, totalMatches: lines.length + narLines.length };
}

// ============================================================
// 审核角色一致性
// ============================================================
async function checkCharacter(characterName, model) {
  const fullName = ROLE_CHINESE[characterName] || characterName;
  const redline = REDLINES[characterName] || "无特殊红线";

  // 收集所有剧本中该角色的台词
  const allFiles = readdirSync(SCRIPT_DIR)
    .filter((f) => f.startsWith("Day") && f.endsWith(".txt") && !f.includes("end") && !f.includes("细化"))
    .sort((a, b) => {
      const na = parseInt(a.match(/Day(\d+)/)?.[1] || "0");
      const nb = parseInt(b.match(/Day(\d+)/)?.[1] || "0");
      return na - nb;
    });

  console.log(`🔍 从 ${allFiles.length} 个剧本中提取「${characterName}」的台词...`);

  let allDialogue = "";
  let totalMatches = 0;
  const fileStats = [];

  for (const file of allFiles) {
    const filePath = join(SCRIPT_DIR, file);
    const extracted = extractCharacterLines(characterName, filePath);
    if (extracted.totalMatches > 0) {
      fileStats.push(`${file}: ${extracted.totalMatches}处匹配`);
      const dayNum = basename(file).match(/Day(\d+)/)?.[1] || "?";
      allDialogue += `\n--- Day ${dayNum} ---\n`;
      for (const line of extracted.lines.slice(0, 30)) {
        allDialogue += line + "\n";
      }
      if (extracted.lines.length > 30) {
        allDialogue += `... (另有${extracted.lines.length - 30}行台词省略)\n`;
      }
    }
    totalMatches += extracted.totalMatches;
  }

  console.log(`✅ 共提取 ${totalMatches} 处台词/提及\n`);

  if (totalMatches === 0) {
    console.log("⚠️ 未找到任何匹配，请检查角色名");
    return;
  }

  // 截断过长的内容
  const maxLen = 50000;
  if (allDialogue.length > maxLen) {
    allDialogue = allDialogue.slice(0, maxLen * 0.5) + "\n... [中间省略] ...\n" + allDialogue.slice(-maxLen * 0.5);
  }

  const prompt = `请审核以下角色在整个剧本中的一致性：

【角色】${fullName}
【角色红线】
${redline}

【台词&行动摘要(从所有Day中提取)】
${allDialogue}

请从以下维度评估：
1. 台词风格是否始终一致？(语气/用词/句式)
2. 角色红线是否全部遵守？逐一检查
3. 角色的关键设定是否在60天中保持一致？(例如: 动机、背景、能力)
4. 有没有"前一天还在哭第二天若无其事"的情绪断裂？
5. 有没有违反角色设定的台词或行为？

输出JSON格式:
{
  "角色": "${characterName}",
  "风格一致": true/false,
  "红线违规": [{"Day": "Day X", "内容": "具体问题"}],
  "设定矛盾": [{"描述": "具体矛盾"}],
  "情绪断裂": [{"描述": "具体断裂点"}],
  "总体评价": "一句话评价",
  "建议": "一句话建议"
}`;

  console.log(`🤖 调用 ${model} 审核中...`);

  try {
    const result = await chatCompletion({
      model,
      messages: [
        { role: "system", content: "你是galgame剧本审核专家，善于发现角色设定的细微矛盾。严格按JSON格式输出。" },
        { role: "user", content: prompt },
      ],
      options: { max_tokens: 8000, temperature: 0.1 },
    });

    const reply = result.choices[0].message.content;
    const jsonStr = reply.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();

    let parsed;
    try {
      parsed = JSON.parse(jsonStr);
    } catch {
      parsed = { 原始回复: reply };
    }

    // 保存报告
    mkdirSync(resolve("../_pipeline_output"), { recursive: true });
    const reportPath = resolve(`../_pipeline_output/character_${characterName}.json`);
    writeFileSync(
      reportPath,
      JSON.stringify({ 审核结果: parsed, 文件覆盖: fileStats, 总匹配数: totalMatches }, null, 2),
      "utf-8"
    );

    console.log("\n📊 " + "=".repeat(40));
    console.log(`📋 ${characterName} 审核结果`);
    console.log("=".repeat(40));

    if (parsed.风格一致 !== undefined) {
      console.log(`   风格一致: ${parsed.风格一致 ? "✅" : "❌"}`);
    }
    if (parsed.红线违规 && parsed.红线违规.length > 0) {
      console.log(`   ⚠️ 红线违规 (${parsed.红线违规.length}):`);
      for (const v of parsed.红线违规) console.log(`      - [${v.Day}] ${v.内容}`);
    } else {
      console.log("   ✅ 红线: 全部通过");
    }
    if (parsed.设定矛盾 && parsed.设定矛盾.length > 0) {
      console.log(`   ⚠️ 设定矛盾 (${parsed.设定矛盾.length}):`);
      for (const c of parsed.设定矛盾) console.log(`      - ${c.描述}`);
    }
    if (parsed.情绪断裂 && parsed.情绪断裂.length > 0) {
      console.log(`   ⚠️ 情绪断裂 (${parsed.情绪断裂.length}):`);
      for (const b of parsed.情绪断裂) console.log(`      - ${b.描述}`);
    }
    console.log(`   💬 评价: ${parsed.总体评价 || "无"}`);
    console.log(`   💡 建议: ${parsed.建议 || "无"}`);
    console.log(`\n   📁 完整报告: ${reportPath}`);

  } catch (err) {
    console.error(`❌ API调用失败: ${err.message}`);
  }
}

// ============================================================
// 主入口
// ============================================================
async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("--help")) {
    console.log("用法: node check_character.mjs <角色名> [--model 模型ID]");
    console.log("\n可用角色:");
    for (const name of Object.keys(ROLE_CHINESE)) {
      console.log(`  - ${name} (${ROLE_CHINESE[name]})`);
    }
    console.log("\n示例: node check_character.mjs 白鹤姬");
    process.exit(0);
  }

  const charName = args[0];
  const modelIdx = args.indexOf("--model");
  const model = modelIdx >= 0 ? args[modelIdx + 1] : DEFAULT_MODEL;

  if (!REDLINES[charName]) {
    console.error(`❌ 未知角色: ${charName}`);
    console.log("可用角色:", Object.keys(ROLE_CHINESE).join(", "));
    process.exit(1);
  }

  await checkCharacter(charName, model);
}

main().catch((err) => {
  console.error("❌ 执行失败:", err.message);
  process.exit(1);
});
