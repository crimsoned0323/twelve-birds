#!/usr/bin/env python3
"""
十二飞鸟 v6 构建脚本
- 读取 v5 全剧本合集（10角色未遂节点链整合版）
- 读取5个诡鹀新事件CSV
- 将诡鹀个人线扩展内容整合进v5
- 输出 v6 全剧本合集

整合规划：
1. Day 21 事件三：诡鹀替身（37行）→ 替换原"佐藤指令"
2. Day 29 事件四后：诡鹀残留（31行）→ 案件线索
3. Day 35 事件五后：诡鹀破绽（32行）→ 破绽揭示
4. Day 41 事件一：诡鹀素颜（45行）→ 替换原"请帖印制"
5. BE10镜中人（28行）→ 作为独立BE分支附在Day 21后
"""

import os
import re
import sys
import csv

BASE = r"G:\codebuddy\十二飞鸟_codebuddy"
V5_PATH = os.path.join(BASE, "十二飞鸟_全剧本合集_v5.txt")
V6_PATH = os.path.join(BASE, "十二飞鸟_全剧本合集_v6.txt")
CSV_DIR = os.path.join(BASE, "csv剧本")

# ============================================================
# 1. 读取 v5 合集
# ============================================================

with open(V5_PATH, "r", encoding="utf-8") as f:
    v5_lines = f.readlines()

print(f"[v5] 读取 {len(v5_lines)} 行")

# ============================================================
# 2. 定位目标位置（基于已知grep结果）
# ============================================================

# 目标位置定义（行号基于v5中grep结果+awk验证）
# 注：行号为0-based数组下标

targets = {
    # Day 21 事件三：诡鹀替身 → 替换原"佐藤指令"块
    "day21_event3_replace": {
        "v5_start_line": None,  # 动态查找"事件三：佐藤指令"开始
        "v5_end_line": None,    # 动态查找"事件四"前一行
        "csv_file": "Day_21_事件三：诡鹀替身.csv",
        "label": "Day 21 事件三：诡鹀替身"
    },
    # Day 29 事件四后：诡鹀残留 → 插入事件四后
    "day29_event4_after": {
        "v5_insert_after": None,  # 动态查找"事件四：记者登场"结束
        "csv_file": "Day_29_事件四：诡鹀残留.csv",
        "label": "Day 29 诡鹀残留（插入事件四后）"
    },
    # Day 35 事件五后：诡鹀破绽 → 插入事件五后
    "day35_event5_after": {
        "v5_insert_after": None,  # 动态查找"事件五：沉默的报价"结束
        "csv_file": "Day_35_事件六：诡鹀破绽.csv",
        "label": "Day 35 诡鹀破绽（插入事件五后）"
    },
    # Day 41 事件一：诡鹀素颜 → 替换原"请帖印制"
    "day41_event1_replace": {
        "v5_start_line": None,  # 动态查找"事件一：请帖印制"开始
        "v5_end_line": None,    # 动态查找"事件二"前一行
        "csv_file": "Day_41_事件一：诡鹀素颜.csv",
        "label": "Day 41 事件一：诡鹀素颜"
    },
    # BE10镜中人 → 作为独立分支段，附在Day 21后
    "be10_append": {
        "v5_append_at": None,  # 动态查找"Day 21 结束·跳转 Day 22"前
        "csv_file": "BE10_镜中人.csv",
        "label": "BE10 镜中人"
    },
}

# ============================================================
# 3. 动态定位行号
# ============================================================

def find_event_range(lines, day, event_name_pattern):
    """找到指定Day的某事件的起止行号
    返回 (start_line, end_line)，其中end_line是该事件标记行之后到下一事件/Day结束标记之前
    """
    day_marker_pat = re.compile(rf'\s*Day {day}：')
    event_marker_pat = re.compile(rf'=+\s*事件[^=]*{re.escape(event_name_pattern)}[^=]*=+')
    day_end_pat = re.compile(rf'=+\s*Day {day} 结束')

    in_target_day = False
    event_start = None
    event_end = None

    for i, line in enumerate(lines):
        if day_marker_pat.search(line):
            in_target_day = True
            continue

        if in_target_day:
            if event_marker_pat.search(line) and event_start is None:
                event_start = i

            if event_start is not None and i > event_start:
                # 找下一个事件标记或Day结束
                if re.match(r'=+\s*事件', line) or day_end_pat.search(line):
                    event_end = i
                    return (event_start, event_end)

    return (event_start, event_end)


