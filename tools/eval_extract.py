# -*- coding: utf-8 -*-
import re
with open(r'G:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_可视化套件.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 80)
print("【12角色防线成熟度表】")
print("=" * 80)
m = re.search(r'12角色防线成熟度.*?</table>', content, re.DOTALL)
if m:
    text = m.group()
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL)
    for r in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells:
            print(' | '.join(cells))

print()
print("=" * 80)
print("【12角色阶段总览表】")
print("=" * 80)
m = re.search(r'12角色阶段总览.*?</table>', content, re.DOTALL)
if m:
    text = m.group()
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL)
    for r in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells:
            print(' | '.join(cells))

print()
print("=" * 80)
print("【综合评估与对标媚肉之香差距】")
print("=" * 80)
m = re.search(r'综合评估与差距.*?</table>', content, re.DOTALL)
if m:
    text = m.group()
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL)
    for r in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells:
            print(' | '.join(cells))
