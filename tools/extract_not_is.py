"""Extract and show all '不是X，是Y' patterns with context from a file"""
import re, sys

fpath = sys.argv[1]
max_show = int(sys.argv[2]) if len(sys.argv) > 2 else 200

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all 不是...是... patterns with surrounding context
# More precise pattern: look for 不是 followed by 是 within reasonable distance
pattern = re.compile(r'(.{20})不是(.{1,40})[，。、,;\s]*是(.{1,40})(.{10})')

matches = []
for m in pattern.finditer(content):
    full = m.group(0)
    before, neg, pos, after = m.groups()
    # Clean up
    neg = neg.strip()
    pos = pos.strip()
    if len(neg) > 2 and len(pos) > 2:  # Skip trivial matches
        matches.append((m.start(), neg[:30], pos[:30]))

# Deduplicate by context window
seen = set()
unique = []
for start, neg, pos in matches:
    key = (neg[:15], pos[:15])
    if key not in seen:
        seen.add(key)
        unique.append((start, neg, pos))

print(f"File: {fpath}")
print(f"Total matches: {len(matches)}, Unique patterns: {len(unique)}")
print("-" * 80)

for i, (start, neg, pos) in enumerate(unique[:max_show]):
    print(f"[{i+1}] 不是 {neg} → 是 {pos}")