# 定位 Day 21 事件三：佐藤指令
day21_evt3 = find_event_range(v5_lines, 21, "佐藤指令")
targets["day21_event3_replace"]["v5_start_line"] = day21_evt3[0]
targets["day21_event3_replace"]["v5_end_line"] = day21_evt3[1]
print(f"[定位] Day 21 事件三: 行{day21_evt3[0]+1}-{day21_evt3[1]}")

# 定位 Day 41 事件一：请帖印制
day41_evt1 = find_event_range(v5_lines, 41, "请帖印制")
targets["day41_event1_replace"]["v5_start_line"] = day41_evt1[0]
targets["day41_event1_replace"]["v5_end_line"] = day41_evt1[1]
print(f"[定位] Day 41 事件一: 行{day41_evt1[0]+1}-{day41_evt1[1]}")

# 定位 Day 29 事件四：记者登场 (在结束前)
day29_evt4 = find_event_range(v5_lines, 29, "记者登场")
targets["day29_event4_after"]["v5_insert_after"] = day29_evt4[1]
print(f"[定位] Day 29 事件四: 结束行{day29_evt4[1]+1}")

# 定位 Day 35 事件五：沉默的报价
day35_evt5 = find_event_range(v5_lines, 35, "沉默的报价")
targets["day35_event5_after"]["v5_insert_after"] = day35_evt5[1]
print(f"[定位] Day 35 事件五: 结束行{day35_evt5[1]+1}")

# 定位 Day 21 结束·跳转 Day 22 行
for i, line in enumerate(v5_lines):
    if re.match(r'=+\s*Day 21 结束', line):
        targets["be10_append"]["v5_append_at"] = i
        print(f"[定位] Day 21 结束标记: 行{i+1}")
        break

# ============================================================
# 4. CSV转剧本格式
# ============================================================

def csv_to_script(csv_path, label):
    """将CSV转为剧本格式字符串列表"""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return []

    # 第一行是表头
    header = rows[0]
    # 列顺序: ID, Speaker, HeadProfile, CharLeft, CharMid, CharRight, Text, Background, BGM, Voice, Command, Note

    script_lines = []
    script_lines.append('\n')
    script_lines.append('=' * 60 + '\n')
    script_lines.append(f'  【诡鹀扩展】{label}\n')
    script_lines.append('=' * 60 + '\n')
    script_lines.append('\n')

    for row in rows[1:]:
        if not row or not row[0]:
            continue

        if len(row) < 12:
            row = row + [''] * (12 - len(row))

        id_val, speaker, head, cleft, cmid, cright, text, bgm, _, _, cmd, note = row[:12]

        # 输出场景描述
        if text and text.strip():
            script_lines.append(f'  {text}\n')

        # 输出立绘/表情描述
        if cleft and cleft != 'hide':
            script_lines.append(f'  [立绘-左: {cleft}]\n')
        if cmid and cmid != 'hide':
            script_lines.append(f'  [立绘-中: {cmid}]\n')
        if cright and cright != 'hide':
            script_lines.append(f'  [立绘-右: {cright}]\n')

        # 输出背景
        if bgm and bgm.strip():
            script_lines.append(f'  [BGM: {bgm}]\n')

        # 输出指令
        if cmd and cmd.strip():
            script_lines.append(f'  [指令: {cmd}]\n')

        # 输出ID备注
        if id_val and id_val.strip():
            script_lines.append(f'  #{id_val}\n')

        script_lines.append('\n')

    return script_lines


# ============================================================
# 5. 收集所有变更
# ============================================================

# 变更操作列表：(操作类型, 参考行号, 内容/起止行号, 标签)
operations = []

# 操作1: 替换 Day 21 事件三
op1_csv = csv_to_script(
    os.path.join(CSV_DIR, targets["day21_event3_replace"]["csv_file"]),
    targets["day21_event3_replace"]["label"]
)
operations.append(('replace', targets["day21_event3_replace"]["v5_start_line"],
                   targets["day21_event3_replace"]["v5_end_line"],
                   op1_csv, targets["day21_event3_replace"]["label"]))

# 操作2: 在 Day 29 事件四后插入
op2_csv = csv_to_script(
    os.path.join(CSV_DIR, targets["day29_event4_after"]["csv_file"]),
    targets["day29_event4_after"]["label"]
)
operations.append(('insert_after', targets["day29_event4_after"]["v5_insert_after"],
                   None, op2_csv, targets["day29_event4_after"]["label"]))

