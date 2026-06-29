#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「十二飞鸟」文字剧本 → CSV 剧本 半自动转化工具
==============================================
解析文字剧本格式，生成与现有CSV格式完全兼容的剧本文件。
不改变CSV格式（12列：ID,Speaker,HeadProfile,CharLeft,CharMid,CharRight,Text,Background,BGM,Voice,Command,Note）

用法：
    python txt_to_csv.py <文字剧本.txt> [输出目录]

示例：
    python txt_to_csv.py ../文字剧本/Day3剧本.txt ../csv剧本/
"""

import csv
import io
import os
import re
import sys
from collections import OrderedDict

# Windows GBK → UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置区（根据项目需要调整）
# ============================================================

# 【映射表1】剧本中角色简称 → CSV Speaker 全名
SPEAKER_MAP = {
    "白鹤姬":            "白鹤姬·桂原雪代",
    "桂原雪代":          "白鹤姬·桂原雪代",
    "白鹤姬·桂原雪代":   "白鹤姬·桂原雪代",
    "雪代":              "白鹤姬·桂原雪代",
    "白鹤姐":            "白鹤姬·桂原雪代",

    "早莺姬":            "早莺姬·小野南梨",
    "小野南梨":          "早莺姬·小野南梨",
    "南梨":              "早莺姬·小野南梨",

    "巢燕姬":            "巢燕姬·谷川景子",
    "谷川景子":          "巢燕姬·谷川景子",
    "景子":              "巢燕姬·谷川景子",

    "青鹭姬":            "青鹭姬·星野葵",
    "星野葵":            "青鹭姬·星野葵",
    "葵":                "青鹭姬·星野葵",

    "黄鹂姬":            "黄鹂姬·日向夏实",
    "日向夏实":          "黄鹂姬·日向夏实",
    "夏实":              "黄鹂姬·日向夏实",

    "神鸦姬":            "神鸦姬·神乐坂紫",
    "神乐坂紫":          "神鸦姬·神乐坂紫",
    "紫":                "神鸦姬·神乐坂紫",

    "朱雀姬":            "朱雀姬·Linda",
    "Linda":             "朱雀姬·Linda",
    "朱雀":              "朱雀姬·Linda",

    "夜鸢姬":            "夜鸢姬·美咲蔷薇",
    "美咲蔷薇":          "夜鸢姬·美咲蔷薇",
    "蔷薇":              "夜鸢姬·美咲蔷薇",

    "双雀姬":            "双雀姬·濑户彩",
    "濑户彩":            "双雀姬·濑户彩",
    "彩":                "双雀姬·濑户彩",
    "濑户瞳":            "双雀姬·濑户瞳",
    "瞳":                "双雀姬·濑户瞳",

    "雏鹃姬":            "雏鹃姬·芦田育子",
    "芦田育子":          "雏鹃姬·芦田育子",
    "育子":              "雏鹃姬·芦田育子",

    "银鹮姬":            "银鹮姬·神宫寺丽莎",
    "神宫寺丽莎":        "银鹮姬·神宫寺丽莎",
    "丽莎":              "银鹮姬·神宫寺丽莎",

    "诡鹀姬":            "诡鹀姬·木岛春奈",
    "木岛春奈":          "诡鹀姬·木岛春奈",
    "春奈":              "诡鹀姬·木岛春奈",

    "小林莉香":          "小林莉香",
    "莉香":              "小林莉香",

    # 配角
    "拉面店老板":        "拉面店老板",
    "增田一郎":          "增田一郎",
    "增田":              "增田一郎",
    "佐藤正义":          "佐藤正义",
    "佐藤":              "佐藤正义",
    "村上道也":          "村上道也",
    "江口裕二":          "江口裕二",

    # 未知/代称
    "？？？":            "？？？",

    # 通用NPC
    "小女孩":            "小澪",
    "陌生男子A":         "陌生男子A",
    "陌生男子B":         "陌生男子B",
    "陌生男子":          "陌生男子A",
    "寝具店员":          "寝具店员",
}

# 【映射表2】HeadProfile 简称 → 完整立绘ID
HEADPROFILE_MAP = {
    "白鹤姬·桂原雪代":   "hide",
    "白银姬·小野南梨":   "hide",
    "巢燕姬·谷川景子":   "hide",
    "青鹭姬·星野葵":     "hide",
    "黄鹂姬·日向夏实":   "hide",
    "神鸦姬·神乐坂紫":   "hide",
    "朱雀姬·Linda":      "hide",
    "夜鸢姬·美咲蔷薇":   "hide",
    "双雀姬·濑户彩":     "hide",
    "双雀姬·濑户瞳":     "hide",
    "雏鹃姬·芦田育子":   "hide",
    "银鹮姬·神宫寺丽莎": "hide",
    "诡鹀姬·木岛春奈":   "hide",
    "小林莉香":           "hide",
    "拉面店老板":         "hide",
    "增田一郎":           "hide",
    "佐藤正义":           "hide",
    "村上道也":           "hide",
    "江口裕二":           "hide",
}

# 【映射表3】地点关键词 → Background
BACKGROUND_MAP = OrderedDict([
    ("Club_away",          ["远处", "外围", "鹤羽小路", "巷子"]),
    ("Club_outside",       ["建筑外", "没有招牌", "五层", "巷子尽头"]),
    ("Club_door",          ["门外", "门前", "门就在"]),
    ("Corridor",           ["走廊", "过道"]),
    ("Manager_Office",     ["经理办公室", "办公室", "办公桌"]),
    ("RestRoom",           ["休息室", "休息区"]),
    ("DressingRoom",       ["化妆间", "更衣室"]),
    ("VIP_Room",           ["VIP室", "VIP区", "包厢"]),
    ("Jan_Room",           ["白鹤姬的房间", "雪代的房间", "一月房间"]),
    ("Bathroom_Jan",       ["浴室", "浴缸"]),
    ("Rooftop",            ["天台", "屋顶"]),
    ("Club_lobby",         ["大厅", "前台"]),
    ("Club_Storage",       ["储物间", "杂物间"]),
    ("Apartment",          ["公寓", "租住", "六叠"]),
    ("RamenShop",          ["拉面店", "拉面"]),
    ("ShoppingStreet",     ["商店街", "拱廊", "店铺"]),
    ("BedStore",           ["寝具店", "床垫"]),
    ("Hospital",           ["医院", "病房"]),
    ("Cafe",               ["咖啡馆", "咖啡"]),
    ("Club_away",          ["大阪的夜空", "大阪最繁华"]),
])

# 【映射表4】情绪/场景关键词 → BGM
BGM_MAP = OrderedDict([
    ("Mixed_Emotion",      ["日常", "准备", "醒来", "早上", "午后"]),
    ("Unreal_Memory",      ["回忆", "过去", "十六岁", "曾"]),
    ("Slow_Lure",          ["浴室", "浴缸", "香气", "甜腻", "诱惑"]),
    ("Coming_Dangerous",   ["危险", "恐惧", "紧张", "冰冷", "杀气"]),
    ("Warm_Encounter",     ["温柔", "温暖", "帮助", "善意"]),
    ("Silent_Night",       ["深夜", "凌晨", "安静", "黑暗", "失眠"]),
    ("Mystery_Box",        ["黑皮书", "秘密", "情报", "线索"]),
    ("Melancholy_Rain",    ["悲伤", "泪水", "哭泣", "痛苦"]),
])


def resolve_speaker(raw_name):
    """将剧本中的角色简称解析为CSV标准Speaker名"""
    raw_name = raw_name.strip()
    if raw_name in SPEAKER_MAP:
        return SPEAKER_MAP[raw_name]
    # 模糊匹配
    for key, value in SPEAKER_MAP.items():
        if key in raw_name or raw_name in key:
            return value
    print(f"  ⚠ 警告：未识别的角色名 '{raw_name}'，将原样使用")
    return raw_name


def guess_background(text, current_bg):
    """根据文本内容猜测背景场景"""
    for bg, keywords in BACKGROUND_MAP.items():
        for kw in keywords:
            if kw in text:
                return bg
    return current_bg


def guess_bgm(text, current_bgm):
    """根据文本内容猜测BGM"""
    for bgm, keywords in BGM_MAP.items():
        for kw in keywords:
            if kw in text:
                return bgm
    return current_bgm


def generate_id_prefix(day_str, event_str):
    """生成CSV ID前缀
    规则：10[Day][序号段]
    例如 Day1的第3个事件 → 1003
          Day2的第1个事件 → 1005
    """
    try:
        day_num = int(day_str)
    except ValueError:
        return "1000"

    # Day→基础偏移映射（匹配现有ID规则）
    # Day 1: 1001-1004, Day 2: 1005-1008, Day 3: 1009-1013, Day 4: 1014-1017
    # 简化：Day N 的基础前缀 = 10 + str(偏移)
    # 实际偏移需要更精细的映射，这里提供基础估算
    base = 1000
    return str(base + day_num * 5)


def parse_text_script(filepath):
    """
    解析文字剧本，返回事件列表。
    每个事件 = {header, location, time, lines: [{type, speaker, text}]}

    支持两种格式:
      A) ========== 事件：标题 ==========  //  #地点 时段
      B) Day N 事件名 ID                    //  #地点 时段
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    events = []
    current_event = None
    current_lines = []

    lines = content.split('\n')

    # 格式B的事件头模式: "Day N <event_name> <id>"
    day_event_pattern = re.compile(r'^Day\s+(\d+)\s+(.+?)\s+(\d{4,8})$')

    # 子事件头模式: "<event_name> <4-8位ID>", 且下一非空行以#开头
    sub_event_pattern = re.compile(r'^(.+?)\s+(\d{4,8})$')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        # ===== 格式A: ========== 分割 =====
        if line.startswith('==========') or line.startswith('=========='):
            if current_event:
                current_event['lines'] = current_lines
                events.append(current_event)
            stripped = line.strip('=').strip()
            if stripped.upper().startswith('END OF DAY'):
                current_event = None
                current_lines = []
                continue
            current_event = {
                'header': stripped,
                'location': '',
                'time': '',
                'lines': []
            }
            current_lines = []
            continue

        # ===== 格式B: Day N 事件名 ID =====
        day_match = day_event_pattern.match(line)
        if day_match:
            if current_event and current_lines:
                current_event['lines'] = current_lines
                events.append(current_event)
            event_name = day_match.group(2).strip()
            event_id = day_match.group(3)
            current_event = {
                'header': event_name,
                'location': '',
                'time': '',
                'event_id': event_id,
                'lines': []
            }
            current_lines = []
            continue

        # ===== 子事件头: <name> <ID> 后跟#地点 =====
        # 跳过空白查找下一行
        next_line = ''
        for j in range(i, min(i + 5, len(lines))):
            if lines[j].strip():
                next_line = lines[j].strip()
                break

        sub_match = sub_event_pattern.match(line)
        if sub_match and next_line.startswith('#'):
            # 确保这不是普通台词（检查不含中文标点分隔的关键台词模式）
            if current_event and current_lines:
                current_event['lines'] = current_lines
                events.append(current_event)
            current_event = {
                'header': sub_match.group(1).strip(),
                'location': '',
                'time': '',
                'event_id': sub_match.group(2),
                'lines': []
            }
            current_lines = []
            continue

        # ===== 分支子事件头(6-8位ID，紧接在++选择后) =====
        if sub_match and current_event is not None and not current_lines:
            current_event['header'] = sub_match.group(1).strip()
            current_event['event_id'] = sub_match.group(2)
            continue

        if current_event is None:
            continue

        # 场景标记 #地点 时段
        if line.startswith('#'):
            parts = line[1:].strip().split(None, 1)
            if parts:
                current_event['location'] = parts[0] if len(parts) > 0 else ''
                current_event['time'] = parts[1] if len(parts) > 1 else ''
            continue

        # 选择分支标记: +choice1 / +choice2
        if line.startswith('+') and not line.startswith('++'):
            current_lines.append({
                'type': 'branch_marker',
                'speaker': '',
                'text': line.lstrip('+').strip()
            })
            continue

        # 格式A分支标记
        if line.startswith('[选择分支]') or line.startswith('※ 选择') or line.startswith('※选择'):
            current_lines.append({
                'type': 'branch_marker',
                'speaker': '',
                'text': line
            })
            continue

        # 分支展开标记
        if line.startswith('++选择【') or line.startswith('++ 选择【'):
            current_lines.append({
                'type': 'branch_expand',
                'speaker': '',
                'text': line
            })
            continue

        # BE触发标记
        if 'BE触发' in line or '☠' in line:
            current_lines.append({
                'type': 'be_marker',
                'speaker': '',
                'text': line
            })
            continue

        # 分行标记
        if line.startswith('==='):
            current_lines.append({
                'type': 'divider',
                'speaker': '',
                'text': line
            })
            continue

        # Speaker 标记 【角色名】/【旁白】/【我】
        if line.startswith('【'):
            match = re.match(r'【(.+?)】\s*(.*)', line)
            if match:
                speaker_raw = match.group(1).strip()
                text_after = match.group(2).strip()
                line_type = 'dialogue' if speaker_raw != '旁白' else 'narration'
                if speaker_raw == '我':
                    speaker_raw = '黑羽哲也'  # 主角

                current_lines.append({
                    'type': line_type,
                    'speaker': speaker_raw,
                    'text': text_after
                })
                continue

        # 表演指导（括弧内）——追加到上一行
        if line.startswith('（') and '）' in line:
            if current_lines:
                current_lines[-1]['action_note'] = line.strip('（）')
            continue

        # 普通文本行（旁白延续）
        current_lines.append({
            'type': 'narration_continued',
            'speaker': '',
            'text': line
        })

    # 最后一个事件
    if current_event and current_lines:
        current_event['lines'] = current_lines
        events.append(current_event)

    return events


