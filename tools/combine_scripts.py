import os, re

script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '文字剧本')
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '十二飞鸟_全剧本合集.txt')

def sort_key(name):
    m = re.match(r'Day(\d+)', name)
    if m:
        day = int(m.group(1))
        if '_endA' in name:
            return (day, 1, 0)
        elif '_endB' in name:
            return (day, 1, 1)
        else:
            return (day, 0, 0)
    return (999, 0, 0)

files = sorted([f for f in os.listdir(script_dir) if f.endswith('.txt') and f.startswith('Day')], key=sort_key)

total_size = 0
with open(output_file, 'w', encoding='utf-8') as out:
    out.write('=' * 60 + '\n')
    out.write(u'  \u300c\u5341\u4e8c\u98db\u9ce5\u300d\u5168\u5287\u672c\u5408\u96c6\n')
    out.write('  \u751f\u6210\u6642\u9593: 2026-06-28\n')
    out.write('  \u5171 ' + str(len(files)) + ' \u500b\u5287\u672c\u6a94\n')
    out.write('=' * 60 + '\n\n')

    for f in files:
        fpath = os.path.join(script_dir, f)
        size = os.path.getsize(fpath)
        total_size += size
        sep = '#' * 60
        out.write('\n' + sep + '\n')
        out.write('#  ' + f + '\n')
        out.write(sep + '\n\n')
        with open(fpath, 'r', encoding='utf-8') as inf:
            out.write(inf.read())
        out.write('\n\n')

    # Footer
    total_mb = total_size / (1024 * 1024)
    out.write('\n' + '=' * 60 + '\n')
    out.write(f'  \u5408\u96c6\u5b8c\u6210 | {len(files)} \u6587\u4ef6 | {total_mb:.2f} MB\n')
    out.write('=' * 60 + '\n')

total_mb = total_size / (1024 * 1024)
print(f'Done. {len(files)} files -> {output_file} ({total_mb:.2f} MB)')
