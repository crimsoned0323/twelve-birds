"""Analyze '不是A，是B' pattern density across all script files"""
import re, os, glob

script_dir = r'g:\codebuddy\十二飞鸟_codebuddy\文字剧本'

# Pattern: 不是...是... (with nearby comma/period)
pattern = re.compile(r'不是.{1,20}[，。,\.是].{1,20}')

results = []
for fname in sorted(os.listdir(script_dir)):
    if not fname.endswith('.txt'):
        continue
    if not (fname.startswith('Day') or fname in ['新建文本文档.txt']):
        continue
    fpath = os.path.join(script_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = pattern.findall(content)
    count = len(matches)
    lines = content.count('\n')
    density = count / max(lines, 1) * 100  # per 100 lines
    
    if count > 0:
        results.append((fname, count, lines, density, matches[:5]))

# Sort by count descending
results.sort(key=lambda x: -x[1])

print(f"{'File':<25} {'Count':>6} {'Lines':>6} {'/100L':>7}  Sample")
print("-" * 100)
for fname, count, lines, density, samples in results[:25]:
    sample = samples[0][:60] if samples else ""
    print(f"{fname:<25} {count:>6} {lines:>6} {density:>6.1f}  {sample}")

print(f"\nTotal files with matches: {len(results)}")
total = sum(r[1] for r in results)
print(f"Total '不是...是' occurrences: {total}")
