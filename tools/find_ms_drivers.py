# -*- coding: utf-8 -*-
"""查 HOOT 全库里哪些驱动名字带 MS，以及各自覆盖哪些作品。"""
import os
import re
from collections import defaultdict

H = r'D:\GamedataUnpack\hoot20251231\xml'
local = {f[:-4] for f in os.listdir(r'D:\GamedataUnpack\hoot20251231\pc98')
         if f.lower().endswith('.zip')}

drv_games = defaultdict(set)
drv_local = defaultdict(set)
for fn in sorted(os.listdir(H)):
    if not fn.endswith('.xml'):
        continue
    company = fn[:-4]
    t = open(os.path.join(H, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        if not a:
            continue
        for m in re.finditer(r'<rom type="code"[^>]*>([^<]+)</rom>', b):
            n = m.group(1).strip().upper()
            if n.startswith('MS') or 'MSDRV' in n or n == 'MSP.COM':
                drv_games[n].add(company)
                if a.group(1) in local:
                    drv_local[n].add(a.group(1))

for k in sorted(drv_games):
    print('%-18s 会社=%d  本地包=%d  %s'
          % (k, len(drv_games[k]), len(drv_local[k]),
             ', '.join(sorted(drv_local[k])[:6])))
