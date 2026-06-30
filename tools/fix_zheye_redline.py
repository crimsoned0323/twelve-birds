"""
修复 v5 全剧本合集中莉香称呼玩家"哲也"的红线问题。
莉香（女友）不应该用卧底化名"哲也"称呼玩家。

修复规则：
- 莉香消息中的"哲也——"前缀 → 删除
- 莉香消息中的"哲也。"前缀 → 删除
- 莉香对话中的"……哲也。" → 删除
- 莉香对话中的"晚安。哲也。" → "晚安。"
- 事件头中的"哲也你是不是出事了" → "你是不是出事了"
- Day2中独立的"哲也。" → 删除该行

保留：
- 警方伪造的LINE聊天记录中的"哲也"（Day1上下文）
- 叙事中的"黑羽哲也"全名
- 白鹤姬等角色称呼"哲也"
- 主角内心独白中的"黑羽哲也"
"""

import re

V5_PATH = r"C:\Users\yansongshen\WorkBuddy\2026-06-30-09-30-40\twelve-birds\十二飞鸟_全剧本合集_v5.txt"

with open(V5_PATH, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = []

# ============================================================
# 1. 莉香消息中的 "哲也——" 前缀 → 删除
#    例如: "哲也——你今天为什么不回我消息。" → "你今天为什么不回我消息。"
# ============================================================
# 这些是莉香短信的固定格式，在叙事上下文中
pattern1 = r'莉香[。，\s]*\n+"哲也——'
def replace_zekka_prefix(match):
    prefix = match.group(0)
    new = prefix.replace("哲也——", "")
    return new

# More targeted: find lines with "哲也——" that are in 莉香 message context
# Looking at the actual patterns from grep:
# "哲也——你今天为什么不回我消息。" 
# "哲也——我查了机票..."
# etc.
# These always appear as standalone lines in莉香的 text message context

old_count = content.count("哲也——")
content = content.replace("哲也——", "")
new_count = content.count("哲也——")
if old_count != new_count:
    changes.append(f"  删除 '哲也——' 前缀: {old_count - new_count} 处")

# ============================================================
# 2. 独立的 "……哲也。" → 删除  
#    Day27, Day30 中莉香的低语
# ============================================================
old_count = content.count("……哲也。")
content = content.replace("……哲也。\n", "\n")
new_count = content.count("……哲也。")
if old_count != new_count:
    changes.append(f"  删除 '……哲也。': {old_count - new_count} 处")

# ============================================================
# 3. Day2 L120: 独立行 "哲也。" → 删除
#    Context: 莉香说 "哲也。" 然后说 "你要好好照顾自己啊..."
# ============================================================
# Match: 莉香说完后，单独一行 "哲也。"
old_count = content.count("\n哲也。\n")
content = content.replace("\n哲也。\n", "\n")
new_count = content.count("\n哲也。\n")
if old_count != new_count:
    changes.append(f"  删除独立行 '哲也。': {old_count - new_count} 处")

# ============================================================
# 4. "晚安。哲也。" → "晚安。"
#    Day55_endB, Day57_endA
# ============================================================
old_count = content.count("晚安。哲也。")
content = content.replace("晚安。哲也。", "晚安。")
new_count = content.count("晚安。哲也。")
if old_count != new_count:
    changes.append(f"  '晚安。哲也。' → '晚安。': {old_count - new_count} 处")

# ============================================================
# 5. Day30 事件头: "哲也你是不是出事了" → "你是不是出事了"
# ============================================================
old_count = content.count("哲也你是不是出事了")
content = content.replace("哲也你是不是出事了", "你是不是出事了")
new_count = content.count("哲也你是不是出事了")
if old_count != new_count:
    changes.append(f"  事件头 '哲也你是不是出事了' → '你是不是出事了': {old_count - new_count} 处")

# ============================================================
# 6. "哲也。你是不是有什么事没有告诉我。" → "你是不是有什么事没有告诉我。"
#    Day10
# ============================================================
old_count = content.count("哲也。你是不是有什么事没有告诉我。")
content = content.replace("哲也。你是不是有什么事没有告诉我。", "你是不是有什么事没有告诉我。")
new_count = content.count("哲也。你是不是有什么事没有告诉我。")
if old_count != new_count:
    changes.append(f"  Day10 莉香消息修复: {old_count - new_count} 处")

# ============================================================
# 7. "哲也。你跟我说实话。你那边到底怎么了。" → "你跟我说实话。你那边到底怎么了。"
#    Day30
# ============================================================
old_count = content.count("哲也。你跟我说实话。你那边到底怎么了。")
content = content.replace("哲也。你跟我说实话。你那边到底怎么了。", "你跟我说实话。你那边到底怎么了。")
new_count = content.count("哲也。你跟我说实话。你那边到底怎么了。")
if old_count != new_count:
    changes.append(f"  Day30 莉香消息修复: {old_count - new_count} 处")

# ============================================================
# 8. "哲也。你还会在这里多久。" → "你还会在这里多久。"
#    Day31
# ============================================================
old_count = content.count("哲也。你还会在这里多久。")
content = content.replace("哲也。你还会在这里多久。", "你还会在这里多久。")
new_count = content.count("哲也。你还会在这里多久。")
if old_count != new_count:
    changes.append(f"  Day31 莉香消息修复: {old_count - new_count} 处")

# ============================================================
# 9. "哲也。我今天只占这一次..." → "我今天只占这一次..."
#    Day33
# ============================================================
old_count = content.count("哲也。我今天只占这一次。今天准了——明天就不准了。你信吗。")
content = content.replace("哲也。我今天只占这一次。今天准了——明天就不准了。你信吗。", "我今天只占这一次。今天准了——明天就不准了。你信吗。")
new_count = content.count("哲也。我今天只占这一次。今天准了——明天就不准了。你信吗。")
if old_count != new_count:
    changes.append(f"  Day33 莉香消息修复: {old_count - new_count} 处")

# ============================================================
# Write result
# ============================================================
with open(V5_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("=== v5 全剧本合集 莉香'哲也'红线修复完成 ===")
print(f"文件: {V5_PATH}")
print(f"变更列表:")
for c in changes:
    print(c)
print(f"\n总计修复: {sum(int(c.split(':')[1].strip().split(' ')[0]) for c in changes)} 处")
print("\n验证: 剩余 \"哲也\" 出现次数:", content.count("哲也"))
print("(剩余的应为叙事中的'黑羽哲也'全名、警方伪造记录、白鹤姬等角色称呼)")
