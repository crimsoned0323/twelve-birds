#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
「十二飞鸟」全自动生产流水线
===========================
一键完成: Review检查 → CSV转化 → 伏笔扫描 → HTML汇总报告

用法:
  python run_pipeline.py                    # 完整流水线
  python run_pipeline.py --skip-review      # 跳过Review,只做转化
  python run_pipeline.py --only review      # 只做Review检查
  python run_pipeline.py --only csv         # 只做CSV转化
  python run_pipeline.py --day 5            # 只处理Day 5
"""

import io
import json
import os
import re
import subprocess
import sys
import time

# Windows GBK → UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================

# 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
TEXT_DIR = os.path.join(PROJECT_ROOT, "文字剧本")
CSV_DIR = os.path.join(PROJECT_ROOT, "csv剧本")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "_pipeline_output")
REVIEW_DIR = os.path.join(OUTPUT_DIR, "review")
SKELETON_DIR = os.path.join(OUTPUT_DIR, "skeleton")

# Python 路径 - 多级fallback
def _find_python():
    candidates = [
        os.path.expandvars(r"%USERPROFILE%\.workbuddy\binaries\python\versions\3.11.9\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\..\..\.workbuddy\binaries\python\versions\3.11.9\python.exe"),
        "python3",
        "python",
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p) or p in ("python", "python3"):
            return p
    return "python"

PYTHON = _find_python()


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def run_tool(tool_name, args, timeout=120):
    """运行一个工具并返回 (returncode, stdout, stderr)"""
    cmd = [PYTHON, os.path.join(TOOLS_DIR, tool_name)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def save_output(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


# ============================================================
# 第一步：扫描剧本文件
# ============================================================

def scan_scripts():
    """扫描文字剧本目录，识别有效剧本"""
    scripts = {}
    duplicates = []

    for fname in sorted(os.listdir(TEXT_DIR)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(TEXT_DIR, fname)

        # 匹配 Day N 剧本
        m = re.match(r'Day\s*(\d+)\s*剧本', fname)
        if m:
            day = int(m.group(1))
            scripts[day] = {
                'file': fpath,
                'name': fname,
                'day': day,
                'refined': '_细化版' in fname,
                'size_kb': round(os.path.getsize(fpath) / 1024, 1)
            }
        elif fname == '新建文本文档.txt':
            duplicates.append(fpath)

    return scripts, duplicates


# ============================================================
# 第二步：自动 Review
# ============================================================

def run_all_reviews(scripts):
    """对所有剧本运行 auto_review"""
    print("\n" + "=" * 70)
    print("  📋 阶段一：自动 Review 检查")
    print("=" * 70)

    ensure_dir(REVIEW_DIR)
    results = {}
    total_errors = 0
    total_warnings = 0

    for day in sorted(scripts.keys()):
        info = scripts[day]
        fpath = info['file']
        fname = info['name']
        label = f"Day{day}{' (细化版)' if info['refined'] else ''}"

        print(f"\n  [{label}] {fname}")
        print(f"  {'─' * 50}")

        rc, stdout, stderr = run_tool("auto_review.py", [fpath])

        # 保存报告
        report_name = f"review_Day{day}"
        if info['refined']:
            report_name += "_refined"
        report_name += ".txt"
        save_output(os.path.join("review", report_name), stdout)

        # 解析统计
        error_count = stdout.count("❌ 错误") + stdout.count("[ERROR]")
        warn_count = stdout.count("⚠") + stdout.count("[WARN]")
        total_errors += error_count
        total_warnings += warn_count

        results[day] = {
            'label': label,
            'rc': rc,
            'errors': error_count,
            'warnings': warn_count,
            'report': report_name
        }

        status = "✅ 通过" if rc == 0 and error_count == 0 else f"⚠ {error_count}错 / {warn_count}警"
        print(f"  {status}")
        # 打印关键行
        for line in stdout.split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['❌', '⚠', '日语', '红线', 'POV', '错误', '发现']):
                print(f"   {line[:100]}")

    return results, total_errors, total_warnings


# ============================================================
# 第三步：文字→CSV 转化
# ============================================================

def run_all_csv_conversions(scripts):
    """对所有剧本运行 txt_to_csv"""
    print("\n" + "=" * 70)
    print("  📊 阶段二：文字剧本 → CSV 转化")
    print("=" * 70)

    ensure_dir(CSV_DIR)
    results = {}
    total_csv_count = 0

    for day in sorted(scripts.keys()):
        info = scripts[day]
        if info['refined']:
            # 细化版单独输出子目录
            output_sub = os.path.join(CSV_DIR, f"Day{day}_refined")
        else:
            output_sub = CSV_DIR
        ensure_dir(output_sub)

        fpath = info['file']
        fname = info['name']
        label = f"Day{day}{' (细化版)' if info['refined'] else ''}"

        print(f"\n  [{label}] {fname} → {output_sub}")
        print(f"  {'─' * 50}")

        rc, stdout, stderr = run_tool("txt_to_csv.py", [fpath, output_sub])

        # 统计生成文件数
        csv_count = stdout.count(".csv")
        total_csv_count += csv_count

        results[day] = {
            'label': label,
            'rc': rc,
            'csv_count': csv_count,
            'output_dir': output_sub
        }

        if rc == 0:
            print(f"  ✅ 生成 {csv_count} 个CSV文件")
        else:
            print(f"  ❌ 转化失败 (rc={rc})")
            if stderr:
                print(f"  err: {stderr[:200]}")

        # 打印关键输出行
        for line in stdout.split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['✅', '事件', 'CSV', '行数', '生成']):
                print(f"   {line[:120]}")

    return results, total_csv_count


# ============================================================
# 第四步：伏笔追踪扫描
# ============================================================

def run_foreshadow_scan():
    """扫描剧本目录追踪伏笔"""
    print("\n" + "=" * 70)
    print("  🔮 阶段三：伏笔追踪扫描")
    print("=" * 70)

    rc, stdout, stderr = run_tool("foreshadow_tracker.py", ["scan", TEXT_DIR])

    print(f"\n  {'─' * 50}")
    for line in stdout.split('\n'):
        line = line.strip()
        if line:
            print(f"   {line[:120]}")

    # 生成伏笔报告
    rc2, report_out, _ = run_tool("foreshadow_tracker.py", ["report"])
    save_output("foreshadow_report.txt", report_out)

    return rc == 0


# ============================================================
# 第五步：生成骨架模板（缺失天数）
# ============================================================

def generate_skeletons(scripts):
    """为已有文字剧本的Day生成对应骨架参考"""
    print("\n" + "=" * 70)
    print("  🏗️ 阶段四：生成骨架参考")
    print("=" * 70)

    ensure_dir(SKELETON_DIR)
    plan_path = os.path.join(PROJECT_ROOT, "设定文档", "剧本规划_60天完整版.txt")

    if not os.path.exists(plan_path):
        print("  ⚠ 规划文档缺失，跳过骨架生成")
        return

    for day in sorted(scripts.keys()):
        info = scripts[day]
        label = f"Day{day}"

        print(f"\n  [{label}] 生成骨架...")
        rc, stdout, stderr = run_tool("event_skeleton.py",
                                       [str(day), "--plan", plan_path])

        skeleton_file = os.path.join(SKELETON_DIR, f"skeleton_Day{day}.txt")
        with open(skeleton_file, 'w', encoding='utf-8') as f:
            f.write(stdout)

        print(f"  ✅ 保存: skeleton_Day{day}.txt")


# ============================================================
# 第六步：生成 HTML 汇总报告
# ============================================================

def generate_html_report(scripts, review_results, csv_results, total_errors, total_warnings, total_csv, start_time):
    """生成美观的HTML汇总报告"""
    duration = time.time() - start_time

    # 统计概览
    total_days = len(scripts)
    review_ok = sum(1 for r in review_results.values() if r['errors'] == 0)

    # 构建剧本表格
    rows_html = ""
    for day in sorted(scripts.keys()):
        info = scripts[day]
        r = review_results.get(day, {})
        c = csv_results.get(day, {})

        err = r.get('errors', '?')
        warn = r.get('warnings', '?')
        csv_n = c.get('csv_count', 0)

        # 状态图标
        if err == 0:
            status = '<span style="color:#22c55e">✅</span>'
        elif isinstance(err, int) and err <= 3:
            status = f'<span style="color:#f59e0b">⚠ {err}错</span>'
        else:
            status = f'<span style="color:#ef4444">❌ {err}错</span>'

        rows_html += f"""
        <tr>
            <td><strong>Day {day}</strong></td>
            <td>{info['name']}</td>
            <td>{info['size_kb']} KB</td>
            <td>{status}</td>
            <td>{warn} 警告</td>
            <td>{csv_n} 个CSV</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>「十二飞鸟」自动化生产报告</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background:#0f1117; color:#e1e4e8; padding:20px; }}
