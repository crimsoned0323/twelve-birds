#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「十二飞鸟」伏笔追踪数据库
==========================
追踪剧本中的"约定→兑现"伏笔链，支持：
  - 自动扫描已有剧本发现伏笔（约定/承诺/暗示）
  - 检查伏笔是否兑现
  - 生成伏笔状态报告
  - 交互式查询

用法：
    python foreshadow_tracker.py scan <剧本目录>              # 扫描目录下所有剧本
    python foreshadow_tracker.py check <Day编号>              # 检查指定Day的伏笔兑现
    python foreshadow_tracker.py report                       # 生成全剧伏笔报告
    python foreshadow_tracker.py add <描述> <约定日> <兑现日>  # 手动添加伏笔
    python foreshadow_tracker.py query <关键词>               # 查询伏笔

数据文件：foreshadow_db.json（自动创建在tools目录下）
"""

import io
import json
import os
import re
import sys
from datetime import datetime

# Windows GBK → UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 配置
# ============================================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foreshadow_db.json')

# 伏笔触发模式（正则）
FORESHADOW_PATTERNS = {
    'promise': [
        # 约定类
        (r'明(?:天|早|晚|日)(?:我[们]|[你我他她])?(?:去|来|到|在|给|带|买|吃|喝|见|找|做|帮忙|陪)\s*(.+?)(?:[。，\n]|$)', '约定'),
        (r'(?:下次|下次见面|下一次|之后|到时候)(?:我[们]|[你我他她])?(?:去|来|到|在|给|带|买|吃|喝|见|找|做)\s*(.+?)(?:[。，\n]|$)', '约定'),
        (r'(?:等|等到|等会儿|回头)(?:我[们]|[你我他她])?(?:去|来|到|给|带|买|吃|见|找|做)\s*(.+?)(?:[。，\n]|$)', '约定'),
        (r'(?:别忘了|别忘了哦|记得|一定要|千万不要忘记)\s*(.+?)(?:[。，\n]|$)', '提醒'),
        (r'我答应[你我他她]?\s*(.+?)(?:[。，\n]|$)', '承诺'),
    ],
    'clue': [
        # 线索/暗示类
        (r'(?:疑[似惑问]|不对[劲头]|奇怪|古怪|不寻常)\s*(.+?)(?:[。，\n]|$)', '疑点'),
        (r'(?:似乎|好像|仿佛|隐约|隐隐)(?:有|是|在|能|看见|听见|闻到|感觉)\s*(.+?)(?:[。，\n]|$)', '暗示'),
        (r'(?:留下|留着|保留|保存)(?:了)?\s*(.+?)(?:[。，\n]|$)', '遗留物'),
    ],
    'reveal': [
        # 揭示/真相类
        (r'(?:原来|其实|真相是|真正[的原]因是|秘密是)\s*(.+?)(?:[。，\n]|$)', '揭示'),
    ],
}

# 已知的伏笔清单（手动登记）
KNOWN_FORESHADOWS = [
    {"id": "FS001", "description": "草莓布丁——早莺姬回忆男友以前的好", "setup_day": 5, "payoff_day": 14, "status": "done"},
    {"id": "FS002", "description": "加蛋——拉面店育子点单习惯", "setup_day": 4, "payoff_day": 9, "status": "done"},
    {"id": "FS003", "description": "增田的烧酒——增田在拉面店的习惯", "setup_day": 1, "payoff_day": 8, "status": "done"},
    {"id": "FS004", "description": "墙纸鼓起——公寓壁纸意象贯穿", "setup_day": 5, "payoff_day": 6, "status": "done"},
    {"id": "FS005", "description": "E-04药瓶——青鹭姬自制药物", "setup_day": 7, "payoff_day": 15, "status": "setup"},
    {"id": "FS006", "description": "黑皮书——夜鸢姬的情报库", "setup_day": 8, "payoff_day": 42, "status": "ongoing"},
    {"id": "FS007", "description": "Phoenix Coin——银鹮姬引荐的虚拟货币", "setup_day": 3, "payoff_day": 30, "status": "ongoing"},
    {"id": "FS008", "description": "绳索理论——白鹤姬的核心哲学", "setup_day": 10, "payoff_day": 13, "status": "done"},
    {"id": "FS009", "description": "佐藤5天倒计时", "setup_day": 15, "payoff_day": 20, "status": "setup"},
    {"id": "FS010", "description": "莉香要买床垫", "setup_day": 4, "payoff_day": 4, "status": "done"},
    {"id": "FS011", "description": "育子想吃味噌拉面加味玉", "setup_day": 4, "payoff_day": 5, "status": "done"},
    {"id": "FS012", "description": "增田有重要情报当面给", "setup_day": 7, "payoff_day": 8, "status": "done"},
    {"id": "FS013", "description": "青鹭姬的杀意宣言", "setup_day": 15, "payoff_day": 34, "status": "ongoing"},
    {"id": "FS014", "description": "莉香想回来看主角", "setup_day": 18, "payoff_day": 42, "status": "ongoing"},
    {"id": "FS015", "description": "神鸦姬预言「背叛者就在身边」", "setup_day": 20, "payoff_day": 30, "status": "setup"},
]

# 伏笔状态颜色
STATUS_COLORS = {
    "done": "✅",
    "setup": "⏳",
    "ongoing": "🔄",
    "broken": "❌",
    "unknown": "❓",
}


def load_db():
    """加载伏笔数据库"""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"foreshadows": KNOWN_FORESHADOWS, "last_updated": "", "scan_results": []}


def save_db(db):
    """保存伏笔数据库"""
    db["last_updated"] = datetime.now().isoformat()
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def scan_text(text, day_num):
    """扫描文本中的伏笔"""
    found = []
    for category, patterns in FORESHADOW_PATTERNS.items():
        for pattern, label in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and len(match) < 80:  # 过滤太短/太长的
                    found.append({
                        "category": category,
                        "label": label,
                        "content": match.strip(),
                        "day": day_num,
                    })
    return found


def scan_directory(directory):
    """扫描目录下所有剧本文件"""
    db = load_db()
    all_found = []

    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue

        # 提取Day编号
        day_match = re.search(r'Day\s*(\d+)', filename)
        if not day_match:
            continue
        day_num = int(day_match.group(1))

        _, ext = os.path.splitext(filename)

        try:
            if ext == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                found = scan_text(text, day_num)
                for f_item in found:
                    f_item['source'] = filename
                all_found.extend(found)
                if found:
                    print(f"  Day {day_num:2d}  {filename[:50]:50s}  发现 {len(found)} 处伏笔")
            elif ext == '.csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                found = scan_text(text, day_num)
                for f_item in found:
                    f_item['source'] = filename
                all_found.extend(found)
        except Exception as e:
            print(f"  ⚠ 读取失败 {filename}: {e}")

    db['scan_results'] = all_found
    save_db(db)
    print(f"\n📊 总计发现 {len(all_found)} 处潜在伏笔")
    return all_found


def check_payoffs(day_num):
    """检查指定Day是否有需要兑现的伏笔"""
    db = load_db()
    foreshadows = db.get('foreshadows', KNOWN_FORESHADOWS)

    # 应该在当天或之前兑现的伏笔
    due = [f for f in foreshadows if f.get('payoff_day', 999) <= day_num]

    print(f"\n📋 Day {day_num} 伏笔兑现检查")
    print(f"{'─'*60}")
    print(f"  应兑现的伏笔 ({len(due)}):")

    pending = []
    for f in due:
        status = f.get('status', 'unknown')
        icon = STATUS_COLORS.get(status, '❓')
        print(f"  {icon} {f['id']}: {f['description'][:55]}")
        print(f"     约定日Day{f['setup_day']} → 兑现日Day{f.get('payoff_day', '?')}  状态:{status}")
        if status not in ('done',):
            pending.append(f)

    if pending:
        print(f"\n  ⚠ {len(pending)} 个伏笔尚未标记为完成：")
        for f in pending:
            print(f"    - {f['id']}: {f['description']}")

    # 检查Day当天设置的伏笔
    setups = [f for f in foreshadows if f.get('setup_day') == day_num]
    if setups:
        print(f"\n  本日新设伏笔 ({len(setups)}):")
        for f in setups:
            print(f"    ⏳ {f['id']}: {f['description']}")
            print(f"      预计兑现日：Day{f.get('payoff_day', '?')}")

    return due, pending


def add_foreshadow(description, setup_day, payoff_day):
    """手动添加伏笔"""
    db = load_db()
    foreshadows = db.get('foreshadows', [])
    new_id = f"FS{len(foreshadows) + 1:03d}"

    new_fs = {
        "id": new_id,
        "description": description,
        "setup_day": int(setup_day),
        "payoff_day": int(payoff_day) if payoff_day else None,
        "status": "setup",
        "created": datetime.now().isoformat(),
    }
    foreshadows.append(new_fs)
    db['foreshadows'] = foreshadows
    save_db(db)
    print(f"✅ 已添加伏笔 {new_id}: {description}")
    print(f"   约定 Day{setup_day} → 兑现 Day{payoff_day or '待定'}")


def generate_report():
    """生成全剧伏笔状态报告"""
    db = load_db()
    foreshadows = db.get('foreshadows', KNOWN_FORESHADOWS)

    # 按状态分组
    done = [f for f in foreshadows if f.get('status') == 'done']
    ongoing = [f for f in foreshadows if f.get('status') == 'ongoing']
    setup = [f for f in foreshadows if f.get('status') == 'setup']
    broken = [f for f in foreshadows if f.get('status') == 'broken']
    unknown = [f for f in foreshadows if f.get('status', 'unknown') == 'unknown']

    report_lines = []
    report_lines.append("「十二飞鸟」伏笔追踪报告")
    report_lines.append("=" * 70)
    report_lines.append(f"更新时间：{db.get('last_updated', '未知')}")
    report_lines.append(f"总伏笔数：{len(foreshadows)}")
    report_lines.append(f"  ✅ 已兑现：{len(done)}")
    report_lines.append(f"  ⏳ 待兑现：{len(setup)}")
    report_lines.append(f"  🔄 进行中：{len(ongoing)}")
    report_lines.append(f"  ❌ 断裂：{len(broken)}")
    report_lines.append("")

    # 时间线视图
    report_lines.append(f"{'─'*70}")
    report_lines.append("  时间线视图")
    report_lines.append(f"{'─'*70}")

    all_days = set()
    for f in foreshadows:
        all_days.add(f.get('setup_day', 0))
        payoff = f.get('payoff_day')
        if payoff:
            all_days.add(payoff)

    for day in sorted(all_days):
        if day == 0:
            continue
        day_setups = [f for f in foreshadows if f.get('setup_day') == day]
        day_payoffs = [f for f in foreshadows if f.get('payoff_day') == day]

        if day_setups or day_payoffs:
            report_lines.append(f"  Day {day:2d}:")
            for f in day_payoffs:
                icon = STATUS_COLORS.get(f.get('status', 'unknown'), '❓')
                report_lines.append(f"         ↙ {icon} 兑现: {f['description'][:50]}")
            for f in day_setups:
                icon = STATUS_COLORS.get(f.get('status', 'unknown'), '❓')
                report_lines.append(f"         ↘ {icon} 约定: {f['description'][:50]}")
            report_lines.append("")

    # 未兑现列表
    if setup or ongoing:
        report_lines.append(f"{'─'*70}")
        report_lines.append("  待兑现/进行中的伏笔")
        report_lines.append(f"{'─'*70}")
        for f in setup + ongoing:
            payoff = f"Day{f.get('payoff_day', '?')}" if f.get('payoff_day') else "待定"
            report_lines.append(f"  {STATUS_COLORS.get(f['status'], '❓')} {f['id']}: {f['description']}")
            report_lines.append(f"     Day{f['setup_day']} → {payoff}")
        report_lines.append("")

    return '\n'.join(report_lines)


def query_foreshadow(keyword):
    """查询伏笔"""
    db = load_db()
    foreshadows = db.get('foreshadows', KNOWN_FORESHADOWS)

    results = [f for f in foreshadows if keyword.lower() in f['description'].lower() or keyword.lower() in f.get('id', '').lower()]

    if not results:
        print(f"未找到包含「{keyword}」的伏笔")
        return

    print(f"\n🔍 搜索「{keyword}」— 找到 {len(results)} 条：")
    for f in results:
        icon = STATUS_COLORS.get(f.get('status', 'unknown'), '❓')
        print(f"  {icon} {f['id']}: {f['description']}")
        print(f"     约定Day{f['setup_day']} → 兑现Day{f.get('payoff_day', '?')}  状态:{f.get('status', '?')}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("用法：")
        print("  python foreshadow_tracker.py scan <剧本目录>")
        print("  python foreshadow_tracker.py check <Day编号>")
        print("  python foreshadow_tracker.py report")
        print("  python foreshadow_tracker.py add <描述> <约定日> <兑现日>")
        print("  python foreshadow_tracker.py query <关键词>")
        return

    command = sys.argv[1]

    if command == 'scan':
        directory = sys.argv[2] if len(sys.argv) > 2 else '.'
        if not os.path.isdir(directory):
            print(f"❌ 无效目录：{directory}")
            return
        print(f"📂 扫描目录：{directory}")
        scan_directory(directory)

    elif command == 'check':
        if len(sys.argv) < 3:
            print("❌ 请指定Day编号")
            return
        check_payoffs(int(sys.argv[2]))

    elif command == 'report':
        report = generate_report()
        print(report)
        # 同时保存到文件
        report_path = os.path.join(os.path.dirname(DB_PATH), '伏笔追踪报告.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 报告已保存：{report_path}")

    elif command == 'add':
        if len(sys.argv) < 5:
            print("❌ 用法：python foreshadow_tracker.py add <描述> <约定日> <兑现日>")
            return
        description = sys.argv[2]
        setup_day = sys.argv[3]
        payoff_day = sys.argv[4] if sys.argv[4] != '-' else None
        add_foreshadow(description, setup_day, payoff_day)

    elif command == 'query':
        if len(sys.argv) < 3:
            print("❌ 请指定查询关键词")
            return
        query_foreshadow(sys.argv[2])

    else:
        print(f"❌ 未知命令：{command}")
        print("支持的命令：scan, check, report, add, query")


if __name__ == '__main__':
    main()
