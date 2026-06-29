#!/usr/bin/env python3
"""
十二飞鸟 v5 构建脚本
- 读取 v4 全剧本合集
- 读取10个角色的未遂节点链文件
- 解析每个节点的场景内容
- 按标注的插入位置，精确插入到v4的对应Day/事件位置
- 输出 v5 全剧本合集
"""

import re
import os
import sys

BASE = r"G:\codebuddy\十二飞鸟_codebuddy"
V4_PATH = os.path.join(BASE, "十二飞鸟_全剧本合集_v4.txt")
V5_PATH = os.path.join(BASE, "十二飞鸟_全剧本合集_v5.txt")
NODE_DIR = os.path.join(BASE, "文字剧本")

# ============================================================
# 1. 读取 v4 合集
# ============================================================
with open(V4_PATH, "r", encoding="utf-8") as f:
    v4_lines = f.readlines()

print(f"[v4] 读取 {len(v4_lines)} 行")

# ============================================================
# 2. 解析 v4 结构
#    - day_end_marks: {day_num: line_index}  "========== Day X 结束" 的行号
#    - event_marks: {(day_num, event_ordinal): line_index}  "========== 事件X：" 的行号
#    - day_start_marks: {day_num: line_index}  "  Day X：" 标题行的行号
# ============================================================

day_end_marks = {}    # Day X 结束·跳转 -> 在此行之前插入"Day末尾"节点
day_start_marks = {}  # Day X 标题行 -> 在此行之后插入"Day开头"节点
event_marks = {}      # (day_num, event_ordinal) -> 事件标记行号

cn_num_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}

current_day = None
for i, line in enumerate(v4_lines):
    # Day 标题行: "  Day 13：生日蜡烛 (1310~1314)"
    m = re.match(r'\s+Day (\d+)：', line)
    if m:
        current_day = int(m.group(1))
        day_start_marks[current_day] = i
        continue

    # Day 结束标记: "========== Day 13 结束·跳转 Day 14 ==========" 或 "========== Day 19 结束 =========="
    m = re.match(r'=+\s*Day (\d+) 结束', line)
    if m:
        day_num = int(m.group(1))
        day_end_marks[day_num] = i
        continue

    # 事件标记: "========== 事件一：佐藤日常 1301 =========="
    # 也可能是: "========== 事件一：第一批情报 ==========" （没有ID）
    m = re.match(r'=+\s*事件([一二三四五六七八九十])[：:](.+?)=+', line)
    if m and current_day:
        event_ordinal = cn_num_map.get(m.group(1), 0)
        if event_ordinal > 0:
            event_marks[(current_day, event_ordinal)] = i

print(f"[v4] 解析到 {len(day_end_marks)} 个Day结束标记, {len(event_marks)} 个事件标记")

# ============================================================
# 3. 读取节点链文件，提取场景内容
#    每个节点链文件的结构：
#    - "============================================================" 大分隔线
#    - "  节点X：标题（插入位置说明）" 节点标题行
#    - "【插入位置】..." 插入位置说明
#    - "【设计说明】..." 设计说明
#    - "==============================" 小分隔线（场景内容开始标志）
#    - "#地点 时间" 场景标签
#    - ... 场景内容 ...
#    - "============================================================" 下一个大分隔线（场景内容结束）
#
#    提取规则：从"=============="小分隔线之后的第一个"#"行开始，
#    到下一个"============================================================"大分隔线结束。
# ============================================================

