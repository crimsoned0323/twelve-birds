#!/usr/bin/env python3
"""
十二飞鸟 全剧本合集 整合脚本 v3.0
整合所有文字剧本（含P0修复文件）为一个完整合集
"""
import os
import re

BASE = r"G:\codebuddy\十二飞鸟_codebuddy\文字剧本"
OLD_COLLECTION = r"G:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_全剧本合集.txt"
OUTPUT = r"G:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_全剧本合集_v3.txt"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def extract_sections_from_old_collection():
    """从旧合集中提取 Day 42, 44, 46 的内容（这些天的剧本文件是错位的）"""
    with open(OLD_COLLECTION, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = {}
    # 找到所有 Day section header 的起始行（### 行）
    sep = "############################################################"
    day_pattern = re.compile(r"^#  Day (\d+):")
    day_starts = []
    for i, line in enumerate(lines):
        if line.startswith(sep) and i + 1 < len(lines):
            m = day_pattern.match(lines[i + 1])
            if m:
                day_starts.append((i, int(m.group(1))))

    # 提取 Day 42, 44, 46 的内容
    for idx, (start, day_num) in enumerate(day_starts):
        if day_num in (42, 44, 46):
            # 内容从这个 section 的 ### 开始
            # 到下一个 section 的 ### 开始（或文件末尾）
            if idx + 1 < len(day_starts):
                end = day_starts[idx + 1][0]
            else:
                end = len(lines)

            content = "".join(lines[start:end]).strip()
            sections[day_num] = content

    return sections

def build_file_list():
    """构建正确的文件顺序列表"""
    file_list = []

    # Day 1-2 (特殊命名，无"剧本"后缀)
    file_list.append(("Day 1", "Day1.txt"))
    file_list.append(("Day 2", "Day2.txt"))

    # Day 3-41
    for day in range(3, 42):
        file_list.append((f"Day {day}", f"Day{day}剧本.txt"))

    # Day 42 - 从旧合集提取
    file_list.append(("Day 42", None))  # special: from old collection

    # Day 43 - P0修复版
    file_list.append(("Day 43", "Day43剧本_new.txt"))

    # Day 44 - 从旧合集提取
    file_list.append(("Day 44", None))  # special: from old collection

    # Day 45 - P0修复版
    file_list.append(("Day 45", "Day45剧本_new.txt"))

    # Day 46 - 从旧合集提取
    file_list.append(("Day 46", None))  # special: from old collection

    # Day 47-52
    for day in range(47, 53):
        file_list.append((f"Day {day}", f"Day{day}剧本.txt"))

    # Day 53 - 共享路径缺失（Day53剧本.txt实为END-D草稿，内容已整合到Day59_endD.txt）
    file_list.append(("Day 53", None))  # special: missing marker

    # Day 54 - P0修复版
    file_list.append(("Day 54", "Day54剧本.txt"))

    return file_list

def build_ending_file_list():
    """构建四条结局路线的文件列表"""
    endings = {}

    # END-A: Day 55-60
    endings["END-A「法理的正义」"] = [
        (f"Day {day} (END-A)", f"Day{day}_endA.txt") for day in range(55, 61)
    ]

    # END-B: Day 55-60
    endings["END-B「堕落的正义」"] = [
        (f"Day {day} (END-B)", f"Day{day}_endB.txt") for day in range(55, 61)
    ]

    # END-C: Day 55-59 (P0修复新增)
    endings["END-C「彻底的沉沦」"] = [
        (f"Day {day} (END-C)", f"Day{day}_endC.txt") for day in range(55, 60)
    ]

    # END-D: Day 55-59 (P0修复新增)
    endings["END-D「朱雀的绽放 (真结局)」"] = [
        (f"Day {day} (END-D)", f"Day{day}_endD.txt") for day in range(55, 60)
    ]

    return endings

def main():
    print("=" * 60)
    print("  十二飞鸟 全剧本合集 整合脚本 v3.0")
    print("=" * 60)

    # 从旧合集提取缺失内容
    print("\n[1/4] 从旧合集提取 Day 42/44/46 内容...")
    old_sections = extract_sections_from_old_collection()
    for day in [42, 44, 46]:
        if day in old_sections:
            print(f"  ✓ Day {day}: 提取成功 ({len(old_sections[day])} 字符)")
        else:
            print(f"  ✗ Day {day}: 提取失败")

    # 构建共享路径
    print("\n[2/4] 读取共享路径剧本 (Day 1 ~ Day 54)...")
    shared_files = build_file_list()
    shared_content = []
    total_files = 0
    missing_files = []

    for day_label, filename in shared_files:
        if filename is None:
            day_num = int(day_label.split()[-1])
            if day_num in old_sections:
                # 从旧合集提取的内容 (Day 42/44/46)
                content = old_sections[day_num]
                shared_content.append(f"\n{'#' * 60}\n#  {day_label} (来源: 旧合集提取)\n{'#' * 60}\n\n{content}\n")
                total_files += 1
            else:
                # Day 53 共享路径缺失
                shared_content.append(f"\n{'#' * 60}\n#  {day_label} [共享路径剧本暂缺]\n{'#' * 60}\n\n")
                shared_content.append("[说明] Day 53 的共享路径剧本暂缺。文字剧本目录中的 Day53剧本.txt 实际为 END-D 路线的\n")
                shared_content.append("极乐之夜草稿（Day 53：极乐之夜 END-C·真结局路径），其内容已整合到 Day59_endD.txt 中。\n")
                shared_content.append("Day 53 共享路径内容待后续补写。\n\n")
                missing_files.append(day_label)
        else:
            filepath = os.path.join(BASE, filename)
            if os.path.exists(filepath):
                content = read_file(filepath)
                shared_content.append(f"\n{'#' * 60}\n#  {day_label}: {filename}\n{'#' * 60}\n\n{content}\n")
                total_files += 1
            else:
                shared_content.append(f"\n{'#' * 60}\n#  {day_label}: {filename} [文件不存在]\n{'#' * 60}\n\n[文件缺失]\n")
                missing_files.append(f"{day_label} ({filename})")

    print(f"  ✓ 成功读取 {total_files} 个文件")
    if missing_files:
        print(f"  ⚠ 缺失: {', '.join(missing_files)}")

    # 构建结局路线
    print("\n[3/4] 读取四条结局路线剧本...")
    endings = build_ending_file_list()
    ending_content = []
    ending_total = 0

    for ending_name, file_list in endings.items():
        ending_content.append(f"\n\n{'=' * 60}\n  {ending_name}\n{'=' * 60}\n")
        for day_label, filename in file_list:
            filepath = os.path.join(BASE, filename)
            if os.path.exists(filepath):
                content = read_file(filepath)
                ending_content.append(f"\n{'#' * 60}\n#  {day_label}: {filename}\n{'#' * 60}\n\n{content}\n")
                ending_total += 1
            else:
                ending_content.append(f"\n{'#' * 60}\n#  {day_label}: {filename} [文件不存在]\n{'#' * 60}\n\n[文件缺失]\n")
                missing_files.append(f"{day_label} ({filename})")

    print(f"  ✓ 成功读取 {ending_total} 个结局路线文件")

    # 写入合集
    print(f"\n[4/4] 写入合集文件: {OUTPUT}")
    header = """============================================================
  「十二飞鸟」全剧本合集 v3.0 (P0修复整合版)
  生成时间: 2026-06-28
============================================================

  版本说明:
  - v3.0 基于 P0 修复后的完整剧本整合
  - Day 43/45 使用 P0-P 修复版 (Day43剧本_new.txt / Day45剧本_new.txt)
  - Day 54 使用 P0-Q 修复版 (Day54剧本.txt)
  - END-C 路线使用 P0-R 新创作内容 (Day55~59_endC.txt)
  - END-D 路线使用 P0-R 新创作内容 (Day55~59_endD.txt)
  - Day 42/44/46 内容从旧合集(v2.0)提取 (原文件内容错位)
  - Day 53 共享路径暂缺 (Day53剧本.txt 实为 END-D 草稿)
  - BE 触发逻辑已重构 (参见 BE触发逻辑重构方案.md)

  结构:
  - 第一部分: 共享路径 (Day 1 ~ Day 54)
  - 第二部分: END-A 法理的正义 (Day 55 ~ Day 60)
  - 第三部分: END-B 堕落的正义 (Day 55 ~ Day 60)
  - 第四部分: END-C 彻底的沉沦 (Day 55 ~ Day 59)
  - 第五部分: END-D 朱雀的绽放·真结局 (Day 55 ~ Day 59)

  结局总数: 23个BE + 4个主线结局 = 27种
"""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n\n")
        f.write("=" * 60 + "\n")
        f.write("  第一部分: 共享路径 (Day 1 ~ Day 54)\n")
        f.write("=" * 60 + "\n")
        f.write("".join(shared_content))
        f.write("".join(ending_content))

    # 统计
    with open(OUTPUT, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
        total_chars = f.seek(0, 2)

    print(f"\n{'=' * 60}")
    print(f"  整合完成!")
    print(f"  总行数: {total_lines:,}")
    print(f"  总字符: {os.path.getsize(OUTPUT):,} bytes")
    print(f"  共享路径文件: {total_files} 个")
    print(f"  结局路线文件: {ending_total} 个")
    print(f"  总计: {total_files + ending_total} 个文件")
    if missing_files:
        print(f"  缺失文件: {len(missing_files)} 个")
        for m in missing_files:
            print(f"    - {m}")
    print(f"  输出: {OUTPUT}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
