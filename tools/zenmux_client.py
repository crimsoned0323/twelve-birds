#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zenmux API 调用脚本
完全兼容 OpenAI SDK，只需替换 base_url 和 api_key

环境变量:
  ZENMUX_API_KEY - 你的 Zenmux API Key (必填)
  ZENMUX_BASE_URL - API 地址 (可选，默认 https://zenmux.ai/api/v1)

用法:
  python zenmux_client.py                    # 基础对话
  python zenmux_client.py --stream           # 流式输出
  python zenmux_client.py --model anthropic/claude-sonnet-4.5  # 切换模型
  python zenmux_client.py --reasoning        # 开启推理模式
  python zenmux_client.py --web-search       # 开启网络搜索
"""

import os
import sys
import argparse
import json
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk


# ============ 配置 ============

BASE_URL = os.getenv("ZENMUX_BASE_URL", "https://zenmux.ai/api/v1")
API_KEY = os.getenv("ZENMUX_API_KEY", "")

if not API_KEY:
    print("❌ 错误: 未找到 ZENMUX_API_KEY 环境变量")
    print("请设置: export ZENMUX_API_KEY='your-key-here'")
    sys.exit(1)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============ 场景1: 基础对话 ============

def basic_chat(model: str, user_message: str) -> str:
    """基础非流式对话，返回完整回复文本"""
    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.7,
    )
    content = completion.choices[0].message.content
    usage = completion.usage
    print(f"[用量] prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
    return content


# ============ 场景2: 流式对话 ============

def stream_chat(model: str, user_message: str) -> None:
    """流式对话，逐字输出"""
    stream: Stream[ChatCompletionChunk] = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        stream=True,
        stream_options={"include_usage": True},  # 末尾 chunk 包含用量
    )
    print("[流式输出]")
    for chunk in stream:
        # 末尾 chunk 只有 usage，没有 choices
        if not chunk.choices:
            if chunk.usage:
                u = chunk.usage
                print(f"\n[用量] prompt={u.prompt_tokens}, completion={u.completion_tokens}, total={u.total_tokens}")
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
    print()  # 末尾换行


# ============ 场景3: 推理模式 (o系列/GPT-5) ============

def reasoning_chat(model: str, user_message: str, effort: str = "medium") -> None:
    """
    推理模式对话，输出思考过程 + 最终回复
    effort: none / minimal / low / medium / high / xhigh
    """
    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        reasoning_effort=effort,
    )
    msg = completion.choices[0].message
    if hasattr(msg, "reasoning") and msg.reasoning:
        print(f"[推理过程]\n{msg.reasoning}\n")
    print(f"[回复]\n{msg.content}")
    if completion.usage:
        u = completion.usage
        rt = u.completion_tokens_details.reasoning_tokens if u.completion_tokens_details else 0
        print(f"[用量] prompt={u.prompt_tokens}, completion={u.completion_tokens}(推理={rt}), total={u.total_tokens}")


# ============ 场景4: 网络搜索增强 ============

def web_search_chat(model: str, user_message: str) -> None:
    """开启网络搜索，模型可引用实时信息"""
    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        web_search_options={},  # 开启网络搜索
    )
    msg = completion.choices[0].message
    print(msg.content)
    # 输出引用来源
    if hasattr(msg, "annotations") and msg.annotations:
        print("\n[引用来源]")
        for ann in msg.annotations:
            if hasattr(ann, "url") and ann.url:
                print(f"  - {ann.url}")


# ============ 场景5: 多轮对话 ============

def multi_turn_chat(model: str) -> None:
    """多轮对话示例，保持上下文"""
    conversation = []

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ("/exit", "/quit", "退出"):
            print("对话结束。")
            break
        if user_input.lower() == "/clear":
            conversation.clear()
            print("上下文已清空。")
            continue

        conversation.append({"role": "user", "content": user_input})

        completion: ChatCompletion = client.chat.completions.create(
            model=model,
            messages=conversation,
            temperature=0.7,
        )
        assistant_reply = completion.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_reply})
        print(f"\n助手: {assistant_reply}")


# ============ 场景6: 工具调用 (Function Calling) ============

def tool_calling_demo(model: str) -> None:
    """
    工具调用示例: 让模型获取天气信息
    实际生产环境需要实现 get_weather 函数并执行工具调用循环
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的当前天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "城市名称，如'上海'、'Tokyo'"},
                    },
                    "required": ["location"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        tools=tools,
        tool_choice="auto",
        messages=[{"role": "user", "content": "上海今天天气怎么样？"}],
    )

    msg = completion.choices[0].message
    if msg.tool_calls:
        print("[模型请求调用工具]")
        for tc in msg.tool_calls:
            print(f"  工具: {tc.function.name}")
            print(f"  参数: {tc.function.arguments}")
    else:
        print(f"[直接回复] {msg.content}")


# ============ 场景7: JSON 结构化输出 ============

def json_output_demo(model: str, user_message: str) -> dict:
    """
    强制输出 JSON，并校验结构
    json_schema 模式可严格约束输出格式
    """
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "一句话总结"},
            "keywords": {"type": "array", "items": {"type": "string"}, "description": "关键词列表"},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
        },
        "required": ["summary", "keywords", "sentiment"],
        "additionalProperties": False,
    }

    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "analysis_result", "schema": schema},
        },
    )
    content = completion.choices[0].message.content
    result = json.loads(content)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


# ============ 场景8: 图片输入 (多模态) ============

def vision_demo(model: str, image_url: str, question: str = "描述这张图片") -> str:
    """图片理解，传入图片 URL 或 Base64"""
    completion: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )
    content = completion.choices[0].message.content
    print(content)
    return content


# ============ 入口 ============

def main():
    parser = argparse.ArgumentParser(description="Zenmux API 调用脚本")
    parser.add_argument("--model", default="openai/gpt-5", help="模型ID，格式 <provider>/<model>，默认 openai/gpt-5")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    parser.add_argument("--reasoning", action="store_true", help="开启推理模式")
    parser.add_argument("--web-search", action="store_true", help="开启网络搜索")
    parser.add_argument("--multi-turn", action="store_true", help="多轮对话模式")
    parser.add_argument("--tools", action="store_true", help="工具调用演示")
    parser.add_argument("--json-output", action="store_true", help="JSON结构化输出演示")
    parser.add_argument("--message", default="你好，请介绍一下你自己", help="用户消息")
    args = parser.parse_args()

    print(f"[Zenmux Client] model={args.model}")
    print(f"[Base URL] {BASE_URL}")
    print("-" * 50)

    if args.multi_turn:
        multi_turn_chat(args.model)
    elif args.stream:
        stream_chat(args.model, args.message)
    elif args.reasoning:
        reasoning_chat(args.model, args.message)
    elif args.web_search:
        web_search_chat(args.model, args.message)
    elif args.tools:
        tool_calling_demo(args.model)
    elif args.json_output:
        json_output_demo(args.model, args.message)
    else:
        result = basic_chat(args.model, args.message)
        print(result)


if __name__ == "__main__":
    main()