def convert_to_csv_rows(events, day_num):
    """
    将解析后的事件列表转换为CSV行。
    每个行是12元素的列表：
    [ID, Speaker, HeadProfile, CharLeft, CharMid, CharRight, Text, Background, BGM, Voice, Command, Note]
    """
    csv_rows = []
    current_bg = 'Club_away'
    current_bgm = 'Mixed_Emotion'

    # 生成ID
    event_counter = 0
    for event in events:
        event_counter += 1
        # ID前缀：10[day][event_counter] 如 Day3的event1 → 10090000
        id_prefix = int(f"10{day_num:02d}{event_counter:02d}")
        row_counter = 1

        last_speaker = 'hide'
        last_speaker_full = 'hide'

        for line in event['lines']:
            line_type = line['type']

            # 生成ID
            row_id = id_prefix * 100 + row_counter
            row_counter += 1

            speaker = 'hide'
            speaker_full = 'hide'
            text = ''
            command = ''
            note = ''

            if line_type == 'narration' or line_type == 'narration_continued':
                speaker = 'hide'
                speaker_full = 'hide'
                text = line['text']
                if 'action_note' in line and line['action_note']:
                    text = line['text']  # 保留原文

            elif line_type == 'dialogue':
                speaker_raw = line['speaker']
                if speaker_raw == '黑羽哲也':
                    # 主角自我对话在CSV中通常用hide
                    speaker = 'hide'
                    speaker_full = 'hide'
                else:
                    speaker_full = resolve_speaker(speaker_raw)
                    speaker = speaker_full
                text = line['text']
                if 'action_note' in line and line['action_note']:
                    note = line['action_note']

            elif line_type == 'branch_marker':
                speaker = 'hide'
                speaker_full = 'hide'
                text = line['text']
                note = '选择分支标记'

            elif line_type == 'branch_expand':
                speaker = 'hide'
                speaker_full = 'hide'
                text = line['text']
                note = '分支展开'

            elif line_type == 'be_marker':
                speaker = 'hide'
                speaker_full = 'hide'
                text = line['text']
                note = 'BE触发点'

            elif line_type == 'divider':
                # 跳过纯分隔线
                continue

            # 更新背景/BGM猜测
            new_bg = guess_background(text, current_bg)
            if new_bg != current_bg:
                current_bg = new_bg
            new_bgm = guess_bgm(text, current_bgm)
            if new_bgm != current_bgm:
                current_bgm = new_bgm

            # 更新当前说话者
            last_speaker = speaker
            last_speaker_full = speaker_full

            # HeadProfile 默认hide（需人工标注）
            head_profile = HEADPROFILE_MAP.get(speaker_full, 'hide')

            # 文本转义：CSV中如果有逗号需要引号包裹
            # 这里的处理由csv模块完成

            row = [
                str(row_id),      # ID
                speaker,          # Speaker
                head_profile,     # HeadProfile
                'hide',           # CharLeft
                'hide',           # CharMid
                'hide',           # CharRight
                text,             # Text
                current_bg,       # Background
                current_bgm,      # BGM
                '',               # Voice
                command,          # Command
                note,             # Note
            ]
            csv_rows.append(row)

            # 表演指导处理后重置
            if 'action_note' in line:
                del line['action_note']

    return csv_rows


