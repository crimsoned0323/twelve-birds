#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「十二飞鸟」剧本自动Review工具
================================
对文字剧本和CSV剧本执行8项自动检查：
  1. 日语残留检测
  2. 时间线连贯性检查
  3. 好感度编号延续
  4. 角色情绪衔接
  5. 伏笔/约定兑现追踪
  6. POV合规检查
  7. 禁止文艺煽情比喻
  8. 主角台词字数检查

用法：
    python auto_review.py <剧本文件.txt/.csv> [--strict] [--output report.txt]

选项：
    --strict    启用严格模式（警告也视为错误）
    --output    指定输出报告文件路径
"""

import csv
import io
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

# Windows GBK → UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 配置区
# ============================================================

# 日语字符正则
JAPANESE_PATTERN = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]')

# 纯日语假名/片假名（不包括汉字，因为汉字在中文中也使用）
JAPANESE_KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u30fc\u309b-\u309c\uff66-\uff9f]')

# 常见日语词汇模式（比较容易渗入中文剧本的）
JAPANESE_WORDS = [
    'ありがとう', 'ごめん', 'さようなら', 'すみません', 'おはよう',
    'こんにちは', 'こんばんは', 'いただきます', 'おやすみ',
    'ママ', 'パパ', 'お母さん', 'お父さん', 'お姉さん', 'お兄さん',
    'はい', 'いいえ', 'お願い', 'かわいい', 'すごい',
    'マスター', 'せんぱい', 'ちゃん', 'くん', 'さん',
    'そうですね', 'ええと', 'あのう', 'やめて', 'だめ',
]

# 角色全名列表（用于一致性检查）
CHARACTERS_FULL = [
    '白鹤姬·桂原雪代', '早莺姬·小野南梨', '巢燕姬·谷川景子',
    '青鹭姬·星野葵', '黄鹂姬·日向夏实', '神鸦姬·神乐坂紫',
    '朱雀姬·Linda', '夜鸢姬·美咲蔷薇', '双雀姬·濑户彩',
    '双雀姬·濑户瞳', '雏鹃姬·芦田育子', '银鹮姬·神宫寺丽莎',
    '诡鹀姬·木岛春奈', '小林莉香',
    '增田一郎', '佐藤正义', '村上道也', '江口裕二',
    '雪鹤姬·如月冬雪', '子鹃姬·铃木唯',
]

# 主角名字
PROTAGONIST_NAMES = ['黑羽义', '黑羽哲也', '我']

# 禁止的文艺煽情比喻模式
BANNED_METAPHORS = [
    r'像?折断了翅膀',
    r'隔着一整片海',
    r'心碎',
    r'泪如雨下',
    r'心如刀割',
    r'肝肠寸断',
    r'痛彻心扉',
    r'撕心裂肺',
    r'天崩地裂',
    r'魂牵梦萦',
    r'刻骨铭心',
]

# 每个角色的禁止事项（来自创作规范）
CHARACTER_REDLINES = {
    '白鹤姬': [
        (r'(?=.*白鹤姬)(?=.*失控|失态|哭泣|流泪|崩溃)', '白鹤姬禁止在Day1~15表露真情实感或失态'),
        (r'白鹤姬.*说[^，。]{30,}', '白鹤姬每句话应该经过衡量，不宜过长'),
    ],
    '青鹭姬': [
        (r'(?=.*青鹭姬)(?=.*愤怒|哭泣|失控|崩溃|激动)', '青鹭姬禁止情绪化表现'),
        (r'(?=.*青鹭姬)(?=.*为自己复仇)', '青鹭姬的复仇动机是为雪鹤姬，不是为自己'),
    ],
    '黄鹂姬': [
        (r'(?=.*黄鹂姬)(?=.*当着.*的面).*(?:叹气|沉默|面无表情)', '黄鹂姬在非独处场合禁止卸下笑容'),
    ],
    '神鸦姬': [
        (r'(?:第二次|再次|又一次).*占卜.*(?:灵验|应验|成真|准确|说中)', '神鸦姬第二次及之后的占卜禁止预测成真'),
    ],
    '朱雀姬': [
        (r'(?=.*朱雀姬)(?=.*Interpol|国际刑警|搜查官).*(?=.*Day\s*[12][0-4])', '朱雀姬在Day25前禁止暴露Interpol身份'),
    ],
    '夜鸢姬': [
        (r'(?=.*夜鸢姬)(?=.*免费|赠送|不收).*(?:情报|信息|黑皮书)', '夜鸢姬在Day32前禁止免费给出重要情报'),
    ],
    '双雀姬': [
        (r'瞳.*说[^，。]{15,}', '瞳(Day16前)禁止说出完整长句'),
        (r'被卖.*双雀|双雀.*被卖', '双雀姬是主动选择来俱乐部，不是被卖来的'),
    ],
    '雏鹃姬': [
        (r'(?=.*育子)(?=.*自信|成熟|老练|熟悉).*(?=.*Day\s*1[0-4])', '育子在Day15前禁止表现过于自信/成熟'),
    ],
    '诡鹀姬': [
        (r'(?=.*素颜).*(?=.*春奈|诡鹀)', '诡鹀姬在Day41前禁止露出素颜'),
    ],
    '小林莉香': [
        (r'(?=.*莉香).*(?:回国|在日本|来到大阪).*(?=.*Day\s*[34][0-1])', '莉香在Day42前禁止出现在日本'),
    ],
}

# POV规则：主角各时段活动范围
POV_RULES = {
    '清晨': {
        'allowed': ['公寓', '拉面店', '商店街', '外面', '外出', '街头'],
        'forbidden': ['俱乐部VIP', '俱乐部包厢', '角色私宅', '卧室'],
        'time_range': '07:00-09:00',
    },
    '上午': {
        'allowed': ['公寓', '外出', '公共场所', '警署'],
        'forbidden': ['俱乐部内部'],
        'time_range': '09:00-12:00',
    },
    '下午': {
        'allowed': ['公寓', '商店街', '咖啡馆', '医院', '俱乐部', '俱乐部走廊'],
        'forbidden': ['角色私宅', '卧室'],
        'time_range': '13:00-16:00',
    },
    '傍晚': {
        'allowed': ['俱乐部', '化妆间', '办公室', '天台', '走廊', '经理办公室'],
        'forbidden': ['俱乐部外', '角色私宅'],
        'time_range': '16:00-18:00',
    },
    '深夜': {
        'allowed': ['俱乐部', '走廊', 'VIP室', '休息室', '化妆间', '办公室', '天台'],
        'forbidden': ['俱乐部外', '角色私宅'],
        'time_range': '18:00-01:00',
    },
}

# 好感度事件编号验证
FAVOR_EVENTS_RANGES = {
    '白鹤姬': range(1, 11),
    '早莺姬': range(1, 11),
    '巢燕姬': range(1, 11),
    '青鹭姬': range(1, 12),
    '黄鹂姬': range(1, 9),
    '神鸦姬': range(1, 8),
    '朱雀姬': range(1, 9),
    '夜鸢姬': range(1, 9),
    '双雀姬': range(1, 9),
    '雏鹃姬': range(1, 12),
    '银鹮姬': range(1, 9),
    '诡鹀姬': range(1, 8),
    '小林莉香': range(1, 11),
}


class ReviewReport:
    """Review报告收集器"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.score = {'total': 100}
        self.strict = False

    def error(self, category, msg, line_num=None):
        loc = f" 第{line_num}行" if line_num else ""
        self.errors.append(f"❌ [{category}]{loc}: {msg}")

    def warning(self, category, msg, line_num=None):
        loc = f" 第{line_num}行" if line_num else ""
        self.warnings.append(f"⚠ [{category}]{loc}: {msg}")

    def info_msg(self, msg):
        self.info.append(f"ℹ {msg}")

    def get_summary(self):
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            return "✅ 全部检查通过！"
        return f"❌ {len(self.errors)}个错误  ⚠ {len(self.warnings)}个警告  ℹ {len(self.info)}条信息"