.container {{ max-width:1100px; margin:0 auto; }}
h1 {{ font-size:28px; margin-bottom:5px; color:#f0f6fc; }}
.subtitle {{ color:#8b949e; margin-bottom:30px; font-size:14px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; margin-bottom:20px; }}
.card h2 {{ font-size:18px; color:#c9d1d9; margin-bottom:15px; border-bottom:1px solid #30363d; padding-bottom:8px; }}
.stats {{ display:flex; gap:15px; flex-wrap:wrap; margin-bottom:20px; }}
.stat-box {{ background:#21262d; border-radius:8px; padding:16px 24px; text-align:center; min-width:120px; flex:1; }}
.stat-box .num {{ font-size:32px; font-weight:bold; }}
.stat-box .label {{ font-size:12px; color:#8b949e; margin-top:5px; }}
.green {{ color:#22c55e; }}
.yellow {{ color:#f59e0b; }}
.red {{ color:#ef4444; }}
.blue {{ color:#58a6ff; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th {{ text-align:left; padding:10px 12px; border-bottom:1px solid #30363d; color:#8b949e; font-weight:600; }}
td {{ padding:8px 12px; border-bottom:1px solid #21262d; }}
tr:hover {{ background:#1c2128; }}
.footer {{ text-align:center; color:#484f58; margin-top:30px; font-size:12px; }}
.progress-bar {{ background:#21262d; border-radius:10px; height:8px; margin:10px 0 20px; overflow:hidden; }}
.progress-fill {{ background:linear-gradient(90deg, #22c55e, #58a6ff); height:100%; border-radius:10px; }}
.warn-list {{ font-size:13px; color:#f59e0b; line-height:1.8; }}
</style>
</head>
<body>
<div class="container">
    <h1>🦅 「十二飞鸟」自动化生产报告</h1>
    <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  耗时 {duration:.0f}秒</div>

    <!-- 统计卡片 -->
    <div class="stats">
        <div class="stat-box">
            <div class="num blue">{total_days}</div>
            <div class="label">文字剧本数</div>
        </div>
        <div class="stat-box">
            <div class="num green">{review_ok}</div>
            <div class="label">Review通过</div>
        </div>
        <div class="stat-box">
            <div class="num {'green' if total_errors == 0 else 'red'}">{total_errors}</div>
            <div class="label">总错误数</div>
        </div>
        <div class="stat-box">
            <div class="num yellow">{total_warnings}</div>
            <div class="label">总警告数</div>
        </div>
        <div class="stat-box">
            <div class="num blue">{total_csv}</div>
            <div class="label">生成CSV文件</div>
        </div>
    </div>

    <div class="progress-bar">
        <div class="progress-fill" style="width:{min(100, int(review_ok / max(total_days, 1) * 100))}%"></div>
    </div>
    <p style="font-size:12px;color:#8b949e">Review通过率: {review_ok}/{total_days} ({int(review_ok / max(total_days, 1) * 100)}%)</p>

    <!-- 剧本明细 -->
    <div class="card">
        <h2>📋 剧本处理明细</h2>
        <table>
            <thead>
                <tr><th>天数</th><th>文件名</th><th>大小</th><th>Review</th><th>警告</th><th>CSV</th></tr>
            </thead>
            <tbody>{rows_html}
            </tbody>
        </table>
    </div>

    <!-- 文件结构 -->
    <div class="card">
        <h2>📁 输出文件结构</h2>
        <pre style="font-size:13px;color:#8b949e;line-height:1.6;">
文字剧本/           ← {total_days} 个原始 .txt 剧本
csv剧本/            ← {total_csv} 个转化后的 .csv 文件
_pipeline_output/
  ├── review/       ← 各Day Review报告
  ├── skeleton/     ← 各Day骨架参考
  ├── foreshadow_report.txt  ← 全剧伏笔报告
  └── pipeline_report.html   ← 本报告
        </pre>
    </div>

    <div class="footer">
        「十二飞鸟」自动化工具链 · event_skeleton + auto_review + txt_to_csv + foreshadow_tracker
    </div>
</div>
</body>
</html>"""

    report_path = os.path.join(OUTPUT_DIR, "pipeline_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return report_path


# ============================================================
# 主流程
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='「十二飞鸟」全自动生产流水线')
    parser.add_argument('--skip-review', action='store_true', help='跳过Review阶段')
    parser.add_argument('--skip-csv', action='store_true', help='跳过CSV转化阶段')
    parser.add_argument('--skip-skeleton', action='store_true', help='跳过骨架生成')
    parser.add_argument('--only', choices=['review', 'csv', 'skeleton', 'foreshadow'],
                        help='只运行指定阶段')
    parser.add_argument('--day', type=int, help='只处理指定Day')
    parser.add_argument('--day-range', nargs=2, type=int, metavar=('START', 'END'),
                        help='处理Day范围 (含两端), 如: --day-range 3 8')

    args = parser.parse_args()

    print("╔" + "═" * 68 + "╗")
    print("║" + "  🦅 「十二飞鸟」全自动生产流水线".center(60) + "║")
    print("║" + f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(60) + "║")
    print("╚" + "═" * 68 + "╝")

    start_time = time.time()
    ensure_dir(OUTPUT_DIR)
    ensure_dir(REVIEW_DIR)
    ensure_dir(SKELETON_DIR)

    # 扫描剧本
    scripts, duplicates = scan_scripts()

    if args.day:
        scripts = {args.day: scripts[args.day]} if args.day in scripts else {}
        if not scripts:
            print(f"  ❌ Day {args.day} 剧本不存在！")
            return

    if args.day_range:
        start_d, end_d = args.day_range
        scripts = {d: scripts[d] for d in sorted(scripts) if start_d <= d <= end_d}
        if not scripts:
            print(f"  ❌ 范围内 Day {start_d}~{end_d} 无有效剧本！")
            return

    print(f"\n  📂 扫描完成: {len(scripts)} 个有效剧本")
    if duplicates:
        print(f"  ⚠ 跳过 {len(duplicates)} 个重复文件: {[os.path.basename(d) for d in duplicates]}")

    for day in sorted(scripts.keys()):
        info = scripts[day]
        print(f"    Day {day:>2}: {info['name']:<30s} ({info['size_kb']} KB)")

    review_results = {}
    csv_results = {}
    total_errors = 0
    total_warnings = 0
    total_csv = 0

    # 执行各阶段
    run_review = args.only in (None, 'review') and not args.skip_review
    run_csv = args.only in (None, 'csv') and not args.skip_csv
    run_fs = args.only in (None, 'foreshadow')
    run_sk = args.only in (None, 'skeleton') and not args.skip_skeleton

    if args.only:
        run_review = args.only == 'review'
        run_csv = args.only == 'csv'
        run_fs = args.only == 'foreshadow'
        run_sk = args.only == 'skeleton'

    # 阶段一：Review
    if run_review:
        review_results, total_errors, total_warnings = run_all_reviews(scripts)
    else:
        print("\n  ⏭ 跳过 Review 阶段")

    # 阶段二：CSV 转化
    if run_csv:
        csv_results, total_csv = run_all_csv_conversions(scripts)
    else:
        print("\n  ⏭ 跳过 CSV 转化阶段")

    # 阶段三：伏笔扫描
    if run_fs:
        run_foreshadow_scan()
    else:
        print("\n  ⏭ 跳过伏笔扫描阶段")

    # 阶段四：骨架生成
    if run_sk:
        generate_skeletons(scripts)
    else:
        print("\n  ⏭ 跳过骨架生成阶段")

    # 生成HTML报告
    report_path = generate_html_report(scripts, review_results, csv_results,
                                        total_errors, total_warnings, total_csv,
                                        start_time)

    # 总结
    duration = time.time() - start_time
    print("\n" + "=" * 70)
    print("  🎉 流水线执行完毕!")
    print("=" * 70)
    print(f"""
   ⏱ 总耗时: {duration:.1f} 秒
   📄 剧本数: {len(scripts)} 个
   📊 CSV文件: {total_csv} 个
   🔍 错误/警告: {total_errors} / {total_warnings}

   📁 报告文件: {report_path}
   📁 Review详情: {REVIEW_DIR}
   📁 CSV输出: {CSV_DIR}
   📁 骨架参考: {SKELETON_DIR}
""")

    # 自动打开报告
    print(f"  🌐 在浏览器中打开报告: file:///{report_path.replace(os.sep, '/')}")


if __name__ == '__main__':
    main()
