# -*- coding: utf-8 -*-
"""统计：MIDI 驱动有多少个、本地样本覆盖多少。"""
import collections
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
local = {f[:-4].lower() for f in os.listdir(PC98) if f.lower().endswith('.zip')}

drv_games = collections.defaultdict(set)
drv_local = collections.defaultdict(set)
games = set()

for fn in os.listdir(X):
    if not fn.endswith('.xml'):
        continue
    co = fn[:-4]
    t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        if not a:
            continue
        if not re.search(r'name="midiout"\s+value="1"', b):
            continue
        games.add(a.group(1))
        for m in re.finditer(r'<rom type="code"[^>]*>([^<]+)</rom>', b):
            n = m.group(1).strip().upper()
            drv_games[n].add(co)
            if a.group(1).lower() in local:
                drv_local[n].add(a.group(1))

print('MIDI 作品总数:', len(games))
print('不同的驱动文件（含桩）:', len(drv_games))
print('其中有本地样本的:', sum(1 for k in drv_games if drv_local[k]))
print('无样本的驱动:', sum(1 for k in drv_games if not drv_local[k]))

print('\n覆盖最广的 12 个:')
for k, v in sorted(drv_games.items(), key=lambda x: -len(x[1]))[:12]:
    print('   %-16s %3d 家   本地 %2d 个包' % (k, len(v), len(drv_local[k])))
