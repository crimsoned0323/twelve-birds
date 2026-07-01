"""
十二飞鸟剧本：句号当逗号用 — 批量修复脚本 v2

修复规则：
1. 处理旁白段落和角色台词内容行（包括与标签分行的内容行）
2. 在单行内，将所有非最后一个「。」改为「，」
   例外：如果「。」后面的文字以转折词开头，保留「。」
3. 转折词：但/但是/然而/不过/可是/只是/其实/原来/没想到/忽然/突然等
4. 不改变行尾最后一个「。」（段落结束标记）
5. 不改变只有1个「。」的行（已是完整句子）

v2修复：正确追踪对话块（角色标签后的分行内容行也需要处理）
"""

import os

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '文字剧本')

SHIFT_WORDS = [
    '但', '但是', '然而', '不过', '可是', '只是', '其实', '原来', 
    '没想到', '忽然', '突然', '终于', '至少', '毕竟', '反而', '果然',
    '因此', '所以', '结果', '要么', '要么是', '幸亏', '还好', '可惜',
    '不料', '谁知道', '偏偏', '至于', '话说', '对了', '说起来',
]

SKIP_PREFIXES = ['====', '  ', '#', '※', '▶', '●', '◇', '「', '『', '—']

def fix_periods_in_line(content):
    """修复一行内的句号当逗号用问题"""
    period_positions = [i for i, ch in enumerate(content) if ch == '。']
    
    if len(period_positions) <= 1:
        return content, 0
    
    changes = 0
    result = list(content)
    
    for pos in period_positions[:-1]:
        after_text = content[pos+1:].strip()
        
        should_preserve = any(after_text.startswith(w) for w in SHIFT_WORDS)
        
        if not should_preserve:
            result[pos] = '，'
            changes += 1
    
    return ''.join(result), changes

def classify_line(stripped):
    """
    返回 (type, info)
    type: 'tag_only', 'tag_with_content', 'content_line', 'skip'
    info: tag_name if tag, None otherwise
    """
    if not stripped:
        return 'empty', None
    
    if any(stripped.startswith(p) for p in SKIP_PREFIXES):
        return 'skip', None
    
    if stripped.startswith('【') and '】' in stripped:
        bracket_end = stripped.index('】')
        tag_name = stripped[1:bracket_end]  # e.g., "旁白", "我", "前台值班"
        content_after = stripped[bracket_end+1:].strip()
        
        if content_after:
            return 'tag_with_content', (tag_name, content_after)
        else:
            return 'tag_only', tag_name
    
    # 不以【开头的行 — 是内容行
    # 判断是否应该处理：长度>3，不是纯数字/标题
    if len(stripped) >= 3:
        return 'content_line', None
    
    return 'skip', None

def process_file(filepath):
    """处理单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_changes = 0
    changed_lines = []
    
    # 当前所在的块类型：None / 'narration' / 'dialogue'
    current_block = None
    
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        
        line_type, info = classify_line(stripped)
        
        if line_type == 'empty':
            # 空行：保持原样，不结束块（因为有些块内有空行）
            new_lines.append(line)
            continue
        
        if line_type == 'skip':
            # 标题/场景标注等：保持原样
            current_block = None
            new_lines.append(line)
            continue
        
        if line_type == 'tag_only':
            # 纯标签行：【旁白】、【角色名】等（无内容）
            tag_name = info
            if tag_name == '旁白':
                current_block = 'narration'
            else:
                current_block = 'dialogue'
            new_lines.append(line)
            continue
        
        if line_type == 'tag_with_content':
            # 标签+内容行：【旁白】内容 或 【角色名】台词
            tag_name, content = info
            if tag_name == '旁白':
                current_block = 'narration'
            else:
                current_block = 'dialogue'
            
            fixed_content, changes = fix_periods_in_line(content)
            total_changes += changes
            if changes > 0:
                changed_lines.append((i+1, stripped[:10], content[:20], fixed_content[:20]))
            
            new_lines.append(indent + stripped[:stripped.index('】')+1] + ' ' + fixed_content + '\n')
            continue
        
        if line_type == 'content_line':
            # 内容行（无标签前缀）— 根据当前块类型决定是否处理
            if current_block in ('narration', 'dialogue'):
                fixed_content, changes = fix_periods_in_line(stripped)
                total_changes += changes
                if changes > 0:
                    changed_lines.append((i+1, 'content', stripped[:20], fixed_content[:20]))
                
                new_lines.append(indent + fixed_content + '\n')
            else:
                # 不在任何块中 — 保持原样（可能是标题/注释等）
                new_lines.append(line)
            continue
        
        # fallback
        new_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return total_changes, changed_lines

def main():
    print('=== 十二飞鸟 · 句号当逗号用 · 批量修复 v2 ===')
    print()
    
    files = sorted([f for f in os.listdir(SCRIPT_DIR) if f.endswith('.txt')])
    
    total_files = 0
    total_changes_all = 0
    file_stats = []
    
    for fname in files:
        filepath = os.path.join(SCRIPT_DIR, fname)
        changes, changed_lines = process_file(filepath)
        
        if changes > 0:
            total_files += 1
            total_changes_all += changes
            file_stats.append((fname, changes, len(changed_lines)))
    
    file_stats.sort(key=lambda x: -x[1])
    
    print(f'处理文件数: {total_files}/{len(files)}')
    print(f'新增句号→逗号: {total_changes_all}')
    print()
    
    print('=== 新增修改量（前10）===')
    for fname, changes, lines_count in file_stats[:10]:
        print(f'  {fname:30s} | +{changes:3d}处句号→逗号')
    
    print()
    print(f'✅ v2补修完成！新增 {total_changes_all} 处「。」→「，」')

if __name__ == '__main__':
    main()
