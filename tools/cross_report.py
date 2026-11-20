# -*- coding: utf-8 -*-
"""把本地收藏和 HOOT 目录对起来：哪些作品两边都有、哪些只有一边。"""
import json

COLL = r'D:\gf\pc98-midi-drivers\catalog\collection.json'
HOOT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
OUT = r'D:\gf\pc98-midi-drivers\catalog\CROSS.md'

coll = json.load(open(COLL, encoding='utf-8'))
hoot = json.load(open(HOOT, encoding='utf-8'))

by_id = {}
for r in hoot:
    v = r.get('vndb')
    if v:
        by_id[v['id']] = r

both, only_coll = [], []
for c in coll:
    v = c.get('vndb')
    if not v:
        continue
    h = by_id.get(v['id'])
    if h:
        both.append((c, h))
    else:
        only_coll.append(c)

print('收藏里 VNDB 匹配到:', sum(1 for c in coll if c['vndb']))
print('其中 HOOT 里也有 PC-98 MIDI 的:', len(both))
print('收藏有、HOOT 的 PC-98 清单里没有的:', len(only_coll))
print()

L = ['# 本地收藏 × HOOT 对照', '']
L.append('| 项 | 数量 |')
L.append('|---|---|')
L.append('| 收藏目录 | %d |' % len(coll))
L.append('| VNDB 匹配到 | %d |' % sum(1 for c in coll if c['vndb']))
L.append('| 含 MIDI | %d（%d 首） |'
         % (sum(1 for c in coll if c['midi']), sum(c['midi'] for c in coll)))
L.append('| 与 HOOT PC-98 MIDI 重合 | **%d** |' % len(both))
L.append('')

L.append('## 两边都有 MIDI 的作品（%d 部）\n' % len(both))
L.append('这些是**可以直接对照验证**的——同一首曲子，PC-98 驱动出的 vs 现成 MIDI。\n')
L.append('| 作品 | 会社 | 收藏 MIDI | PC-98 驱动 | 平台 |')
L.append('|---|---|---|---|---|')
for c, h in sorted(both, key=lambda x: -x[0]['midi']):
    L.append('| %s | %s | %d | %s | %s |'
             % (c['dir'][:32], h['company'], c['midi'],
                ','.join(h['drivers'])[:24] or '—',
                ' '.join(h['vndb']['platforms'])))
L.append('')

L.append('## 收藏有、但不在 HOOT PC-98 MIDI 清单里的（%d 部）\n' % len(only_coll))
L.append('多半是 PC-98 版没 MIDI、只有 Windows 版有——正是你说的那批反向作品。\n')
L.append('| 目录 | VNDB 标题 | 平台 | MIDI |')
L.append('|---|---|---|---|')
for c in sorted(only_coll, key=lambda x: -x['midi']):
    v = c['vndb']
    L.append('| %s | %s | %s | %d |'
             % (c['dir'][:30], (v['title'] or '')[:26],
                ' '.join(v['platforms']), c['midi']))
L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('写入', OUT)
