# -*- coding: utf-8 -*-
import re
with open(r'G:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_可视化套件.html', 'r', encoding='utf-8') as f:
    content = f.read()

print('=' * 100)
print('12角色防线成熟度（v5更新版）')
print('=' * 100)
m = re.search(r'4\. 各角色防线崩塌弧成熟度评估.*?</section>', content, re.DOTALL)
if m:
    text = m.group()
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL)
    for r in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells:
            print(' | '.join(cells))

print()
print('=' * 100)
print('对标媚肉之香差距评估（v5更新版）')
print('=' * 100)
m = re.search(r'5\. 对标.*?差距评估.*?</section>', content, re.DOTALL)
if m:
    text = m.group()
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL)
    for r in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells:
            print(' | '.join(cells))

print()
print('=' * 100)
print('总体评分+仪表盘（v5更新版）')
print('=' * 100)
m = re.search(r'1\. 总体评分.*?</section>', content, re.DOTALL)
if m:
    text = m.group()
    nums = re.findall(r'<div class="num">([^<]+)</div>', text)
    descs = re.findall(r'<div class="desc">([^<]+)</div>', text)
    vals = re.findall(r'<div class="lbl">([^<]+)</div>.*?<div class="val">([^<]+)</div>', text, re.DOTALL)
    for n, d in zip(nums, descs):
        print(f'  {n}  -  {d}')
    for l, v in vals:
        print(f'  {l}: {v}')
