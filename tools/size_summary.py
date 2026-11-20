# -*- coding: utf-8 -*-
"""算整个 pc98 索引的总大小、以及去掉本地已有的之后还剩多少。"""
import os
import re

IDX = r'D:\gf\pc98-midi-drivers\build\hoot_index.html'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
UNIT = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}

t = open(IDX, encoding='utf-8', errors='replace').read()
rows = []
for m in re.finditer(
        r'href="([^"]+\.zip)"[^>]*>[^<]*</a>\s*[\d-]+\s+[\d:]+\s+([\d.]+)\s*([KMG]?)',
        t, re.I):
    rows.append((m.group(1), float(m.group(2)) * UNIT.get(m.group(3).upper() or 'B', 1)))

local = {f[:-4].lower() for f in os.listdir(PC98) if f.lower().endswith('.zip')}
tot = sum(s for _, s in rows)
missing = [(n, s) for n, s in rows if n[:-4].lower() not in local]
mtot = sum(s for _, s in missing)

print('索引包数 %d   合计 %.1f MB' % (len(rows), tot / 1024 / 1024))
print('本地已有 %d' % len(local))
print('还缺 %d 个   合计 %.1f MB' % (len(missing), mtot / 1024 / 1024))

# 大小分布
big = sorted(missing, key=lambda x: -x[1])[:10]
print('\n最大的 10 个:')
for n, s in big:
    print('   %-24s %8.1f KB' % (n, s / 1024))
