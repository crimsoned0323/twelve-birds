#!/usr/bin/env python3
"""
十二飞鸟 全剧本合集 v4.0 构建脚本
- 去重：删除Day41-54区间重复段落
- 重排：按新骨架移动内容到正确Day
- 剥离：删除判定块/制作笔记
- 填空：Day53新创作内容
- 组装：完整60天 + 4结局
"""

import os
import re

BASE = r"G:\codebuddy\十二飞鸟_codebuddy\文字剧本"
OUTPUT = r"G:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_全剧本合集_v4.txt"

SEP = "=" * 60

def read_file(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_lines(text, start_line, end_line):
    """提取指定行范围的内容（1-based）"""
    lines = text.split("\n")
    return "\n".join(lines[start_line - 1 : end_line])

def extract_between_markers(text, start_marker, end_marker=None):
    """提取两个标记之间的内容"""
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return None
    start_idx = text.rfind("\n", 0, start_idx) + 1 if start_idx > 0 else 0
    
    if end_marker:
        end_idx = text.find(end_marker, start_idx + len(start_marker))
        if end_idx == -1:
            return text[start_idx:]
        end_idx = text.rfind("\n", 0, end_idx) + 1
        return text[start_idx:end_idx]
    return text[start_idx:]

def strip_judgment_blocks(text):
    """剥离Day54中的判定块/制作笔记"""
    lines = text.split("\n")
    cleaned = []
    skip_mode = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过制作笔记行
        if "※本日为共享路径" in line or "※路线判定在本日" in line:
            i += 1
            continue
        
        # 跳过路线判定系统块（从"路线判定系统"到文件末尾的判定块）
        if "路线判定系统" in line and "参照" in line:
            # 跳过直到遇到下一个 ========== 或 ===== 分隔线
            while i < len(lines) and not lines[i].startswith("=========="):
                i += 1
            continue
        
        # 跳过判定逻辑段落（含END-/BE/好感度判定的段落）
        if any(kw in line for kw in ["路线判定系统", "第一步：END-C", "第二步：BE", "第三步：主线结局",
                                       "条件A：", "条件B：", "条件C：", "条件D：",
                                       "※注意：END-C", "※注意：END-D", "※所有BE"]):
            i += 1
            continue
        
        # 清理事件链标题中的"好感度结算·路线判定"
        if "好感度结算·路线判定" in line:
            line = line.replace("好感度结算·路线判定·", "")
        
        # 跳过嵌入的判定逻辑段（"规则很清楚" 到 "END-D" 结束段）
        if "规则很清楚。Day 45 的路线判定系统" in line:
            # 跳过直到 "我把纸折起来" 这一行
            while i < len(lines) and "我把纸折起来" not in lines[i]:
                i += 1
            continue
        
        # 跳过 BE 判定段
        if "如果超过四个人低于六" in line and "BE" in line:
            i += 1
            continue
        if "第三步——主线结局判定" in line:
            i += 1
            continue
        if "如果雪代没有到十——END-A" in line:
            i += 1
            continue
        if "如果雪代到了八——但青鹭" in line:
            i += 1
            continue
        if "如果雪代到十。至少七个人" in line:
            i += 1
            continue
        if "以上全部满足——END-D" in line:
            i += 1
            continue
        # 跳过这些段落的续行（以【旁白】开头但属于判定逻辑的）
        if skip_mode and line.strip() == "":
            skip_mode = False
        
        # 跳过"Day 54 结束"之后的判定块
        if "Day 54 结束" in line and "路线分支" in line:
            # 保留这一行但跳过后面的判定块
            cleaned.append(line)
            i += 1
            # 跳过后续所有判定内容
            while i < len(lines):
                if lines[i].startswith("==========") and "事件" in lines[i]:
                    break
                if lines[i].startswith("  【路线判定"):
                    break
                if "路线判定" in lines[i] or "END-" in lines[i] or "好感度" in lines[i] or "BE" in lines[i] or "条件" in lines[i] or "※" in lines[i]:
                    i += 1
                    continue
                # 如果是空行或分隔线，也跳过
                if lines[i].strip() == "" or lines[i].startswith("=="):
                    i += 1
                    continue
                # 其他内容保留
                break
            continue
        
        cleaned.append(line)
        i += 1
    
    return "\n".join(cleaned)

def strip_duplicate_events(text, event_titles_to_remove):
    """从文件中删除指定标题的事件"""
    lines = text.split("\n")
    result = []
    skip = False
    
    for i, line in enumerate(lines):
        # 检查是否是事件标题行
        if line.startswith("========== 事件"):
            event_title = line.replace("========== ", "").replace(" ==", "")
            if any(t in event_title for t in event_titles_to_remove):
                skip = True
                continue
            else:
                skip = False
        
        if not skip:
            result.append(line)
    
    return "\n".join(result)

def build_day_header(day_num, title, events=None):
    """构建Day标题头"""
    header = f"\n{SEP}\n#  Day {day_num}：{title}\n{SEP}\n"
    if events:
        header += f"\n  [事件链]\n{events}\n"
    return header

def main():
    print("=" * 60)
    print("  十二飞鸟 全剧本合集 v4.0 构建脚本")
    print("  去重 · 重排 · 剥离判定 · 填空 · 组装")
    print("=" * 60)
    
    parts = []
    stats = {"total_files": 0, "total_lines": 0, "stripped": 0}
    
    # ==========================================================
    # 文件头
    # ==========================================================
    parts.append(f"""{SEP}
#  十二飞鸟 — 全剧本合集 v4.0
#  去重版 · 判定逻辑已剥离至 路线判定.config
#  60天共享路径 + 4条结局路线
{SEP}
""")
    
    # ==========================================================
    # 第一部分：共享路径 Day 1 ~ Day 54
    # ==========================================================
    parts.append(f"\n{'=' * 60}\n  第一部分：共享路径 (Day 1 ~ Day 54)\n{'=' * 60}\n")
    
    # --- Day 1-41: 使用现有文件 ---
    print("\n[1/5] Day 1-41: 读取现有文件...")
    
    # Day1 和 Day2 使用不同命名
    day1_2_mapping = {
        1: "Day1.txt",
        2: "Day2.txt",
    }
    
    for day in range(1, 42):
        if day in day1_2_mapping:
            filename = day1_2_mapping[day]
        else:
            filename = f"Day{day}剧本.txt"
        
        content = read_file(filename)
        if content:
            # Day 41 特殊处理：只取正文部分，避免整文件1493行mega混入
            if day == 41:
                lines = content.split("\n")
                # 找到第二个Day区段标记 = 正文结束，mega拼接内容开始
                # mega文件中Day41内容结束于第二个"Day 4"标签（行228的 Day41重复 或 行378的 Day42）
                cutoff_line = len(lines)
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    # 匹配 "========== Day 4X：========" 形式的重复标记
                    if stripped.startswith("==========") and ("Day 4" in stripped or "Day 5" in stripped):
                        if i > 10:  # 跳过文件最前面的标题块（前10行内）
                            cutoff_line = i
                            break
                if cutoff_line < len(lines):
                    content = "\n".join(lines[:cutoff_line]).rstrip()
                    print(f"  ✓ Day 41 (已从mega文件截取, 保留前{cutoff_line}行)")
                else:
                    print(f"  ✓ Day 41")
            
            parts.append(content.rstrip() + "\n")
            stats["total_files"] += 1
            line_count = content.count("\n")
            stats["total_lines"] += line_count
        else:
            parts.append(f"\n{SEP}\n#  Day {day} [文件缺失: {filename}]\n{SEP}\n\n[此天剧本内容暂缺]\n")
            print(f"  ⚠ Day {day} 文件缺失: {filename}")
    
    print(f"  ✓ Day 1-41 完成 ({stats['total_files']} 个文件)")
    
    # --- Day 41 mega 文件内容提取 ---
    print("\n[2/5] 从Day41 mega文件提取Day42/44/46/47/50/52内容...")
    day41_mega = read_file("Day41剧本.txt")
    if not day41_mega:
        print("  ✗ Day41剧本.txt 读取失败!")
        return
    
    mega_lines = day41_mega.split("\n")
    
    def extract_mega_section(start_marker, end_marker=None):
        """从mega文件中提取section"""
        text = day41_mega
        start_idx = text.find(start_marker)
        if start_idx == -1:
            print(f"    ⚠ 未找到标记: {start_marker}")
            return None
        
        # 回退到行首
        start_idx = text.rfind("\n", 0, start_idx) + 1
        
        if end_marker:
            end_idx = text.find(end_marker, start_idx + len(start_marker))
            if end_idx == -1:
                return text[start_idx:].rstrip()
            end_idx = text.rfind("\n", 0, end_idx) + 1
            return text[start_idx:end_idx].rstrip()
        return text[start_idx:].rstrip()
    
    # Day 42: 黑田来电/景子点头/奈良校门/纽扣还在 (lines 621-797)
    day42_content = extract_mega_section(
        "========== Day 42：=========",
        "========== Day 44 结束"
    )
    if day42_content:
        # 清理标签
        day42_content = day42_content.replace("========== Day 42：========", f"{SEP}\n#  Day 42：黑田来电 — 奈良校门\n{SEP}")
        parts.append("\n" + day42_content + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day42_content.count("\n")
        print(f"  ✓ Day 42 (黑田来电) 提取成功")
    else:
        print(f"  ⚠ Day 42 提取失败")
    
    # Day 43: 使用 P0 修复版
    print("\n[3/5] Day 43-54: 去重 + 重排...")
    day43 = read_file("Day43剧本.txt")
    if day43:
        parts.append(day43.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day43.count("\n")
        print(f"  ✓ Day 43 (收网)")
    
    # Day 44: 黑羽公寓/备用镇静剂/沉默的时间/替法律做的 (lines 972-1151)
    day44_content = extract_mega_section(
        "========== Day 42：========\n",
        "========== Day 44：========="
    )
    # 如果上面没找到，尝试另一种标记
    if not day44_content:
        day44_content = extract_mega_section(
            "========== 事件一：黑羽公寓",
            "========== Day 44：========="
        )
        if day44_content:
            day44_content = f"{SEP}\n#  Day 44：备用镇静剂 — 青鹭交底\n{SEP}\n\n" + day44_content
    
    if day44_content:
        # 清理跳转标记和mega章节边界
        day44_content = re.sub(r"========== Day \d+.*?==========", "", day44_content)
        day44_content = re.sub(r"========== Day \d+ 结束.*?==========", "", day44_content)
        day44_content = re.sub(r"========== Day \d+：=+\n?", "", day44_content)
        day44_content = re.sub(r"========== Day \d+：=+\n?", "", day44_content)  # 二次清理
        if "Day 44" not in day44_content[:100]:
            day44_content = f"{SEP}\n#  Day 44：备用镇静剂 — 青鹭交底\n{SEP}\n\n" + day44_content.lstrip()
        parts.append("\n" + day44_content.strip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day44_content.count("\n")
        print(f"  ✓ Day 44 (青鹭交底) 提取成功")
    else:
        print(f"  ⚠ Day 44 提取失败")
    
    # Day 45: Day45剧本.txt，删除重复事件(#1949逐一确认, #1950统计与判定, #1951白无垢)
    day45 = read_file("Day45剧本.txt")
    if day45:
        # 删除重复事件
        day45 = strip_duplicate_events(day45, ["逐一确认", "统计与判定", "白无垢"])
        # 清理事件链标题中的重复项
        day45_lines = day45.split("\n")
        cleaned_45 = []
        for line in day45_lines:
            # 跳过事件链中已删除事件的描述行
            if any(kw in line for kw in ["#1949  逐一确认", "#1950  统计与判定", "#1951  白无垢"]):
                continue
            cleaned_45.append(line)
        day45 = "\n".join(cleaned_45)
        parts.append(day45.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day45.count("\n")
        stats["stripped"] += 3
        print(f"  ✓ Day 45 (删除3个重复事件: 逐一确认/统计判定/白无垢)")
    
    # Day 46: 后巷碰头/部署图/不报备/两个人的行动 (lines 1152-1325)
    day46_content = extract_mega_section(
        "========== Day 44：=========" ,
        "========== Day 47 结束"
    )
    if not day46_content:
        day46_content = extract_mega_section(
            "========== 事件一：后巷碰头",
            "========== Day 47 结束"
        )
        if day46_content:
            day46_content = f"{SEP}\n#  Day 46：后巷部署 — 两个人的行动\n{SEP}\n\n" + day46_content
    
    if day46_content:
        day46_content = re.sub(r"========== Day \d+.*?跳转.*?==========", "", day46_content)
        day46_content = re.sub(r"========== Day \d+：=+\n?", "", day46_content)
        day46_content = re.sub(r"========== Day \d+：=+\n?", "", day46_content)
        if "Day 46" not in day46_content[:100]:
            day46_content = f"{SEP}\n#  Day 46：后巷部署 — 两个人的行动\n{SEP}\n\n" + day46_content.lstrip()
        parts.append("\n" + day46_content.strip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day46_content.count("\n")
        print(f"  ✓ Day 46 (后巷部署) 提取成功")
    else:
        print(f"  ⚠ Day 46 提取失败")
    
    # Day 47: 黑皮书最后三页/六年的记录 (lines 1326-1493)
    day47_content = extract_mega_section(
        "========== Day 47 结束·跳转 Day 48 =========="
    )
    if not day47_content:
        day47_content = extract_mega_section(
            "========== 事件一：黑皮书最后三页"
        )
        if day47_content:
            day47_content = f"{SEP}\n#  Day 47：夜鸢黑皮书 — 最后三页\n{SEP}\n\n" + day47_content
    
    if day47_content:
        day47_content = re.sub(r"========== Day \d+.*?跳转.*?==========", "", day47_content)
        if "Day 47" not in day47_content[:100]:
            day47_content = f"{SEP}\n#  Day 47：夜鸢黑皮书 — 最后三页\n{SEP}\n\n" + day47_content.lstrip()
        parts.append("\n" + day47_content.strip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day47_content.count("\n")
        print(f"  ✓ Day 47 (夜鸢黑皮书) 提取成功")
    else:
        print(f"  ⚠ Day 47 提取失败")
    
    # Day 48: 使用原Day49剧本.txt (最后的确认)
    day48 = read_file("Day49剧本.txt")
    if day48:
        # 替换Day编号
        day48 = day48.replace("Day 49", "Day 48")
        parts.append(day48.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day48.count("\n")
        print(f"  ✓ Day 48 (原Day49: 最后的确认)")
    
    # Day 49: 使用原Day50剧本.txt (各自的黎明)
    day49 = read_file("Day50剧本.txt")
    if day49:
        day49 = day49.replace("Day 50", "Day 49")
        parts.append(day49.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day49.count("\n")
        print(f"  ✓ Day 49 (原Day50: 各自的黎明)")
    
    # Day 50: 双雀任务/黄鹂任务/神鸦任务/银鹮座位 (lines 378-620)
    day50_content = extract_mega_section(
        "========== Day 42 结束·跳转 Day 43 ==========",
        "========== Day 42：========="
    )
    if not day50_content:
        day50_content = extract_mega_section(
            "========== 事件一：双雀任务",
            "========== Day 42：========="
        )
        if day50_content:
            day50_content = f"{SEP}\n#  Day 50：双雀任务 — 撤退路线布置\n{SEP}\n\n" + day50_content
    
    if day50_content:
        day50_content = re.sub(r"========== Day \d+.*?跳转.*?==========", "", day50_content)
        if "Day 50" not in day50_content[:100]:
            day50_content = f"{SEP}\n#  Day 50：双雀任务 — 撤退路线布置\n{SEP}\n\n" + day50_content.lstrip()
        parts.append("\n" + day50_content.strip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day50_content.count("\n")
        print(f"  ✓ Day 50 (四连任务) 提取成功")
    else:
        print(f"  ⚠ Day 50 提取失败")
    
    # Day 51: 使用现有Day51剧本.txt (十二杯茶)
    day51 = read_file("Day51剧本.txt")
    if day51:
        parts.append(day51.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day51.count("\n")
        print(f"  ✓ Day 51 (十二杯茶)")
    
    # Day 52: 白无垢(from mega) + 现有Day52剧本.txt (夜之前)
    # 提取白无垢场景
    shir_mushi = extract_mega_section(
        "========== 事件一：白无垢改制 ==========",
        "========== 事件二：育子送茶"
    )
    if shir_mushi:
        shir_mushi = f"{SEP}\n#  Day 52：白无垢 — 最后一夜\n{SEP}\n\n  [事件链]\n  清晨  #1968a 白无垢改制      雪代试穿改制和服·白色·侧腰结·\"凉了二十一年\"\n\n" + shir_mushi
    
    day52 = read_file("Day52剧本.txt")
    if day52:
        # 合并白无垢 + 现有Day52内容
        if shir_mushi:
            # 去掉现有Day52的标题头，只保留事件
            day52_events = re.sub(r"^.*?\[事件链\].*?\n", "", day52, flags=re.DOTALL)
            day52_events = re.sub(r"^={60}\n  Day 52.*?\n={60}\n", "", day52_events)
            combined = shir_mushi.rstrip() + "\n\n" + day52_events.strip() + "\n"
            parts.append("\n" + combined)
        else:
            parts.append(day52.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += len(combined.split("\n")) if shir_mushi else day52.count("\n")
        print(f"  ✓ Day 52 (白无垢 + 夜之前) 合并成功")
    else:
        if shir_mushi:
            parts.append("\n" + shir_mushi + "\n")
            stats["total_files"] += 1
            print(f"  ✓ Day 52 (仅白无垢，Day52剧本.txt缺失)")
    
    # Day 53: Day53剧本.txt（宴会厅/厨房门/茶室）
    day53 = read_file("Day53剧本.txt")
    if day53:
        parts.append(day53.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day53.count("\n")
        print(f"  ✓ Day 53 (极乐之夜前夕 — 新创作)")
    
    # Day 54: Day54剧本.txt，剥离判定块
    print("\n[4/5] Day 54: 剥离判定块...")
    day54 = read_file("Day54剧本.txt")
    if day54:
        day54_clean = strip_judgment_blocks(day54)
        
        # 额外清理：删除事件链中的"好感度"描述
        day54_lines = day54_clean.split("\n")
        cleaned_54 = []
        for line in day54_lines:
            # 清理事件链标题
            if "好感度结算·路线判定" in line:
                line = line.replace("好感度结算·路线判定·", "")
            # 删除制作笔记
            if line.strip().startswith("※") and any(kw in line for kw in ["本日为", "路线判定", "注意", "BE"]):
                continue
            # 删除独立的判定块标题行
            if "【路线判定" in line:
                continue
            cleaned_54.append(line)
        
        day54_clean = "\n".join(cleaned_54)
        
        # 删除末尾的判定块（从"Day 54 结束"之后的全部内容，只保留分隔线）
        end_marker = "Day 54 结束"
        end_idx = day54_clean.find(end_marker)
        if end_idx != -1:
            # 保留到"Day 54 结束"行
            line_end = day54_clean.find("\n", end_idx)
            if line_end != -1:
                day54_clean = day54_clean[:line_end + 1]
        
        parts.append(day54_clean.rstrip() + "\n")
        stats["total_files"] += 1
        stats["total_lines"] += day54_clean.count("\n")
        print(f"  ✓ Day 54 (判定块已剥离)")
    
    print(f"\n  共享路径完成: {stats['total_files']} 个文件, {stats['total_lines']} 行")
    print(f"  去重删除: {stats['stripped']} 个重复事件")
    
    # ==========================================================
    # 结局路线
    # ==========================================================
    print("\n[5/5] 结局路线...")
    
    endings = [
        ("END-A", "法理的正义", [
            ("Day55_endA.txt", "Day 55"),
            ("Day56_endA.txt", "Day 56"),
            ("Day57_endA.txt", "Day 57"),
            ("Day58_endA.txt", "Day 58"),
            ("Day59_endA.txt", "Day 59"),
            ("Day60_endA.txt", "Day 60"),
        ]),
        ("END-B", "堕落的正义", [
            ("Day55_endB.txt", "Day 55"),
            ("Day56_endB.txt", "Day 56"),
            ("Day57_endB.txt", "Day 57"),
            ("Day58_endB.txt", "Day 58"),
            ("Day59_endB.txt", "Day 59"),
            ("Day60_endB.txt", "Day 60"),
        ]),
        ("END-C", "彻底的沉沦", [
            ("Day55_endC.txt", "Day 55"),
            ("Day56_endC.txt", "Day 56"),
            ("Day57_endC.txt", "Day 57"),
            ("Day58_endC.txt", "Day 58"),
            ("Day59_endC.txt", "Day 59"),
        ]),
        ("END-D", "朱雀的绽放·真结局", [
            ("Day55_endD.txt", "Day 55"),
            ("Day56_endD.txt", "Day 56"),
            ("Day57_endD.txt", "Day 57"),
            ("Day58_endD.txt", "Day 58"),
            ("Day59_endD.txt", "Day 59"),
        ]),
    ]
    
    for i, (end_code, end_name, day_files) in enumerate(endings, 1):
        section_num = i + 1
        parts.append(f"\n{'=' * 60}\n  第{['一','二','三','四','五'][section_num-1]}部分：{end_code} {end_name}\n{'=' * 60}\n")
        
        for filename, day_label in day_files:
            content = read_file(filename)
            if content:
                parts.append(content.rstrip() + "\n")
                stats["total_files"] += 1
                stats["total_lines"] += content.count("\n")
            else:
                parts.append(f"\n{SEP}\n#  {day_label} ({end_code}) [文件缺失: {filename}]\n{SEP}\n\n")
                print(f"  ⚠ {filename} 缺失")
        
        print(f"  ✓ {end_code} {end_name}")
    
    # ==========================================================
    # 文件尾
    # ==========================================================
    parts.append(f"\n{'=' * 60}\n#  十二飞鸟 · 完\n{'=' * 60}\n")
    
    # ==========================================================
    # 写入文件
    # ==========================================================
    print(f"\n{'=' * 60}")
    print(f"  写入: {OUTPUT}")
    full_text = "\n".join(parts)
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    final_lines = full_text.count("\n")
    final_size = os.path.getsize(OUTPUT)
    
    print(f"  ✓ 完成!")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  总行数: {final_lines}")
    print(f"  文件大小: {final_size / 1024:.1f} KB")
    print(f"  去重删除: {stats['stripped']} 个重复事件")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
