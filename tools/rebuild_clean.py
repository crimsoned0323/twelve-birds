"""
Extract unique content from contaminated Day42-46 files,
de-duplicate, and rebuild clean Day files + combined txt.
"""
import os, re

SCRIPT_DIR = r"g:\codebuddy\十二飞鸟_codebuddy\文字剧本"
OUTPUT_FILE = r"g:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_全剧本合集.txt"

def read_file(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_sections(text):
    """Extract sections between ========== markers"""
    # Split by ========== markers
    parts = re.split(r'\n(?=={10,})', text)
    sections = []
    for part in parts:
        part = part.strip()
        if part:
            sections.append(part)
    return sections

def get_section_fingerprint(section):
    """Create a fingerprint from the first 200 chars for dedup"""
    first_event = ""
    m = re.search(r'事件[一二三四五六七八九十]+[：:]\s*(\S+)', section)
    if m:
        first_event = m.group(1)
    # Get first 150 meaningful chars
    clean = re.sub(r'[#\n\s*\-=]+', '', section)[:150]
    return first_event + "|" + clean[:100]

def get_day_number(section):
    """Extract day number from section"""
    m = re.search(r'Day\s*(\d+)', section)
    if m:
        return int(m.group(1))
    return None

# ============================================================
# STEP 1: Collect all clean Day 1-41 files
# ============================================================
clean_files = []
for f in sorted(os.listdir(SCRIPT_DIR)):
    if re.match(r'Day\d+\.txt$', f) or re.match(r'Day\d+剧本\.txt$', f):
        day_match = re.search(r'Day(\d+)', f)
        if day_match:
            day_num = int(day_match.group(1))
            if day_num <= 41:
                clean_files.append(f)

clean_files.sort(key=lambda x: int(re.search(r'Day(\d+)', x).group(1)))
print("Clean Day 1-41 files:")
for f in clean_files:
    print(f"  {f}")

# ============================================================
# STEP 2: Decontaminate Day42 and Day43
# ============================================================
print("\nDecontaminating Day42 and Day43...")

# Read the two source files
day42_content = read_file("Day42剧本.txt")
day43_content = read_file("Day43剧本.txt")

# Extract all sections
day42_sections = extract_sections(day42_content)
day43_sections = extract_sections(day43_content)

print(f"  Day42 has {len(day42_sections)} sections")
print(f"  Day43 has {len(day43_sections)} sections")

# Collect all unique sections with their fingerprints
all_sections = []
fingerprints_seen = set()

# Process Day42 sections first (confirmed ORIGINAL)
for sec in day42_sections:
    fp = get_section_fingerprint(sec)
    if fp and fp not in fingerprints_seen:
        fingerprints_seen.add(fp)
        all_sections.append(sec)
        day_match = re.search(r'Day\s*(\d+)', sec)
        if day_match:
            print(f"  Day42 ORIGINAL: Day {day_match.group(1)} — {fp[:60]}...")

# Process Day43 sections
for sec in day43_sections:
    fp = get_section_fingerprint(sec)
    if fp and fp not in fingerprints_seen:
        fingerprints_seen.add(fp)
        all_sections.append(sec)
        day_match = re.search(r'Day\s*(\d+)', sec)
        if day_match:
            print(f"  Day43 ORIGINAL: Day {day_match.group(1)} — {fp[:60]}...")
    elif fp in fingerprints_seen:
        day_match = re.search(r'Day\s*(\d+)', sec)
        day_str = day_match.group(1) if day_match else "?"
        print(f"  Day43 DUPLICATE SKIPPED: Day {day_str} — {fp[:60]}...")

print(f"\nTotal unique sections extracted: {len(all_sections)}")

# ============================================================
# STEP 3: Identify section types and sort
# ============================================================
# We know these sections should become:
# Day 42: 前夕/雪代白无垢 (from Day42, labeled Day 45)
# Day 43: 青鹭姬/星野葵 (from Day42, labeled Day 42) 
# Day 44: 朱雀姬/Linda (from Day42, labeled Day 44)
# Day 45: 双雀姬/彩&瞳 (from Day43, labeled Day 49)
# Day 46: 黄鹂姬/夏实 或 夜鸢姬 (depending on timeline)

# Let me identify each section by content keywords
section_map = {}
for sec in all_sections:
    sec_clean = sec[:300]
    if '白无垢' in sec_clean or '雪代的房间在三楼' in sec_clean:
        section_map['snow_crane_d45'] = sec
    elif '黑羽公寓' in sec_clean and '星野葵' in sec_clean:
        section_map['blue_heron_d42'] = sec
    elif '后巷' in sec_clean and 'Linda' in sec_clean:
        section_map['vermillion_d44'] = sec
    elif '双雀' in sec_clean and '后巷路线' in sec_clean:
        section_map['twin_sparrows_d49'] = sec
    elif '黑皮书最后三页' in sec_clean or '美咲蔷薇的房间在走廊' in sec_clean:
        section_map['night_kite_d47'] = sec
    elif '出道曲' in sec_clean and '排练室' in sec_clean:
        section_map['oriole_d43'] = sec
    elif '化妆间的灯' in sec_clean and '春奈' in sec_clean:
        section_map['mockingbird_d50'] = sec
    elif '弹匣' in sec_clean or '衣帽间' in sec_clean:
        section_map['swallow_d52'] = sec
    elif '茶室的光' in sec_clean or '账簿最后一页' in sec_clean:
        section_map['crane_tearoom_d53'] = sec
    elif '逐一确认' in sec_clean or '全员' in sec_clean:
        section_map['all_d54'] = sec
    elif '重排座位' in sec_clean or '最后占卜' in sec_clean or '摸椅子' in sec_clean:
        section_map['finale_d55'] = sec

print("\nIdentified sections:")
for k, v in section_map.items():
    print(f"  {k}: {v[:80].strip()[:80]}...")

# ============================================================
# STEP 4: Now rebuild Days 42-46 from the unique sections
# ============================================================
# According to the compressed timeline, Days 42-46 should be:
# Day 42: 雪代·白无垢 + 最后一夜 (前夕)
# Day 43: 星野葵·青鹭姬 (黑羽公寓)
# Day 44: Linda·朱雀姬 (后巷部署)
# Day 45: 彩&瞳·双雀姬 (后巷路线)
# Day 46: 夏实·黄鹂姬 (出道曲排练) OR 蔷薇·夜鸢姬 (黑皮书)

# The remaining sections (Day 47-55) are already in clean files or can be appended later

# Actually, let me just generate the clean combined txt directly
# including Days 1-41 clean + extracted unique sections + clean 47-53 + endings

print("\n" + "="*60)
print("Generating clean combined txt...")

# ============================================================
# STEP 5: Generate combined txt
# ============================================================
with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
    out.write('=' * 60 + '\n')
    out.write('  「十二飞鸟」全剧本合集 (去重修复版 v2.0)\n')
    out.write('  生成时间: 2026-06-28\n')
    out.write('=' * 60 + '\n\n')

    file_count = 0

    # --- Part A: Days 1-41 (clean files) ---
    for fname in clean_files:
        day_match = re.search(r'Day(\d+)', fname)
        day_num = int(day_match.group(1))
        out.write(f'\n{"#" * 60}\n')
        out.write(f'#  Day {day_num}: {fname}\n')
        out.write(f'{"#" * 60}\n\n')
        content = read_file(fname)
        out.write(content + '\n\n')
        file_count += 1
        print(f"  Added Day {day_num} ({fname})")

    # --- Part B: Extracted unique sections (Days 42-46) ---
    # Define the correct order for the compressed timeline
    extracted_order = [
        ('snow_crane_d45', 'Day 42: 前夕·白无垢 — 雪代的最后准备'),
        ('blue_heron_d42', 'Day 43: 青鹭姬 — 星野葵的镇静剂'),
        ('vermillion_d44', 'Day 44: 朱雀姬 — Linda的后巷部署'),
        ('twin_sparrows_d49', 'Day 45: 双雀姬 — 彩与瞳的撤离路线'),
        ('oriole_d43', 'Day 46: 黄鹂姬 — 夏实的出道曲与遗书'),
    ]

    day_num = 42
    for key, title in extracted_order:
        if key in section_map:
            out.write(f'\n{"#" * 60}\n')
            out.write(f'#  {title}\n')
            out.write(f'{"#" * 60}\n\n')
            out.write(section_map[key] + '\n\n')
            file_count += 1
            print(f"  Added {title}")
            day_num += 1
        else:
            print(f"  WARNING: Missing section {key}!")

    # --- Part C: Remaining unique sections as Days 47+ ---
    # These were part of the expanded timeline, reassign them
    remaining_keys = [
        ('night_kite_d47', 'Day 47: 夜鸢姬 — 美咲蔷薇的黑皮书'),
    ]
    for key, title in remaining_keys:
        if key in section_map:
            out.write(f'\n{"#" * 60}\n')
            out.write(f'#  {title}\n')
            out.write(f'{"#" * 60}\n\n')
            out.write(section_map[key] + '\n\n')
            file_count += 1
            print(f"  Added {title}")
            day_num += 1

    # --- Part D: Clean Day 48-53 files (System A, #1956-#1979) ---
    # Day 48 bridges the gap between extracted Day 47 and the compressed finale
    for d in range(48, 54):
        cand = f"Day{d}剧本.txt"
        cpath = os.path.join(SCRIPT_DIR, cand)
        if os.path.exists(cpath):
            out.write(f'\n{"#" * 60}\n')
            out.write(f'#  Day {d}: {cand}\n')
            out.write(f'{"#" * 60}\n\n')
            content = read_file(cand)
            out.write(content + '\n\n')
            file_count += 1
            print(f"  Added Day {d} ({cand})")
        else:
            print(f"  WARNING: {cand} not found!")

    # --- Part E: Endings ---
    ending_files = sorted([
        f for f in os.listdir(SCRIPT_DIR)
        if f.startswith('Day') and ('_endA' in f or '_endB' in f) and f.endswith('.txt')
    ])

    out.write(f'\n\n{"=" * 60}\n')
    out.write(f'  分支结局\n')
    out.write(f'{"=" * 60}\n\n')

    for fname in ending_files:
        out.write(f'\n{"#" * 60}\n')
        out.write(f'#  {fname}\n')
        out.write(f'{"#" * 60}\n\n')
        content = read_file(fname)
        out.write(content + '\n\n')
        file_count += 1
        print(f"  Added {fname}")

    # Footer
    total_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    out.write(f'\n{"=" * 60}\n')
    out.write(f'  合集完成 | {file_count} 章节 | {total_size:.2f} MB\n')
    out.write(f'  修复内容: 移除重复拼接段, 去重Day42-46\n')
    out.write(f'{"=" * 60}\n')

print(f"\nDone! {file_count} files combined, saved to {OUTPUT_FILE}")
print(f"File size: {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB")