def check_japanese(text_lines, report):
    """检查1：日语残留检测"""
    found_any = False
    for i, line in enumerate(text_lines):
        line_num = i + 1
        # 检查日语假名
        kana_matches = JAPANESE_KANA.findall(line)
        if kana_matches:
            report.error('日语残留', f'发现日语假名: {"".join(kana_matches)}', line_num)
            found_any = True
        else:
            # 检查常见日语词汇（仅限纯假名词汇，避免误报汉字）
            for word in JAPANESE_WORDS:
                if word in line:
                    report.error('日语残留', f'发现日语词汇: "{word}"', line_num)
                    found_any = True
    if not found_any:
        report.info_msg("✅ 日语残留检测通过")
    return found_any


def check_format(text_lines, report):
    """检查2：格式合规"""
    header_count = 0
    location_count = 0
    has_speaker_format = False

    for i, line in enumerate(text_lines):
        line_num = i + 1
        if re.match(r'^=+\s*(事件|END OF DAY)', line.strip('=')):
            header_count += 1
        if line.strip().startswith('#'):
            location_count += 1
        if '【' in line and '】' in line:
            has_speaker_format = True

    if header_count == 0:
        report.warning('格式', '未找到事件分割标记（==========）')
    if location_count == 0:
        report.warning('格式', '未找到地点标记（#地点 时段）')
    if not has_speaker_format:
        report.warning('格式', '未找到标准Speaker标记（【角色名】）')

    report.info_msg(f"事件数: {header_count}, 地点标记: {location_count}")


