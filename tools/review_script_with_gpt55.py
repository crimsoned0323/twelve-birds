#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 Zenmux GPT-5.5 评审「十二飞鸟」剧本质量
读取创作规范 + 剧本样本，发送给 GPT-5.5 进行专业叙事评审
"""

import os
import sys
import argparse
from openai import OpenAI

# ============ 配置 ============
API_KEY = os.getenv("ZENMUX_API_KEY", "")
BASE_URL = "https://zenmux.ai/api/v1"
MODEL = "openai/gpt-5.5"

if not API_KEY:
    print("❌ 未找到 ZENMUX_API_KEY 环境变量")
    sys.exit(1)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============ 读取文件 ============

def read_file(path: str, max_lines: int = 0) -> str:
    """读取文件内容，可选限制行数"""
    with open(path, "r", encoding="utf-8") as f:
        if max_lines > 0:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
        return f.read()


# ============ 构建评审 Prompt ============

def build_review_prompt() -> str:
    """
    构建完整的评审请求 prompt
    包含：创作规范 + 剧本样本 + 评审维度说明
    """
    # 读取创作规范
    rules = read_file("设定文档/创作规范_全局.md")

    # 读取剧本关键样本（Day1开头、Day2角色登场、Day7雏鹃姬场景、Day8增田之死、Day45高潮部署）
    script = read_file("十二飞鸟_全剧本合集_v4.txt")

    # 提取关键段落（按行号范围）
    def extract_lines(content: str, start: int, end: int) -> str:
        lines = content.split("\n")
        return "\n".join(lines[max(0, start-1):min(len(lines), end)])

    samples = ""
    samples += "\n\n# ===== 样本一：Day 1 开头（氛围建立）=====\n"
    samples += extract_lines(script, 1, 110)
    samples += "\n\n# ===== 样本二：Day 2 角色登场（双雀姬、黄鹂姬、夜鸢姬）=====\n"
    samples += extract_lines(script, 800, 950)
    samples += "\n\n# ===== 样本三：Day 7 结尾 雏鹃姬场景（情感描写）=====\n"
    samples += extract_lines(script, 3490, 3560)
    samples += "\n\n# ===== 样本四：Day 8 增田之死（转折场景）=====\n"
    samples += extract_lines(script, 3574, 3750)
    samples += "\n\n# ===== 样本五：Day 45 后巷部署（高潮前奏）=====\n"
    samples += extract_lines(script, 12058, 12200)

    prompt = f"""你是一位资深叙事设计师和游戏剧本评审专家。请对以下剧本进行专业评审。

## 剧本背景
- 类型：互动恋爱悬疑游戏剧本（卧底题材，60天游戏进度，27种结局）
- 背景：日本大阪风俗俱乐部，毒品案×连环杀人案双线叙事
- 主角：黑羽哲也，异常敏锐嗅觉（Day60前不可有意识使用），极度寡言（≤15字/句）

## 创作规范（必须遵守）
{rules}

## 剧本样本（5个关键场景）
{samples}

## 评审要求
请从以下维度进行评审，每个维度给出评分（1-10）和具体问题描述：

1. **角色声音一致性**：每个角色的对话是否符合其身份设定？主角是否足够寡言（≤15字/句）？
2. **文风规范遵守**：短句为主？嗅觉优先？零感叹号（活泼角色除外）？比喻是否冷峻精确？
3. **情感表达方式**：情感是否从不直说？是否用身体反应/环境隐喻/沉默替代直白抒情？
4. **旁白质量**：旁白占比60-65%？环境先行人物后至？节奏缓慢克制？
5. **POV合规性**：主角视角是否受限？有无出现主角不应在场的描述？
6. **日语残留检查**：有无任何日语字符（平假名/片假名）混入？
7. **设定红线遵守**：各角色禁止行为是否出现？（如白鹤姬前期表露真情、青鹭姬情绪化等）
8. **整体叙事节奏**：场景切换是否流畅？悬念设置是否合理？

## 输出格式
请按以下格式输出：
### 综合评分：X/10
### 各维度评分与问题
（逐维度列出）
### 最严重的问题（Top 3）
（列出最影响剧本质量的问题）
### 改进建议
（具体可执行的改进建议）
"""

    return prompt


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(description="用 GPT-5.5 评审剧本")
    parser.add_argument("--output", default="GPT55_剧本评审报告.md", help="评审报告输出路径")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    args = parser.parse_args()

    print("[评审] 正在构建评审请求...")
    prompt = build_review_prompt()
    print(f"[评审] Prompt 长度: {len(prompt)} 字符")
    print(f"[评审] 发送到模型: {MODEL}")
    print("-" * 50)

    if args.stream:
        # 流式输出
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            stream_options={"include_usage": True},
            max_completion_tokens=8192,
            temperature=0.3,  # 低温度，评审要客观
        )
        print("[流式评审输出]\n")
        full_response = ""
        for chunk in stream:
            if not chunk.choices:
                if chunk.usage:
                    u = chunk.usage
                    print(f"\n[用量] prompt={u.prompt_tokens}, completion={u.completion_tokens}, total={u.total_tokens}")
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content
        # 保存报告
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("# GPT-5.5 剧本评审报告\n\n")
            f.write(full_response)
        print(f"\n\n[报告已保存] {args.output}")

    else:
        # 非流式，一次性返回
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=8192,
            temperature=0.3,
        )
        content = completion.choices[0].message.content
        usage = completion.usage

        print(f"[评审完成]\n")
        print(content)
        print(f"\n[用量统计] prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")

        # 保存报告
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("# GPT-5.5 剧本评审报告\n\n")
            f.write(content)
        print(f"\n[报告已保存] {args.output}")


if __name__ == "__main__":
    main()
