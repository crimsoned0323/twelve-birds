"""Verify the rebuilt combined txt for duplicates and issues"""
import re

with open(r'g:\codebuddy\十二飞鸟_codebuddy\十二飞鸟_全剧本合集.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 50)
print("  合集去重验证报告")
print("=" * 50)

# 1. Check common repeating phrases
checks = [
    '育子重排座位', '紫的最后占卜', '景子的电话', '雪代摸椅子',
    '巢燕的纽扣', '弹匣', '出道曲', '双雀的路线', '白无垢', '逐一确认',
    '黑皮书最后三页', '化妆间的灯', '纽扣',
]
print("\n-- 重点短语出现次数 --")
for phrase in checks:
    count = content.count(phrase)
    if count > 0:
        status = "  OK" if count <= 2 else "  WARN: appears " + str(count) + " times!"
        print(f"  '{phrase}': {count}{status}")

# 2. Day sequence
days = re.findall(r'#  Day (\d+)', content)
print(f"\n-- Day序列 ({len(days)} 个章节) --")
for d in days:
    print(f"  Day {d}")

# 3. Formula patterns
not_is = len(re.findall(r'不是.{1,10}[，。是].{1,10}', content))
air_smell = len(re.findall(r'空气里有.{1,30}还有更淡', content))
print(f"\n-- 句式统计 --")
print(f"  '不是A，是B' 句式: ~{not_is} 处")
print(f"  '空气里有X。还有更淡的Y': {air_smell} 处")

# 4. Total stats
lines = content.count('\n')
print(f"\n-- 总量 --")
print(f"  总字符: {len(content):,}")
print(f"  总行数: {lines:,}")