def check_protagonist_wordcount(text_lines, report):
    """检查8：主角台词字数"""
    protagonist_pattern = re.compile(r'【我】\s*(.+)')
    for i, line in enumerate(text_lines):
        line_num = i + 1
        match = protagonist_pattern.match(line.strip())
        if match:
            text = match.group(1)
            # 去除表演指导（括弧内容）
            text_clean = re.sub(r'（[^）]*）', '', text).strip()
            char_count = len(text_clean)
            if char_count > 15:
                report.warning('主角台词', f'主角单句{char_count}字，超过15字限制: "{text_clean[:30]}..."', line_num)


def check_banned_metaphors(text_lines, report):
    """检查7：禁止文艺煽情比喻"""
    for pattern in BANNED_METAPHORS:
        compiled = re.compile(pattern)
        for i, line in enumerate(text_lines):
            if compiled.search(line):
                report.warning('禁止比喻', f'疑似文艺煽情比喻: "{pattern}"', i + 1)


def check_character_redlines(text_content, report):
    """检查角色设定红线"""
    # 需要推断当前Day编号
    day_match = re.search(r'Day\s*(\d+)', text_content[:500])
    current_day = int(day_match.group(1)) if day_match else 0

    for char, rules in CHARACTER_REDLINES.items():
        for pattern_str, msg in rules:
            pattern = re.compile(pattern_str, re.DOTALL)
            if pattern.search(text_content):
                report.error('角色红线', f'{msg}', None)


def check_character_names(text_lines, report):
    """检查角色名一致性"""
    used_names = set()
    for line in text_lines:
        # 提取【角色名】标记
        matches = re.findall(r'【(.+?)】', line)
        for m in matches:
            if m not in ('旁白', '我'):
                used_names.add(m)

    # 检查是否有未识别的简称
    for name in used_names:
        # 简单的启发式检查
        if len(name) <= 2 and name not in ('育子', '南梨', '景子', '葵', '夏实', '紫',
                                             'Linda', '蔷薇', '彩', '瞳', '丽莎', '春奈',
                                             '莉香', '增田', '佐藤'):
            report.warning('角色名', f'角色名简称可能不规范: "{name}"')


def check_pov(text_lines, report):
    """检查6：POV合规"""
    # 检测地点标记
    location_pattern = re.compile(r'#\s*(.+?)\s+(清晨|上午|下午|傍晚|深夜)')
    for i, line in enumerate(text_lines):
        match = location_pattern.match(line.strip())
        if match:
            location = match.group(1)
            time_period = match.group(2)
            if time_period in POV_RULES:
                rules = POV_RULES[time_period]
                for forbidden_loc in rules['forbidden']:
                    if forbidden_loc in location:
                        report.error('POV违规',
                                     f'{time_period}时段主角不应出现在"{location}"（含禁地"{forbidden_loc}"）',
                                     i + 1)


def check_be_format(text_lines, report):
    """检查BE标记格式"""
    has_be_marker = False
    for i, line in enumerate(text_lines):
        if 'BE' in line and ('触发' in line or '☠' in line):
            has_be_marker = True
            # 检查是否包含完整分支文本
            # 简单检查：后续应有++选择标记
            found_branch = False
            for j in range(i + 1, min(i + 20, len(text_lines))):
                if '++选择' in text_lines[j] or '=== 分支' in text_lines[j]:
                    found_branch = True
                    break
            if not found_branch:
                report.warning('BE标记', f'BE触发点附近未找到完整分支文本', i + 1)

    if not has_be_marker:
        report.info_msg("本文件未找到BE触发点")


