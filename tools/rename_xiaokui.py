#!/usr/bin/env python3
"""
全局替换：将所有文件中的"小澪"替换为"小澪"
同时重命名包含"小澪"的文件名
"""

import os
import sys

PROJECT_ROOT = r"G:\codebuddy\十二飞鸟_codebuddy"

# 需要处理的文件扩展名
EXTENSIONS = {".txt", ".md", ".csv", ".html", ".py", ".mjs", ".json", ".bat", ".js"}

OLD = "小澪"
NEW = "小澪"

# 统计
files_modified = 0
files_renamed = 0
total_replacements = 0
skipped = []

# 需要跳过的目录
SKIP_DIRS = {".git", ".workbuddy", "node_modules", "__pycache__"}

for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
    # 跳过特定目录
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in EXTENSIONS:
            continue

        try:
            # 读取文件
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            except Exception as e:
                skipped.append(f"{filepath} (读取失败: {e})")
                continue

        if OLD not in content:
            continue

        # 统计替换次数
        count = content.count(OLD)
        total_replacements += count

        # 替换
        new_content = content.replace(OLD, NEW)

        # 写回
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            files_modified += 1
            print(f"  ✓ {os.path.relpath(filepath, PROJECT_ROOT)} ({count}处)")
        except Exception as e:
            skipped.append(f"{filepath} (写入失败: {e})")

# 处理文件名中包含"小澪"的文件
print("\n--- 检查文件名 ---")
for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

    for filename in filenames:
        if OLD in filename:
            old_path = os.path.join(dirpath, filename)
            new_name = filename.replace(OLD, NEW)
            new_path = os.path.join(dirpath, new_name)
            try:
                os.rename(old_path, new_path)
                files_renamed += 1
                print(f"  📁 重命名: {filename} → {new_name}")
            except Exception as e:
                skipped.append(f"{old_path} (重命名失败: {e})")

# 汇总
print(f"\n{'='*60}")
print(f"替换完成汇总:")
print(f"  修改文件数: {files_modified}")
print(f"  重命名文件数: {files_renamed}")
print(f"  总替换次数: {total_replacements}")
if skipped:
    print(f"  跳过: {len(skipped)} 个文件")
    for s in skipped:
        print(f"    - {s}")
print(f"{'='*60}")
