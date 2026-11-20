# -*- coding: utf-8 -*-
"""按关键词在索引里找包名。"""
import re
import sys

IDX = r'D:\gf\pc98-midi-drivers\build\hoot_index.html'
idx = open(IDX, encoding='utf-8', errors='replace').read()
names = re.findall(r'href="([^"]+\.zip)"', idx, re.I)

for kw in ('gao', 'karanon', 'amiyo', 'ekudorado', 'tokio'):
    hit = [n for n in names if kw in n.lower()]
    print('%-12s → %s' % (kw, hit[:8]))