def write_csv(csv_rows, output_path, script_name=""):
    """写入CSV文件，保持与现有格式完全一致"""
    header = ['ID', 'Speaker', 'HeadProfile', 'CharLeft', 'CharMid', 'CharRight',
              'Text', 'Background', 'BGM', 'Voice', 'Command', 'Note']

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in csv_rows:
            writer.writerow(row)

    print(f"  ✅ 已生成：{output_path}  ({len(csv_rows)} 行)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("用法：python txt_to_csv.py <文字剧本.txt> [输出目录]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(input_path)

    if not os.path.exists(input_path):
        print(f"❌ 文件不存在：{input_path}")
        sys.exit(1)

    # 从文件名推断 Day 编号
    basename = os.path.splitext(os.path.basename(input_path))[0]
    day_match = re.search(r'Day\s*(\d+)', basename)
    day_num = int(day_match.group(1)) if day_match else 0

    print(f"\n📖 解析文字剧本：{input_path}")
    print(f"   Day 编号：{day_num}")

    events = parse_text_script(input_path)
    print(f"   解析到 {len(events)} 个事件")

    if not events:
        print("   ⚠ 未解析到任何事件，请检查剧本格式")
        return

    # 输出每个事件的摘要
    for i, event in enumerate(events):
        # 统计台词行数
        dialogue_count = sum(1 for l in event['lines'] if l['type'] == 'dialogue')
        narration_count = sum(1 for l in event['lines'] if l['type'] in ('narration', 'narration_continued'))
        speakers = set(l['speaker'] for l in event['lines'] if l['speaker'] and l['speaker'] != '黑羽哲也')
        print(f"   事件{i+1}: {event['header'][:40]:40s} "
              f"旁白{narration_count}行 对话{dialogue_count}行 "
              f"角色:{', '.join(list(speakers)[:3]) if speakers else '无'}")

    # 转换为CSV
    print(f"\n🔄 转换为CSV格式...")
    csv_rows = convert_to_csv_rows(events, day_num)

    # 写入CSV
    os.makedirs(output_dir, exist_ok=True)

    # 按事件分割写入多个CSV文件
    if events:
        # 先写出一个合并的完整文件
        full_output = os.path.join(output_dir, f"{basename}_full.csv")
        write_csv(csv_rows, full_output, f"Day{day_num}完整合并")

    # 同时按事件分别写出（推荐用法）
    event_idx = 0
    for event in events:
        event_idx += 1
        # 统计该事件的行数
        event_id_prefix = int(f"10{day_num:02d}{event_idx:02d}")
        event_rows = [r for r in csv_rows if r[0].startswith(str(event_id_prefix))]

        if event_rows:
            # 生成事件文件名（从header提取）
            safe_name = event['header'].replace('/', '_').replace(' ', '_')[:30]
            event_output = os.path.join(output_dir, f"Day_{day_num}_{safe_name}.csv")
            write_csv(event_rows, event_output, event['header'])

    print(f"\n📋 转换完成！")
    print(f"   ⚠ 重要提醒：以下字段需要人工标注：")
    print(f"     - HeadProfile（角色立绘ID）")
    print(f"     - CharLeft / CharMid / CharRight（立绘位置）")
    print(f"     - Background / BGM（已自动猜测，需确认）")
    print(f"     - Voice（语音指令）")
    print(f"     - Command（特殊指令：loadScript, choice, AddS_Char 等）")
    print(f"     - Note（备注）")


if __name__ == '__main__':
    main()
