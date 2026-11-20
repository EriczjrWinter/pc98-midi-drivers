# -*- coding: utf-8 -*-
"""统计 HOOT 里每个 MIDI 驱动被多少「作品 / 会社」复用。

复用度越高，实现一次的收益越大。
"""
import os
import re
from collections import defaultdict

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')

FMS = re.compile(r'(?i)(fmp|fmdx|fmp2|fmp3|fmx|pmd|ogg|mml)', )

by_driver = defaultdict(lambda: {'games': set(), 'companys': set()})

for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    company = fn[:-4]
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        if not re.search(r'name="midiout"\s+value="1"', b):
            continue
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not nm:
            continue
        roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
        for r in roms:
            up = r.upper()
            if not re.match(r'.*(\.COM|\.SYS|\.DRV)$', up):
                continue
            if re.search(r'(?i)(hd|main|bin)', up) and not up.endswith('.COM'):
                continue
            by_driver[up]['games'].add(nm.group(1))
            by_driver[up]['companys'].add(company)

rows = sorted(by_driver.items(), key=lambda kv: -len(kv[1]['games']))
print('%-22s %5s %5s  %s' % ('驱动', '作品', '会社', '会社例'))
print('-' * 96)
for drv, d in rows[:32]:
    if len(d['games']) < 3:
        break
    comp = ', '.join(sorted(d['companys'])[:5])
    print('%-22s %5d %5d  %s' % (drv, len(d['games']), len(d['companys']), comp[:46]))
