#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""压缩Day 41-53: 13天→8天"""

import os, re

BASE = r"g:\codebuddy\十二飞鸟_codebuddy\文字剧本"

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def merge(day_num, files):
    """合并多个文件为一个，只保留第一个文件的事件链头部"""
    parts = []
    first = True
    for fname in files:
        text = read(os.path.join(BASE, fname))
        if not first:
            # 去掉旧头部和事件链，只保留==========事件内容
            text = re.sub(r'(?s)^.*?(========== 事件)', r'\1', text)
        else:
            # 更新标题
            text = re.sub(r'Day \d+.*?=', f'Day {day_num}：', text, count=1)
        parts.append(text.strip())
        first = False
    result = "\n\n\n".join(parts) + "\n"
    out = os.path.join(BASE, f"Day{day_num}剧本_merged.txt")
    write(out, result)
    size_kb = len(result.encode("utf-8")) / 1024
    print(f"  [OK] Day{day_num} <- {'+'.join(files)} -> {size_kb:.1f} KB")
    # 同时覆盖原主文件
    main_out = os.path.join(BASE, f"Day{day_num}剧本.txt")
    if 41 <= day_num <= 48:
        write(main_out, result)

# 合并方案
merges = [
    (41, ["Day41剧本.txt", "Day42剧本.txt"]),           # 请帖+名单
    (42, ["Day43剧本.txt", "Day44剧本.txt"]),           # 角色分配+黑田试探
    (43, ["Day45剧本.txt"]),                             # 前夕(保持)
    (44, ["Day46剧本.txt", "Day47剧本.txt", "Day48剧本.txt"]),  # 青鹭+朱雀+夜鸢
    (45, ["Day49剧本.txt", "Day50剧本.txt", "Day51剧本.txt"]),  # 双雀+黄鹂+诡鹀
    (46, ["Day52剧本.txt", "Day53剧本.txt"]),            # 巢燕+雪代
    (47, ["Day54剧本.txt"]),                             # 好感度结算(保持)
    (48, ["Day55剧本.txt"]),                             # 最后的夜(保持)
]

print(">>> 压缩 Day 41-53 (13天->8天)")
print("=" * 50)

for day_num, files in merges:
    merge(day_num, files)

# 重命名 Day 56-60 → Day 49-53
renames = {
    "Day56剧本.txt": "Day49剧本.txt",
    "Day57剧本.txt": "Day50剧本.txt",
    "Day58剧本.txt": "Day51剧本.txt",
    "Day59剧本.txt": "Day52剧本.txt",
    "Day60剧本.txt": "Day53剧本.txt",
}

print("\n📋 重命名 Day 56-60 → Day 49-53")
for old, new in renames.items():
    old_path = os.path.join(BASE, old)
    new_path = os.path.join(BASE, new)
    text = read(old_path)
    # 更新内部Day引用
    old_num = int(re.search(r'Day\s*(\d+)', old).group(1))
    new_num = int(re.search(r'Day\s*(\d+)', new).group(1))
    text = text.replace(f"Day {old_num}", f"Day {new_num}")
    text = text.replace(f"Day{old_num}", f"Day{new_num}")
    write(new_path, text)
    print(f"  {old} → {new} ({len(text.encode('utf-8'))/1024:.1f} KB)")

print("\n✅ 完成。汇总:")
for f in sorted(os.listdir(BASE)):
    if f.startswith("Day") and f.endswith("剧本.txt") and not f.endswith("_merged.txt"):
        size = os.path.getsize(os.path.join(BASE, f)) / 1024
        print(f"  {f}: {size:.1f} KB")
