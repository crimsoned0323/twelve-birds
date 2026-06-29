#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zenmux 连通性测试脚本
支持两种方式传入 API Key：
  1. 命令行参数: python test_zenmux.py --key sk-xxx
  2. 环境变量:    设置 ZENMUX_API_KEY 后直接运行

模型: claude-fable-5 (Zenmux 格式: anthropic/claude-fable-5)
"""

import os
import sys
import argparse
from openai import OpenAI


def test_connection(api_key: str, model: str = "anthropic/claude-fable-5") -> bool:
    """测试 Zenmux API 连通性"""
    client = OpenAI(
        base_url="https://zenmux.ai/api/v1",
        api_key=api_key,
    )

    print(f"[测试] 模型: {model}")
    print(f"[测试] Base URL: https://zenmux.ai/api/v1")
    print("-" * 50)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "请用一句话介绍你自己，包括你的能力和限制。"}
            ],
            max_completion_tokens=200,
            temperature=0.7,
        )
        content = completion.choices[0].message.content
        usage = completion.usage

        print(f"[成功] 模型回复:\n{content}\n")
        print(f"[用量统计]")
        print(f"  prompt tokens:     {usage.prompt_tokens}")
        print(f"  completion tokens: {usage.completion_tokens}")
        print(f"  total tokens:      {usage.total_tokens}")
        if usage.completion_tokens_details:
            print(f"  reasoning tokens:   {usage.completion_tokens_details.reasoning_tokens}")
        return True

    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Zenmux API 连通性测试")
    parser.add_argument("--key", help="Zenmux API Key (临时测试用，推荐用环境变量)")
    parser.add_argument("--model", default="anthropic/claude-fable-5", help="模型ID")
    args = parser.parse_args()

    api_key = args.key or os.getenv("ZENMUX_API_KEY", "")

    if not api_key:
        print("❌ 未找到 API Key")
        print("\n用法:")
        print("  1. 环境变量: $env:ZENMUX_API_KEY='your-key' ; python test_zenmux.py")
        print("  2. 命令行参数: python test_zenmux.py --key sk-xxx")
        sys.exit(1)

    # 安全提示：如果 Key 通过命令行传入，提醒用户
    if args.key:
        print("⚠️  警告: Key 通过命令行参数传入，可能留在 shell 历史记录里")
        print("   推荐方式: 使用环境变量 ZENMUX_API_KEY\n")

    success = test_connection(api_key, args.model)

    if success:
        print("\n✅ 连通性测试通过！")
    else:
        print("\n❌ 连通性测试失败，请检查 Key 和模型名称")
        sys.exit(1)


if __name__ == "__main__":
    main()
