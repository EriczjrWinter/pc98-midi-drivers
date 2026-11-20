# -*- coding: utf-8 -*-
"""生成作品目录：一行一个作品，标出 PC-98 侧有没有 MIDI、用什么驱动。

Win 侧的状态留空，等外部信息补（用户的收藏、VGMrips、GOG 等）。

输出 catalog/games.json
"""
import json
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
OUT = r'D:\gf\pc98-midi-drivers\catalog\games.json'
DRV_EXT = re.compile(r'.*\.(COM|SYS|DRV|EXE)$', re.I)


def clean(title):
    """去掉 [系统] 前缀和 (音源) 后缀，得到作品名。"""
    t = re.sub(r'^\[[^\]]*\]\s*', '', title)
    t = re.sub(r'\s*\((?:OPN|OPNA|GS|MT-32[^)]*|SC-88[^)]*|86|SB16|CM-64|GM|FM)\)\s*$',
               '', t, flags=re.I)
    return t.strip()


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    games = {}

    for fn in sorted(os.listdir(X)):
        if not fn.endswith('.xml'):
            continue
        company = fn[:-4]
        t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
        for b in re.split(r'<game>', t):
            a = re.search(r'archive="([^"]+)"', b)
            nm = re.search(r'<name>([^<]+)</name>', b)
            if not a or not nm:
                continue
            title = nm.group(1)
            sysm = re.match(r'\[([^\]]+)\]', title)
            system = sysm.group(1) if sysm else ''
            base = clean(title)
            midi = bool(re.search(r'name="midiout"\s+value="1"', b))
            srcs = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
            drivers = [s for s in srcs if DRV_EXT.match(s)]

            key = (company, base)
            g = games.setdefault(key, {
                'title': base,
                'company': company,
                'systems': set(),
                'pc98_midi': False,
                'archives': set(),
                'drivers': set(),
                'variants': set(),
            })
            g['systems'].add(system)
            g['archives'].add(a.group(1))
            if midi and 'PC-98' in system:
                g['pc98_midi'] = True
                g['drivers'].update(d.upper() for d in drivers)
                m = re.search(r'\(([^)]+)\)\s*$', title)
                if m:
                    g['variants'].add(m.group(1))

    rows = []
    for (company, _), g in sorted(games.items()):
        rows.append({
            'title': g['title'],
            'company': g['company'],
            'systems': sorted(g['systems']),
            'pc98_midi': g['pc98_midi'],
            'variants': sorted(g['variants']),
            'archives': sorted(g['archives']),
            'drivers': sorted(g['drivers']),
            'win_midi': None,          # 待补：true / false / null
            'source': None,            # 待补：Win 版来源
            'status': 'A' if g['pc98_midi'] else '',
        })

    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n_midi = sum(1 for r in rows if r['pc98_midi'])
    print('作品总数:', len(rows))
    print('PC-98 有 MIDI 的:', n_midi)
    print('写入', OUT)

    # 按驱动分组，看看每个驱动对应哪些作品
    from collections import Counter
    c = Counter()
    for r in rows:
        if r['pc98_midi']:
            for d in r['drivers']:
                c[d] += 1
    print('\n驱动分布（前 10）:')
    for k, v in c.most_common(10):
        print('   %-18s %d' % (k, v))


if __name__ == '__main__':
    main()
