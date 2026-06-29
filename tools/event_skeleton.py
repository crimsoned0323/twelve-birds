#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「十二飞鸟」事件骨架生成器
==========================
根据60天规划文档，为指定天数生成创作骨架模板。
骨架包含：事件名、地点、时段、出场角色、叙事目标、感官提示、红线避让、好感度编号。

用法：
    python event_skeleton.py <Day编号> [--plan <规划文件>] [--output <输出目录>]

示例：
    python event_skeleton.py 20                                    # 生成Day 20的骨架
    python event_skeleton.py 20 --plan ../设定文档/剧本规划_60天完整版.txt
    python event_skeleton.py 5-10                                  # 生成Day 5~10
    python event_skeleton.py 1-60 --output ../骨架/               # 生成全部60天
    python event_skeleton.py overview                               # 输出全剧概览
"""

import io
import os
import re
import sys

# Windows GBK → UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 角色全名映射
# ============================================================
CHAR_NAME_MAP = {
    "白鹤姬": "白鹤姬·桂原雪代",
    "雪代":   "白鹤姬·桂原雪代",
    "早莺姬": "早莺姬·小野南梨",
    "南梨":   "早莺姬·小野南梨",
    "巢燕姬": "巢燕姬·谷川景子",
    "景子":   "巢燕姬·谷川景子",
    "青鹭姬": "青鹭姬·星野葵",
    "葵":     "青鹭姬·星野葵",
    "黄鹂姬": "黄鹂姬·日向夏实",
    "夏实":   "黄鹂姬·日向夏实",
    "神鸦姬": "神鸦姬·神乐坂紫",
    "紫":     "神鸦姬·神乐坂紫",
    "朱雀姬": "朱雀姬·Linda",
    "Linda":  "朱雀姬·Linda",
    "夜鸢姬": "夜鸢姬·美咲蔷薇",
    "蔷薇":   "夜鸢姬·美咲蔷薇",
    "双雀姬": "双雀姬·濑户彩&瞳",
    "雏鹃姬": "雏鹃姬·芦田育子",
    "育子":   "雏鹃姬·芦田育子",
    "银鹮姬": "银鹮姬·神宫寺丽莎",
    "丽莎":   "银鹮姬·神宫寺丽莎",
    "诡鹀姬": "诡鹀姬·木岛春奈",
    "春奈":   "诡鹀姬·木岛春奈",
    "莉香":   "小林莉香",
}

# 角色红线速查
CHAR_REDLINES = {
    "白鹤姬": "禁止Day1~15表露真情实感；每句话经过衡量；魅惑异能可感知他人",
    "早莺姬": "男友癌症末期，坚信他会变好；淤青是偶尔的；禁止在男友死前彻底觉醒",
    "巢燕姬": "女儿叫小澪(4-5岁)；从不为女儿的事隐瞒动机",
    "青鹭姬": "京都医科大学高材生；为雪鹤姬复仇；禁止情绪化(愤怒/哭泣/失控)",
    "黄鹂姬": "雪鹤姬自杀第一发现人；笑容是面具；非独处禁止卸下笑容",
    "神鸦姬": "第一次占卜准，第二次开始必定错误；柏青哥成瘾；父母双亡",
    "朱雀姬": "俄罗斯人；Interpol搜查官；Day25前禁止暴露身份；享受卧底",
    "夜鸢姬": "SM女王；黑皮书情报库；Day32前禁止免费给重要情报；要价越来越高",
    "双雀姬": "马戏团出身；瞳Day16前几乎不开口；主动来俱乐部；禁止拆散姐妹",
    "雏鹃姬": "16岁被骗来；妈不知退学；脚尖内八；Day15前禁止自信成熟",
    "银鹮姬": "前投行女公关；Phoenix Coin引荐者；欠地下钱庄；禁止直接交易毒品",
    "诡鹀姬": "模仿仿妆能力；Day41前禁止露素颜；内心善良；禁止失去顽皮底色",
    "小林莉香": "澳洲留学；Day42前禁止出现在日本",
}

# POV时段速查
TIME_PERIODS = ["清晨", "上午", "下午", "傍晚", "深夜"]

# 时段典型事件类型
PERIOD_TYPICAL = {
    "清晨": "醒来、汇报、电话、独白、回忆、拉面店、公寓",
    "上午": "外出、整理资料、佐藤联络、街头观察",
    "下午": "商店街、咖啡馆、医院探病、偶遇",
    "傍晚": "俱乐部准备、化妆间、办公室、天台、新人/事件",
    "深夜": "俱乐部营业、走廊偶遇、VIP室、浴室、深夜对话",
}


def parse_planning_doc(filepath):
    """解析60天规划文档，提取每天的事件列表"""
    if not os.path.exists(filepath):
        print(f"⚠ 规划文件不存在：{filepath}，使用内置精简版")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    days = {}
    current_day = None
    current_events = []

    lines = content.split('\n')
    day_pattern = re.compile(r'^Day\s+(\d+)\s+')
    event_pattern = re.compile(r'(清晨|上午|下午|傍晚|深夜)\s+(\d+)\s+([★◆◎☠]+)\s+(.+)')

    for line in lines:
        day_match = day_pattern.match(line.strip())
        if day_match:
            # 保存前一天的数据
            if current_day and current_events:
                days[current_day] = current_events
            current_day = int(day_match.group(1))
            current_events = []
            continue

        if current_day is None:
            continue

        event_match = event_pattern.match(line.strip())
        if event_match:
            time_period = event_match.group(1)
            event_num = event_match.group(2)
            markers = event_match.group(3)
            description = event_match.group(4)

            # 解析标记含义
            is_key = '◆' in markers      # 关键剧情
            is_favor = '★' in markers    # 好感度事件
            is_transition = '◎' in markers  # 过渡事件
            has_be = '☠' in markers      # BE触发点

            event = {
                'day': current_day,
                'period': time_period,
                'num': event_num,
                'description': description.strip(),
                'is_key': is_key,
                'is_favor': is_favor,
                'is_transition': is_transition,
                'has_be': has_be,
            }
            current_events.append(event)

    if current_day and current_events:
        days[current_day] = current_events

    return days


def extract_characters(description):
    """从事件描述中提取角色名"""
    chars = []
    for name in CHAR_NAME_MAP:
        if name in description:
            full = CHAR_NAME_MAP[name]
            if full not in chars:
                chars.append(full)
    return chars


def guess_location(event):
    """根据事件描述和时段猜测地点"""
    desc = event['description']
    period = event['period']

    location_keywords = {
        "公寓": ["公寓", "醒来", "租住", "起床", "房间"],
        "拉面店": ["拉面", "老板", "味噌"],
        "俱乐部_走廊": ["走廊", "偶遇", "走过"],
        "俱乐部_办公室": ["办公室", "报表", "汇报", "整理"],
        "俱乐部_化妆间": ["化妆", "换衣", "准备"],
        "俱乐部_天台": ["天台", "屋顶"],
        "俱乐部_休息室": ["休息室", "休息"],
        "俱乐部_VIP": ["VIP", "包厢", "客人"],
        "俱乐部_大厅": ["大厅", "前台", "营业"],
        "商店街": ["商店街", "购物", "逛街", "寝具"],
        "咖啡馆": ["咖啡", "茶"],
        "医院": ["医院", "病房", "探病", "化疗"],
        "户外": ["外出", "街头", "大阪"],
        "电话": ["电话", "视频", "消息", "LINE", "来电"],
    }

    for loc, keywords in location_keywords.items():
        for kw in keywords:
            if kw in desc:
                return loc

    # 默认根据时段
    period_loc = {
        "清晨": "公寓",
        "上午": "公寓",
        "下午": "俱乐部_走廊",
        "傍晚": "俱乐部_办公室",
        "深夜": "俱乐部_走廊",
    }
    return period_loc.get(period, "俱乐部")


def generate_skeleton(day_num, events):
    """为指定天数生成创作骨架"""
    lines = []
    lines.append(f"Day {day_num}：创作骨架")
    lines.append("=" * 70)

    for event in events:
        event_type = []
        if event['is_key']:
            event_type.append("🔑关键")
        if event['is_favor']:
            event_type.append("⭐好感度")
        if event['is_transition']:
            event_type.append("↪过渡")
        if event['has_be']:
            event_type.append("☠BE触发")

        type_str = " ".join(event_type)
        chars = extract_characters(event['description'])
        chars_str = "、".join(chars) if chars else "(无角色标记)"
        location = guess_location(event)

        lines.append(f"""
{"─" * 70}
  事件#{event['num']}  {event['period']}  {type_str}
  描述：{event['description']}
  地点：{location}
  出场角色：{chars_str}