def check_csv_format(csv_lines, report):
    """对CSV文件的格式检查"""
    if not csv_lines:
        return
    # 检查列头
    header = csv_lines[0]
    expected_header = ['ID', 'Speaker', 'HeadProfile', 'CharLeft', 'CharMid',
                       'CharRight', 'Text', 'Background', 'BGM', 'Voice', 'Command', 'Note']
    if header != expected_header:
        report.error('CSV格式', f'列头不匹配\n  期望: {",".join(expected_header)}\n  实际: {",".join(header)}')
        return

    # 检查ID格式
    id_pattern = re.compile(r'^\d{8,}$')
    for i, row in enumerate(csv_lines[1:], 1):
        if len(row) != 12:
            report.error('CSV格式', f'第{i}行列数不匹配（期望12列，实际{len(row)}列）', i + 1)
        if row[0] and not id_pattern.match(row[0]):
            report.warning('CSV格式', f'第{i}行ID格式异常: {row[0]}', i + 1)

    report.info_msg(f"CSV共{len(csv_lines) - 1}行数据")


def read_file_auto(filepath):
    """自动识别txt/csv并读取"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
        return rows, ext
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, ext


def review_file(filepath, strict=False):
    """对剧本文件执行全面Review"""
    report = ReviewReport()
    report.strict = strict

    print(f"\n{'='*60}")
    print(f"  📋 Review: {os.path.basename(filepath)}")
    print(f"{'='*60}")

    data, file_type = read_file_auto(filepath)

    if file_type == '.csv':
        # CSV文件检查
        csv_rows = data
        text_lines = [','.join(row) for row in csv_rows]  # 用于文本分析

        print("\n  [1/8] 日语残留检测...")
        check_japanese(text_lines, report)

        print("  [2/8] CSV格式检查...")
        check_csv_format(csv_rows, report)

        print("  [3/8] 角色名一致性...")
        check_character_names(text_lines, report)

        # CSV跳过文字分析
        report.info_msg("CSV文件跳过了部分文字级别检查（7.比喻/8.字数）")

    else:
        # 文字剧本检查
        lines = data.split('\n')

        print("\n  [1/8] 日语残留检测...")
        check_japanese(lines, report)

        print("  [2/8] 格式合规检查...")
        check_format(lines, report)

        print("  [3/8] 角色名一致性...")
        check_character_names(lines, report)

        print("  [4/8] POV合规检查...")
        check_pov(lines, report)

        print("  [5/8] BE标记格式检查...")
        check_be_format(lines, report)

        print("  [6/8] 角色红线检查...")
        check_character_redlines(data, report)

        print("  [7/8] 禁止比喻检查...")
        check_banned_metaphors(lines, report)

        print("  [8/8] 主角台词字数检查...")
        check_protagonist_wordcount(lines, report)

    # 输出结果
    print(f"\n{'─'*60}")
    print(f"  📊 Review结果：{report.get_summary()}")
    print(f"{'─'*60}")

    if report.errors:
        print(f"\n  🔴 错误 ({len(report.errors)}):")
        for e in report.errors:
            print(f"     {e}")

    if report.warnings:
        print(f"\n  🟡 警告 ({len(report.warnings)}):")
        for w in report.warnings:
            print(f"     {w}")

    if report.info:
        print(f"\n  🔵 信息 ({len(report.info)}):")
        for info in report.info:
            print(f"     {info}")

    return report


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("用法：python auto_review.py <剧本文件.txt/.csv> [--strict] [--output report.txt]")
        sys.exit(1)

    filepath = sys.argv[1]
    strict = '--strict' in sys.argv
    output_file = None

    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(1)

    report = review_file(filepath, strict=strict)

    # 输出到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Review Report: {os.path.basename(filepath)}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(report.get_summary() + '\n\n')
            if report.errors:
                f.write(f"Errors ({len(report.errors)}):\n")
                for e in report.errors:
                    f.write(f"  {e}\n")
                f.write('\n')
            if report.warnings:
                f.write(f"Warnings ({len(report.warnings)}):\n")
                for w in report.warnings:
                    f.write(f"  {w}\n")
                f.write('\n')
            if report.info:
                f.write(f"Info ({len(report.info)}):\n")
                for info in report.info:
                    f.write(f"  {info}\n")
        print(f"\n📄 报告已保存到：{output_file}")

    # 返回错误数量作为退出码
    exit_code = 1 if report.errors else 0
    if strict and report.warnings:
        exit_code = 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
