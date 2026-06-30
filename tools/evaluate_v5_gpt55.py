#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十二飞鸟 v5 全量剧本评估脚本
使用 ZenMux GPT-5.5 对最新全量剧本进行多维度叙事评审

策略：
  1. 自动从 v5 合集提取关键段落（开头/角色登场/转折/高潮/结局）
  2. 结合创作规范作为评审标准
  3. 分两步评估：
     Step A: 结构+红线扫描（全量抽样 Day 轮廓）
     Step B: 关键段落深度叙事评审（5个核心场景）
  4. 合并生成最终评审报告

用法:
  python evaluate_v5_gpt55.py                     # 默认 GPT-5.5
  python evaluate_v5_gpt55.py --model openai/gpt-5  # 用 GPT-5
  python evaluate_v5_gpt55.py --output 评审报告_v5.md
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from openai import OpenAI

# ============ 配置 ============
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.getenv("ZENMUX_API_KEY", "")
BASE_URL = "https://zenmux.ai/api/v1"

if not API_KEY:
    # 尝试从 .env 文件读取
    env_path = os.path.join(PROJECT_ROOT, "zenmux-api-demo", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ZENMUX_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip()
                    break

if not API_KEY:
    print("❌ 未找到 ZENMUX_API_KEY")
    print("请设置环境变量或在 zenmux-api-demo/.env 中配置")
    sys.exit(1)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============ 文件读取 ============

def read_file(path, max_chars=0):
    """读取文件，可选截断"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if max_chars > 0 and len(content) > max_chars:
        head = content[:int(max_chars * 0.7)]
        tail = content[-int(max_chars * 0.3):]
        return head + "\n\n... [中间省略] ...\n\n" + tail
    return content


def extract_lines(content, start, end):
    """按行号范围提取"""
    lines = content.split("\n")
    return "\n".join(lines[max(0, start - 1):min(len(lines), end)])


def find_day_boundaries(content):
    """
    自动查找 v5 中所有 Day 边界行号。
    v5 格式混合：
      - Day 1-2 使用 "Day N 标题 编号" 显式行标记
      - Day 4+ 使用 "========== Day N 结束·跳转 Day N+1 ==========" 结尾标记
      - 事件内部用 "========== 事件X：标题 编号 =========="
    策略：综合使用 "Day N" 行标记 + 事件编号 + "Day N 结束" 标记来推断所有 Day 起止
    """
    lines = content.split("\n")
    day_starts = {}

    # 方法1: 显式 "Day N 标题" 行
    for i, line in enumerate(lines):
        m = re.match(r"^Day\s+(\d+)\s+", line)
        if m:
            day = int(m.group(1))
            if day not in day_starts:
                day_starts[day] = i + 1  # 1-based

    # 方法2: 从 "Day N 结束" 标记推断 Day 边界
    # 以及从事件编号推断（编号格式: DDEE, DD=Day两位数, EE=事件序号）
    day_ends = {}
    for i, line in enumerate(lines):
        m = re.search(r"Day\s+(\d+)\s+结束", line)
        if m:
            day = int(m.group(1))
            if day not in day_ends:
                day_ends[day] = i + 1

    # 方法3: 从事件编号推断 Day 起始
    for i, line in enumerate(lines):
        m = re.match(r"^==========\s+事件[一二三四五六七八九十]+[：:]", line)
        if m:
            # 提取编号（如 1401, 1601 等）
            num_m = re.search(r"\s(\d{4})\s+==========$", line)
            if num_m:
                code = int(num_m.group(1))
                day_from_code = code // 100  # 1401 → Day 14, 1601 → Day 16
                # Day 1-2 用1001-1008编码（1001→Day10? 不对，需要特殊处理）
                # 实际编号: 1001=Day1事件1, 1002=Day1事件2, 1006=Day2事件1, etc.
                # 所以1001-1005=Day1, 1006-1008=Day2, 1009+=Day3(?), 但1009实际是Day3
                # 从已知映射看: 1001-1005=Day1, 1006-1008=Day2
                # 1009+, 1401+=Day4+... 这个编号系统不太直观
                # 先跳过复杂推断，只处理明确的编号
                if day_from_code >= 10:
                    # 编号1401→Day14, 1501→Day15, etc.
                    inferred_day = day_from_code
                    if inferred_day not in day_starts:
                        day_starts[inferred_day] = i + 1

    # 补充: Day 3 的起始从 Day 2 结束之后推断
    # 从 "Day 2 氤氲陷阱" 后面查找第一个事件标记作为 Day 3 起点
    if 2 in day_starts and 3 not in day_starts:
        day2_line = day_starts[2]
        # 从 Day 2 起始往后扫描，找 "========== 事件" 或 Day 3 相关标记
        for i in range(day2_line, min(day2_line + 2000, len(lines))):
            line = lines[i]
            # Day 3 在 v5 中没有显式标记，但从事件编号1009开始是Day 3
            m = re.search(r"1009", line)
            if m and "事件" in line:
                day_starts[3] = i + 1
                break

    # 确保每个Day有对应范围：对缺失起始的Day，用前一个Day结束+1推断
    all_known_days = sorted(set(list(day_starts.keys()) + list(day_ends.keys())))
    for day in range(1, max(all_known_days) + 1):
        if day not in day_starts:
            # 用前一个Day的结束行推断
            prev_end = day_ends.get(day - 1, 0)
            if prev_end > 0:
                # 在结束标记后面几行找第一个有意义的内容
                for i in range(prev_end, min(prev_end + 50, len(lines))):
                    line = lines[i].strip()
                    if line and not line.startswith("=") and not line.startswith("#"):
                        day_starts[day] = i + 1
                        break

    return day_starts


def extract_day_header(content, day_num, day_starts, max_lines=80):
    """提取某 Day 的开头段落"""
    start = day_starts.get(day_num, 0)
    if start == 0:
        return ""
    return extract_lines(content, start, min(start + max_lines, len(content.split("\n"))))


# ============ 关键段落提取 ============

def extract_key_samples(content, day_starts):
    """提取 7 个关键段落用于深度评审，用已知行号直接定位"""

    lines_list = content.split("\n")
    total_lines = len(lines_list)

    samples = {}

    # 样本一：Day 1 开头（氛围建立 + 主角嗅觉描写）- 行22起
    samples["Day1开头_氛围建立"] = extract_lines(content, 22, 122)

    # 样本二：Day 2 角色登场（女友莉香通话 + 多角色首次出场）- 行668起
    samples["Day2角色登场_莉香通话"] = extract_lines(content, 668, 818)

    # 样本三：Day 3-4 事件展开（第二次汇报/三重奏/雏鹃登场）- 行1248起
    samples["Day3-4_事件展开"] = extract_lines(content, 1248, 1435)

    # 样本四：Day 7 增田之死前夜（转折关键）- 行3283起
    samples["Day7_增田之死前夜"] = extract_lines(content, 3283, 3423)

    # 样本五：Day 8 增田之死 + 佐藤接班 - 行3625起
    samples["Day8_增田之死转折"] = extract_lines(content, 3625, 3752)

    # 样本六：Day 20 中段深化（阶段三）- 行7141起
    samples["Day20_中段深化"] = extract_lines(content, 7141, 7261)

    # 样本七：Day 40 终章序幕 - 行12121起
    samples["Day40_终章序幕"] = extract_lines(content, 12121, 12241)

    return samples


def extract_day_outlines(content, day_starts, max_lines=30):
    """提取所有 Day 的开头轮廓，用于结构扫描"""
    outlines = {}
    for day in sorted(day_starts):
        outlines[f"Day{day}"] = extract_day_header(content, day, day_starts, max_lines)
    return outlines


# ============ Step A: 结构 + 红线扫描 ============

STEP_A_SYSTEM = """你是「十二飞鸟」Galgame 项目的剧本结构审核员。故事发生在2025年日本大阪。
你将收到：
1. 创作规范（包含角色红线和格式要求）
2. 所有Day的开头轮廓（每Day约30行）

请检查以下内容，逐项报告：

【检查清单】
1. 日语残留: 是否在轮廓中出现了平假名(ひらがな)、片假名(カタカナ)或日文特有词汇？
   注意: "大麦茶""关西""大阪""奈良""章鱼烧"等中文常用词不算日语残留。
2. 角色红线: 是否违背了创作规范中的角色设定红线？
3. POV合规: 主角是否出现在不合理地点（私宅/角色卧室）？
4. 格式规范: 是否缺少必要的事件分割标记或Speaker标签？
5. Day衔接: 各Day开头是否能与前一天自然衔接？
6. 主角台词: 是否超过15字？是否以省略号(……)开头？

【输出格式】严格按以下JSON格式输出(不要markdown标记):
{
  "结构总评": "一句话总结整体结构质量",
  "Day总数": N,
  "日语残留": {"发现": true/false, "详情": ["位置+内容"]},
  "角色红线违规": {"发现": true/false, "详情": ["角色+违规内容"]},
  "POV违规": {"发现": true/false, "详情": ["位置+描述"]},
  "格式问题": {"发现": true/false, "详情": ["Day+问题"]},
  "Day衔接问题": {"发现": true/false, "详情": ["Day X→Day Y: 问题描述"]},
  "主角台词超标": {"发现": true/false, "详情": ["Day+台词内容"]},
  "严重问题Top3": ["问题描述"],
  "改进建议": ["建议列表"]
}"""


# ============ Step B: 深度叙事评审 ============

STEP_B_SYSTEM = """你是资深叙事设计师和游戏剧本评审专家。你将对「十二飞鸟」Galgame的关键场景进行深度评审。

剧本背景：
- 类型：互动恋爱悬疑游戏剧本（卧底题材，60天进度，27种结局）
- 背景：日本大阪风俗俱乐部，毒品案×连环杀人案双线叙事
- 主角：黑羽哲也，异常敏锐嗅觉（Day60前不可有意识使用），极度寡言（≤15字/句）

创作规范（必须遵守的核心要点）：
- 禁止日语字符
- 旁白占比60~65%，短句为主
- 嗅觉优先感官描写
- 情感从不直说：用身体反应/环境隐喻/沉默替代
- 比喻冷峻精确，偏好黑暗意象
- 零感叹号（活泼角色除外）
- 角色红线不可违背（详见创作规范文件）

评审维度（每维度评分1-10）：
1. 角色声音一致性：每个角色对话是否符合身份设定？主角是否寡言？
2. 文风规范遵守：短句？嗅觉优先？零感叹号？比喻冷峻？
3. 情感表达方式：从不直说？身体反应/环境隐喻替代直白抒情？
4. 旁白质量：占比60~65%？环境先行？节奏缓慢克制？
5. POV合规性：主角视角受限？无越界描述？
6. 日语残留：有无任何日语字符？
7. 设定红线遵守：各角色禁止行为是否出现？
8. 叙事节奏与张力：场景切换流畅？悬念设置合理？节奏推进感？

【输出格式】严格按以下JSON格式输出(不要markdown标记):
{
  "综合评分": X,
  "各维度评分": {
    "角色声音一致性": {"分": N, "问题": ["具体问题"]},
    "文风规范遵守": {"分": N, "问题": ["具体问题"]},
    "情感表达方式": {"分": N, "问题": ["具体问题"]},
    "旁白质量": {"分": N, "问题": ["具体问题"]},
    "POV合规性": {"分": N, "问题": ["具体问题"]},
    "日语残留": {"分": N, "问题": ["具体问题"]},
    "设定红线遵守": {"分": N, "问题": ["具体问题"]},
    "叙事节奏与张力": {"分": N, "问题": ["具体问题"]}
  },
  "最严重问题Top5": ["问题描述+位置"],
  "亮点Top3": ["值得保留的优秀写作片段"],
  "改进建议": ["具体可执行的建议"]
}"""


# ============ API 调用 ============

def call_gpt(model, system_prompt, user_content, max_tokens=16000, temperature=0.1, stream=False):
    """调用 ZenMux API"""
    print(f"[调用] model={model}, prompt长度≈{len(system_prompt)+len(user_content)}字")

    if stream:
        full_response = ""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_completion_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in response:
            if not chunk.choices:
                if chunk.usage:
                    u = chunk.usage
                    print(f"\n[用量] prompt={u.prompt_tokens}, completion={u.completion_tokens}, total={u.total_tokens}")
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content
        print()
        return full_response
    else:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )
        content = completion.choices[0].message.content
        usage = completion.usage
        print(f"[用量] prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        return content


def parse_json_response(text):
    """尝试解析模型返回的JSON，清理markdown包裹"""
    cleaned = text.replace("```json\n", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 尾部截断修复：找到最后一个 } 并补全
        last_brace = cleaned.rfind("}")
        if last_brace > 0:
            try:
                return json.loads(cleaned[:last_brace + 1])
            except:
                pass
        print("[警告] JSON解析失败，返回原始文本")
        return {"原始回复": cleaned[:2000]}


# ============ 主流程 ============

def main():
    parser = argparse.ArgumentParser(description="十二飞鸟 v5 剧本评估")
    parser.add_argument("--model", default="openai/gpt-5.5", help="模型ID")
    parser.add_argument("--output", default="GPT55_v5_剧本评估报告.md", help="输出报告路径")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    parser.add_argument("--step", choices=["a", "b", "both"], default="both", help="执行步骤")
    args = parser.parse_args()

    model = args.model
    output_path = os.path.join(PROJECT_ROOT, args.output)

    print("=" * 70)
    print("  🦅 十二飞鸟 v5 全量剧本评估")
    print("=" * 70)
    print(f"  模型: {model}")
    print(f"  输出: {output_path}")
    print(f"  步骤: {args.step}")
    print()

    # 读取文件
    script_v5 = read_file(os.path.join(PROJECT_ROOT, "十二飞鸟_全剧本合集_v5.txt"))
    rules = read_file(os.path.join(PROJECT_ROOT, "设定文档", "创作规范_全局.md"))

    print(f"[文件] v5剧本: {len(script_v5)} 字符, {len(script_v5.split(chr(10)))} 行")
    print(f"[文件] 创作规范: {len(rules)} 字符")

    # 分析 Day 结构
    day_starts = find_day_boundaries(script_v5)
    print(f"[结构] 发现 {len(day_starts)} 个Day边界: Day {min(day_starts)} ~ Day {max(day_starts)}")

    result_a = None
    result_b = None

    # ===== Step A: 结构 + 红线扫描 =====
    if args.step in ("a", "both"):
        print("\n" + "=" * 70)
        print("  🔍 Step A: 结构 + 红线扫描")
        print("=" * 70)

        # 提取所有Day轮廓（每个Day只取30行）
        outlines = extract_day_outlines(script_v5, day_starts, max_lines=30)
        outlines_text = ""
        for day_key, outline in outlines.items():
            outlines_text += f"\n### {day_key} 轮廓\n{outline}\n"

        # 截断过长的轮廓文本
        if len(outlines_text) > 80000:
            outlines_text = outlines_text[:80000] + "\n\n... [后续Day轮廓省略] ..."

        user_a = f"""## 创作规范\n{rules}\n\n## 全量剧本Day轮廓\n{outlines_text}"""

        print(f"[Step A] 发送内容长度: {len(user_a)} 字符")

        response_a = call_gpt(model, STEP_A_SYSTEM, user_a, max_tokens=8000, stream=args.stream)
        result_a = parse_json_response(response_a)

    # ===== Step B: 深度叙事评审 =====
    if args.step in ("b", "both"):
        print("\n" + "=" * 70)
        print("  📝 Step B: 关键段落深度叙事评审")
        print("=" * 70)

        samples = extract_key_samples(script_v5, day_starts)
        samples_text = ""
        for key, text in samples.items():
            samples_text += f"\n\n# ===== {key} =====\n{text}\n"

        user_b = f"""## 创作规范（核心要点）\n{rules}\n\n## 剧本关键段落\n{samples_text}\n\n请对以上5个关键段落进行深度叙事评审。"""

        print(f"[Step B] 发送内容长度: {len(user_b)} 字符")

        response_b = call_gpt(model, STEP_B_SYSTEM, user_b, max_tokens=16000, stream=args.stream)
        result_b = parse_json_response(response_b)

    # ===== 生成报告 =====
    print("\n" + "=" * 70)
    print("  📊 生成评审报告")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# 十二飞鸟 v5 全量剧本评估报告

> 评估模型: **{model}**
> 评估时间: {timestamp}
> 评估剧本: 十二飞鸟_全剧本合集_v5.txt ({len(script_v5)}字符, {len(script_v5.split(chr(10)))}行)
> 发现Day数: {len(day_starts)} (Day {min(day_starts)} ~ Day {max(day_starts)})

---

## 一、结构 + 红线扫描结果 (Step A)

"""

    if result_a:
        report += f"""```json
{json.dumps(result_a, ensure_ascii=False, indent=2)}
```

"""
    else:
        report += "> 未执行 Step A\n\n"

    report += """---

## 二、关键段落深度叙事评审 (Step B)

"""

    if result_b:
        if "综合评分" in result_b:
            score = result_b["综合评分"]
            report += f"""### 🏆 综合评分: **{score}/10**

"""
        if "各维度评分" in result_b:
            report += "### 各维度评分明细\n\n"
            report += "| 维度 | 评分 | 问题 |\n|------|------|------|\n"
            for dim, detail in result_b["各维度评分"].items():
                score = detail.get("分", "?")
                problems = detail.get("问题", [])
                problem_text = "; ".join(problems[:3]) if problems else "无"
                report += f"| {dim} | {score}/10 | {problem_text} |\n"
            report += "\n"

        for section in ["最严重问题Top5", "亮点Top3", "改进建议"]:
            if section in result_b:
                report += f"### {section}\n\n"
                for item in result_b[section]:
                    report += f"- {item}\n"
                report += "\n"

        report += f"""<details>
<summary>完整评审数据 (JSON)</summary>

```json
{json.dumps(result_b, ensure_ascii=False, indent=2)}
```

</details>

"""
    else:
        report += "> 未执行 Step B\n\n"

    report += """---

*报告由 ZenMux GPT-5.5 评估脚本自动生成*
"""

    # 写入报告
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 报告已保存: {output_path}")

    # 输出摘要
    if result_b and "综合评分" in result_b:
        score = result_b["综合评分"]
        print(f"\n🏆 综合评分: {score}/10")
        if "最严重问题Top5" in result_b:
            print("⚠️ 最严重问题:")
            for p in result_b["最严重问题Top5"]:
                print(f"   - {p}")
        if "亮点Top3" in result_b:
            print("✨ 亮点:")
            for h in result_b["亮点Top3"]:
                print(f"   - {h}")


if __name__ == "__main__":
    main()
