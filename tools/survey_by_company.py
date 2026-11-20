# -*- coding: utf-8 -*-
"""按会社汇总 HOOT 里「带 MIDI 输出」的作品。

XML 文件名即会社/分类。输出：会社 → 作品数 + 用到的驱动。
"""
import os
import re
from collections import Counter, defaultdict

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')

summary = []
for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    company = fn[:-4]
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    n = 0
    drv = Counter()
    for b in re.split(r'<game>', t):
        if not re.search(r'name="midiout"\s+value="1"', b):
            continue
        if not re.search(r'<name>', b):
            continue
        n += 1
        roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
        for r in roms:
            if re.match(r'(?i).*\.(com|sys|drv)$', r):
                drv[r.upper()] += 1
    if n:
        summary.append((company, n, drv))

summary.sort(key=lambda x: -x[1])
print('%-16s %5s  %s' % ('会社(XML)', '作品', '驱动（按出现次数）'))
print('-' * 96)
for company, n, drv in summary:
    top = ', '.join('%s×%d' % (k, v) for k, v in drv.most_common(4))
    print('%-16s %5d  %s' % (company, n, top[:70]))