def extract_node_scenes(filepath):
    """从节点链文件中提取所有节点的场景内容。
    返回列表：[{title, position_desc, scene_lines: [str, ...]}, ...]

    文件结构：
      ====（大分隔60=）  <- big_sep_indices[i]
      节点X：标题        <- title line
      ====（大分隔60=）  <- big_sep_indices[i+1]
      【插入位置】...
      【设计说明】...
      ====（小分隔30=）  <- scene start marker
      #地点 时间
      ... 场景内容 ...
      ====（大分隔60=）  <- big_sep_indices[i+2]  下一节点的标题开始

    所以：标题在 big_sep[i]~big_sep[i+1] 之间
          内容在 big_sep[i+1]~big_sep[i+2] 之间
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split('\n')

    # 找到所有大分隔线（50+等号）的位置
    big_sep_indices = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) >= 50 and all(c == '=' for c in stripped):
            big_sep_indices.append(i)

    nodes = []
    # 遍历大分隔线对，寻找"标题块"
    # 标题块：big_sep[i] 和 big_sep[i+1] 之间只有一行非空行，且包含"节点"
    idx = 0
    while idx < len(big_sep_indices) - 1:
        # 检查 big_sep[idx] ~ big_sep[idx+1] 之间是否是标题块
        title_start = big_sep_indices[idx] + 1
        title_end = big_sep_indices[idx + 1]
        title_block = lines[title_start:title_end]

        # 找到第一个非空行
        title_line = ''
        non_empty_count = 0
        for bl in title_block:
            if bl.strip():
                non_empty_count += 1
                if not title_line:
                    title_line = bl.strip()

        # 标题块应该只有1~2行非空内容，且包含"节点"
        if '节点' in title_line and non_empty_count <= 2:
            # 找到了标题块！内容在 big_sep[idx+1] ~ big_sep[idx+2] 之间
            if idx + 2 < len(big_sep_indices):
                content_start = big_sep_indices[idx + 1] + 1
                content_end = big_sep_indices[idx + 2]
            else:
                # 最后一个节点，内容到文件末尾
                content_start = big_sep_indices[idx + 1] + 1
                content_end = len(lines)

            content_block = lines[content_start:content_end]

            # 提取插入位置说明
            position_desc = ''
            for j, bl in enumerate(content_block):
                if '【插入位置】' in bl:
                    position_desc = bl.strip()
                    for k in range(j + 1, min(j + 5, len(content_block))):
                        if content_block[k].strip() and not content_block[k].strip().startswith('【'):
                            position_desc += ' ' + content_block[k].strip()
                        else:
                            break
                    break

            # 找到小分隔线（30~49个等号）
            small_sep_idx = None
            for j, bl in enumerate(content_block):
                stripped = bl.strip()
                if 30 <= len(stripped) <= 49 and all(c == '=' for c in stripped):
                    small_sep_idx = j
                    break

            if small_sep_idx is None:
                # 如果没有小分隔线，尝试找以#开头的行作为场景开始
                for j, bl in enumerate(content_block):
                    if bl.strip().startswith('#'):
                        small_sep_idx = j - 1
                        break

            if small_sep_idx is not None:
                scene_lines = content_block[small_sep_idx + 1:]
            else:
                # 退回到设计说明之后
                scene_lines = content_block
                # 尝试跳过【插入位置】和【设计说明】部分
                skip = True
                skipped_lines = []
                for bl in scene_lines:
                    if bl.strip().startswith('#'):
                        skip = False
                    if not skip:
                        skipped_lines.append(bl)
                scene_lines = skipped_lines

            # 去除首尾空行
            while scene_lines and not scene_lines[0].strip():
                scene_lines.pop(0)
            while scene_lines and not scene_lines[-1].strip():
                scene_lines.pop()

            if scene_lines:
                nodes.append({
                    'title': title_line,
                    'position_desc': position_desc,
                    'scene_lines': scene_lines
                })

            # 跳过下一个大分隔线（它属于内容块的结束=下一标题块的开始）
            idx += 2
        else:
            idx += 1

    return nodes


# 10个角色文件
node_files = {
    '青鹭姬': '青鹭姬_未遂节点链_阶段2-4.txt',
    '白鹤姬': '白鹤姬_未遂节点链_阶段2-4.txt',
    '巢燕姬': '巢燕姬_未遂节点链_阶段2-4.txt',
    '朱雀姬': '朱雀姬_未遂节点链_阶段2-4.txt',
    '黄鹂姬': '黄鹂姬_未遂节点链_阶段2-4.txt',
    '雏鹃姬': '雏鹃姬_未遂节点链_阶段2-4.txt',
    '银鹮姬': '银鹮姬_未遂节点链_阶段2-4.txt',
    '诡鹀姬': '诡鹀姬_未遂节点链_阶段2-4.txt',
    '神鸦姬': '神鸦姬_未遂节点链_阶段2-4.txt',
    '双雀姬': '双雀姬_未遂节点链_阶段2-4.txt',
}

all_nodes = {}  # {role_name: [node_list]}
for role, filename in node_files.items():
    filepath = os.path.join(NODE_DIR, filename)
    if os.path.exists(filepath):
        nodes = extract_node_scenes(filepath)
        all_nodes[role] = nodes
        print(f"[节点链] {role}: 提取到 {len(nodes)} 个节点")
    else:
        print(f"[警告] 文件不存在: {filepath}")

# ============================================================
# 4. 定义插入位置映射
#    每个节点 -> (day_num, position_type, ref_event_ordinal)
#    position_type:
#      'day_end'    -> 在Day末尾（Day结束标记之前）
#      'before_event' -> 在某事件之前
#      'after_event'  -> 在某事件之后（= 在下一事件之前）
# ============================================================

# 格式: (角色, 节点序号0-based) -> (day, position_type, event_ordinal)
# event_ordinal: 1=事件一, 2=事件二, ...
# 对于'day_end'，event_ordinal不用
INSERT_MAP = {
    # === Day 13 ===
    ('巢燕姬', 0): (13, 'before_event', 4),    # Day 13 事件三之后 = 事件四之前
    ('青鹭姬', 0): (13, 'day_end', None),       # Day 13 事件五之后，Day 13→14跳转前
    ('白鹤姬', 0): (13, 'day_end', None),       # Day 13 末尾

    # === Day 14 ===
    ('诡鹀姬', 0): (14, 'before_event', 1),     # Day 14 凌晨 = 事件一之前

    # === Day 15 ===
    ('双雀姬', 0): (15, 'before_event', 2),     # Day 15 事件一与二之间 = 事件二之前

    # === Day 16 ===
    # 朱雀/黄鹂/神鸦都插在事件三之前（事件二之后）
    ('朱雀姬', 0): (16, 'before_event', 3),     # Day 16 事件二之后，事件三之前
    ('黄鹂姬', 0): (16, 'before_event', 3),     # Day 16 事件二与三之间
    ('神鸦姬', 0): (16, 'before_event', 3),     # Day 16 事件二之后（大扫除）

    # === Day 17 ===
    ('银鹮姬', 0): (17, 'day_end', None),       # Day 17 事件之后，Day 17→18跳转前

    # === Day 18 ===
    ('青鹭姬', 1): (18, 'before_event', 3),     # Day 18 事件二和三之间
    ('雏鹃姬', 0): (18, 'before_event', 3),     # Day 18 事件二与三之间
    ('白鹤姬', 1): (18, 'day_end', None),       # Day 18 傍晚，Day 18→19跳转前

    # === Day 19/20 ===
    ('白鹤姬', 2): (19, 'day_end', None),       # Day 19 傍晚（节点三-B）
    ('巢燕姬', 1): (20, 'after_event', 3),      # Day 20 傍晚，银鹮引荐(事件三)之后

    # === Day 22 ===
    ('黄鹂姬', 1): (22, 'day_end', None),       # Day 22 事件四之后

    # === Day 23 ===
    ('朱雀姬', 1): (23, 'before_event', 2),     # Day 23 事件一与二之间
    ('雏鹃姬', 1): (23, 'before_event', 3),     # Day 23 事件二与三之间

    # === Day 25 ===
    ('诡鹀姬', 1): (25, 'day_end', None),       # Day 25 下午

    # === Day 26/27 ===
    ('银鹮姬', 1): (26, 'day_end', None),       # Day 26 深夜
    ('神鸦姬', 1): (27, 'after_event', 1),      # Day 27 午后，事件一之后
    ('青鹭姬', 2): (27, 'day_end', None),       # Day 27或28 深夜

    # === Day 28/29 ===
    ('白鹤姬', 3): (28, 'day_end', None),       # Day 28-29 深夜
    ('巢燕姬', 2): (28, 'before_event', 4),     # Day 28 下午，事件之前（插在事件四之前或找一个事件之前）
    ('黄鹂姬', 2): (28, 'day_end', None),       # Day 28 事件四之后
    ('雏鹃姬', 2): (29, 'before_event', 3),     # Day 29 事件二与三之间
    ('双雀姬', 1): (29, 'day_end', None),       # Day 29 下午

    # === Day 33 ===
    ('朱雀姬', 2): (33, 'day_end', None),       # Day 33 事件四之后

    # === Day 37 ===
    ('神鸦姬', 2): (37, 'after_event', 1),      # Day 37 上午，事件一之后
    ('诡鹀姬', 2): (37, 'day_end', None),       # Day 37 深夜

    # === Day 39 ===
    ('银鹮姬', 2): (39, 'day_end', None),       # Day 39 现有事件之后

    # === Day 40/41 ===
    ('双雀姬', 2): (40, 'day_end', None),       # Day 40 深夜 + Day 41 清晨
}

# ============================================================
# 5. 计算每个节点的插入行号
# ============================================================

def get_insert_line(day_num, pos_type, event_ordinal):
    """根据Day、位置类型、事件序号，返回在v4_lines中的插入行号（0-based）。
    插入内容将放在该行号之前。
    """
    if pos_type == 'day_end':
        # 在Day结束标记之前插入
        if day_num in day_end_marks:
            return day_end_marks[day_num]
        else:
            # 如果没有Day结束标记，找下一个Day的开始
            if (day_num + 1) in day_start_marks:
                return day_start_marks[day_num + 1]
            print(f"  [警告] 找不到Day {day_num} 的结束标记，跳过")
            return None

    elif pos_type == 'before_event':
        # 在某事件之前插入
        key = (day_num, event_ordinal)
        if key in event_marks:
            return event_marks[key]
        else:
            # 如果该事件不存在，退回到Day末尾
            print(f"  [警告] Day {day_num} 事件{event_ordinal} 不存在，退回Day末尾")
            if day_num in day_end_marks:
                return day_end_marks[day_num]
            return None

    elif pos_type == 'after_event':
        # 在某事件之后 = 在下一事件之前
        key = (day_num, event_ordinal + 1)
        if key in event_marks:
            return event_marks[key]
        else:
            # 没有下一事件，退回到Day末尾
            if day_num in day_end_marks:
                return day_end_marks[day_num]
            print(f"  [警告] Day {day_num} 事件{event_ordinal}之后无处插，退回Day末尾")
            return None

    return None


# 收集所有插入点
inserts = []  # [(line_num, role, node_title, scene_lines), ...]

for (role, node_idx), (day_num, pos_type, event_ordinal) in INSERT_MAP.items():
    if role not in all_nodes:
        print(f"  [警告] 角色 {role} 没有节点链文件，跳过")
        continue
    if node_idx >= len(all_nodes[role]):
        print(f"  [警告] {role} 节点序号 {node_idx} 超出范围（共{len(all_nodes[role])}个节点），跳过")
        continue

    node = all_nodes[role][node_idx]
    insert_line = get_insert_line(day_num, pos_type, event_ordinal)

    if insert_line is not None:
        inserts.append((insert_line, role, node['title'], node['scene_lines']))
        print(f"  [插入] {role} - {node['title'][:30]}... -> v4行{insert_line+1} (Day{day_num} {pos_type})")
    else:
        print(f"  [跳过] {role} - {node['title'][:30]}... (找不到插入位置)")

# ============================================================
# 6. 按行号从大到小排序，逐个插入
# ============================================================

inserts.sort(key=lambda x: x[0], reverse=True)

print(f"\n总共 {len(inserts)} 个插入点，开始构建v5...")

v5_lines = list(v4_lines)  # 复制

for insert_line, role, title, scene_lines in inserts:
    # 构建插入内容
    insert_content = []
    insert_content.append('\n')
    insert_content.append('============================================================\n')
    insert_content.append(f'  【未遂节点链】{role} - {title}\n')
    insert_content.append('============================================================\n')
    insert_content.append('\n')

    for sl in scene_lines:
        # 确保每行以换行符结尾
        if not sl.endswith('\n'):
            insert_content.append(sl + '\n')
        else:
            insert_content.append(sl)

    insert_content.append('\n')

    # 在insert_line位置之前插入
    v5_lines[insert_line:insert_line] = insert_content

# ============================================================
# 7. 更新文件头
# ============================================================

# 替换v4头为v5头
for i, line in enumerate(v5_lines[:10]):
    if 'v4.0' in line:
        v5_lines[i] = line.replace('v4.0', 'v5.0')
    if '去重版' in line:
        v5_lines[i] = v5_lines[i].replace('去重版', '去重版 + 10角色未遂节点链整合版')

# 在头部添加说明
header_note = """
============================================================
#  v5.0 更新内容：
#  - 整合10个角色（青鹭/白鹤/巢燕/朱雀/黄鹂/雏鹃/银鹮/诡鹀/神鸦/双雀）
#    的防线崩塌弧未遂节点链，共30个节点
#  - 每节点3个微裂痕场景，覆盖阶段二~四
#  - 所有节点按标注的精确位置插入对应Day/事件之间
#  - 标记为【未遂节点链】以便区分
============================================================

"""

# 在第一个"===="行之前插入头部说明
for i, line in enumerate(v5_lines):
    if '第一部分：共享路径' in line:
        v5_lines[i:i] = [header_note]
        break

# ============================================================
# 8. 写入 v5
# ============================================================

with open(V5_PATH, "w", encoding="utf-8") as f:
    f.writelines(v5_lines)

print(f"\n[v5] 写入完成: {V5_PATH}")
print(f"[v5] 总行数: {len(v5_lines)}")
print(f"[v5] 文件大小: {os.path.getsize(V5_PATH) / 1024:.1f} KB")
print(f"[v5] 插入节点数: {len(inserts)}")