""")

        # 红线提醒
        for char_name in chars:
            short = char_name.split('·')[0] if '·' in char_name else char_name
            if short in CHAR_REDLINES:
                lines.append(f"  ⚡红线({short})：{CHAR_REDLINES[short]}")

        # 创作提示
        if event['is_favor']:
            lines.append(f"  💡提示：这是好感度事件，确保角色展现新的面向或加深羁绊")
        if event['is_key']:
            lines.append(f"  💡提示：关键剧情事件，需包含一个令人难忘的画面或揭示")
        if event['has_be']:
            lines.append(f"  💡提示：此处为BE触发窗口开启点，规划分支文本")
        if event['is_transition']:
            lines.append(f"  💡提示：过渡事件，3~5行旁白 + 1句对话即可，不必展开")

        lines.append(f"""
========== 事件：{event['description'][:30]} ==========
# {location} {event['period']}

【旁白】
（在此建立场景氛围——气味/光线/声音优先）

【{chars[0] if chars else '？？？'}】
（角色台词，注意语气和红线）

【我】
（主角台词≤15字）

（继续发展……）
""")

    lines.append("─" * 70)
    lines.append(f"  Day {day_num} 骨架结束  —  共 {len(events)} 个事件")
    lines.append("=" * 70)
    return '\n'.join(lines)


def generate_overview(days_data):
    """生成全剧概览"""
    lines = []
    lines.append("「十二飞鸟」全剧60天概览")
    lines.append("=" * 70)
    lines.append(f"{'Day':<5} {'事件数':<7} {'关键':<5} {'好感':<5} {'BE':<5} {'过渡':<5} 概要")
    lines.append("-" * 70)

    total_events = 0
    total_key = 0
    total_favor = 0
    total_be = 0
    total_transition = 0

    for day in sorted(days_data.keys()):
        events = days_data[day]
        key_count = sum(1 for e in events if e['is_key'])
        favor_count = sum(1 for e in events if e['is_favor'])
        be_count = sum(1 for e in events if e['has_be'])
        transition_count = sum(1 for e in events if e['is_transition'])

        # 第一个事件描述
        first_desc = events[0]['description'][:40] if events else ""

        lines.append(f"{day:<5} {len(events):<7} {key_count:<5} {favor_count:<5} {be_count:<5} {transition_count:<5} {first_desc}")

        total_events += len(events)
        total_key += key_count
        total_favor += favor_count
        total_be += be_count
        total_transition += transition_count

    lines.append("-" * 70)
    lines.append(f"总计  {total_events:<7} {total_key:<5} {total_favor:<5} {total_be:<5} {total_transition:<5}")
    lines.append("=" * 70)

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("用法：python event_skeleton.py <Day编号> [--plan <规划文件>] [--output <输出目录>]")
        return

    day_arg = sys.argv[1]
    plan_path = None
    output_dir = None

    for i, arg in enumerate(sys.argv):
        if arg == '--plan' and i + 1 < len(sys.argv):
            plan_path = sys.argv[i + 1]
        if arg == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]

    # 默认规划文件路径
    if plan_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_plan = os.path.join(script_dir, '..', '设定文档', '剧本规划_60天完整版.txt')
        if os.path.exists(default_plan):
            plan_path = default_plan

    # 解析规划
    print(f"📖 解析规划文档：{plan_path}")
    days_data = parse_planning_doc(plan_path)
    print(f"   解析到 {len(days_data)} 天的规划数据")

    # 概览模式
    if day_arg.lower() == 'overview':
        overview = generate_overview(days_data)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(output_dir, "全剧概览.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(overview)
            print(f"✅ 概览已保存：{out_path}")
        else:
            print(overview)
        return

    # 解析Day范围
    day_range = None
    if '-' in day_arg:
        parts = day_arg.split('-')
        day_range = range(int(parts[0]), int(parts[1]) + 1)
    else:
        try:
            day_num = int(day_arg)
            day_range = [day_num]
        except ValueError:
            print(f"❌ 无效的Day编号：{day_arg}")
            return

    # 生成骨架
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for day_num in day_range:
        if day_num not in days_data:
            print(f"⚠ Day {day_num} 不在规划中，跳过")
            continue

        events = days_data[day_num]
        skeleton = generate_skeleton(day_num, events)

        if output_dir:
            out_path = os.path.join(output_dir, f"Day{day_num}_骨架.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(skeleton)
            print(f"✅ 已生成：{out_path}")
        else:
            print(skeleton)

    print(f"\n📋 共生成 {len([d for d in day_range if d in days_data])} 天的骨架模板")


if __name__ == '__main__':
    main()
