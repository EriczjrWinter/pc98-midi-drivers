# -*- coding: utf-8 -*-
"""从 VGMRips 缓存页里抽时长（data-duration 属性，单位秒）。"""
import glob
import re

SPILL = glob.glob(r'C:\Users\ericz\AppData\Local\Temp\dsh-spill-*\session-*\*.txt')
seen = {}
for p in SPILL:
    t = open(p, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'data-duration="([\d.]+)"\s+data-order="(\d\d)"', t):
        d, n = float(m.group(1)), int(m.group(2))
        seen.setdefault(n, d)
if not seen:
    # 属性顺序可能相反
    for p in SPILL:
        t = open(p, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'data-order="(\d\d)"[^>]*?data-duration="([\d.]+)"', t):
            seen.setdefault(int(m.group(1)), float(m.group(2)))
print('抽到', len(seen), '首')
for n in sorted(seen)[:6]:
    print('  %02d %.1f 秒' % (n, seen[n]))