# 操作3: 在 Day 35 事件五后插入
op3_csv = csv_to_script(
    os.path.join(CSV_DIR, targets["day35_event5_after"]["csv_file"]),
    targets["day35_event5_after"]["label"]
)
operations.append(('insert_after', targets["day35_event5_after"]["v5_insert_after"],
                   None, op3_csv, targets["day35_event5_after"]["label"]))

# 操作4: 替换 Day 41 事件一
op4_csv = csv_to_script(
    os.path.join(CSV_DIR, targets["day41_event1_replace"]["csv_file"]),
    targets["day41_event1_replace"]["label"]
)
operations.append(('replace', targets["day41_event1_replace"]["v5_start_line"],
                   targets["day41_event1_replace"]["v5_end_line"],
                   op4_csv, targets["day41_event1_replace"]["label"]))

# 操作5: BE10 在 Day 21 结束前插入
op5_csv = csv_to_script(
    os.path.join(CSV_DIR, targets["be10_append"]["csv_file"]),
    targets["be10_append"]["label"]
)
operations.append(('insert_before', targets["be10_append"]["v5_append_at"],
                   None, op5_csv, targets["be10_append"]["label"]))

# ============================================================
# 6. 应用变更（从大到小处理行号）
# ============================================================

# 排序：按主要参考行号从大到小
def sort_key(op):
    op_type, ref, end, _, _ = op
    if op_type == 'replace':
        return ref  # 用 start_line
    elif op_type == 'insert_after':
        return ref
    elif op_type == 'insert_before':
        return ref
    return ref

operations.sort(key=sort_key, reverse=True)
print(f"\n[操作] 共 {len(operations)} 个变更（从大到小行号）:")
for op in operations:
    print(f"  - {op[0]}: 行{op[1]+1} -> {op[4]}")

v6_lines = list(v5_lines)

for op_type, ref, end, content, label in operations:
    if op_type == 'replace':
        # 替换: 删除 [ref, end) 范围，插入 content
        v6_lines[ref:end] = content
        print(f"  [应用] 替换 行{ref+1}-{end} -> {label}")
    elif op_type == 'insert_after':
        # 在 ref 行之后插入
        v6_lines[ref+1:ref+1] = content
        print(f"  [应用] 在行{ref+1}后插入 -> {label}")
    elif op_type == 'insert_before':
        # 在 ref 行之前插入
        v6_lines[ref:ref] = content
        print(f"  [应用] 在行{ref+1}前插入 -> {label}")

# ============================================================
# 7. 更新头部说明
# ============================================================

# 替换v5头为v6头
for i, line in enumerate(v6_lines[:20]):
    if 'v5.0' in line:
        v6_lines[i] = line.replace('v5.0', 'v6.0')
    if 'v4.0' in line:
        v6_lines[i] = line.replace('v4.0', 'v6.0')

# 在头部添加v6说明
header_note = """
============================================================
#  v6.0 更新内容（诡鹀个人线扩展版）：
#  - Day 21 事件三:诡鹀替身（替换佐藤指令,3分支选择）
#  - Day 29 事件四后:诡鹀残留（31行,白檀气味+雪代端杯=增田案现场痕迹）
#  - Day 35 事件五后:诡鹀破绽（32行,模仿葵时按压手腕=增田尸体左臂痕迹）
#  - Day 41 事件一:诡鹀素颜（45行,狐狸发卡仪式+旧疤+棉布铁锈气味完结）
#  - BE10 镜中人（28行,半面面具+栽赃+「经理...我找不到我了」）
#  - 诡鹀模仿能力5大设计空间全部激活:
#    残留→案件钥匙 / 替身→BE触发 / 素颜→案件线索 / 辨别真假→玩法 / 模仿代价→情感
============================================================

"""

# 在第一个"===="行之前插入头部说明
for i, line in enumerate(v6_lines):
    if '第一部分：共享路径' in line:
        v6_lines[i:i] = [header_note]
        break

# ============================================================
# 8. 写入 v6
# ============================================================

with open(V6_PATH, "w", encoding="utf-8") as f:
    f.writelines(v6_lines)

print(f"\n[v6] 写入完成: {V6_PATH}")
print(f"[v6] 总行数: {len(v6_lines)}")
print(f"[v6] 文件大小: {os.path.getsize(V6_PATH) / 1024:.1f} KB")
print(f"[v6] 较v5变化: +{len(v6_lines) - len(v5_lines)} 行")
