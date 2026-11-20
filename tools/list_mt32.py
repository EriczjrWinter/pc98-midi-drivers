# -*- coding: utf-8 -*-
"""列出 do / zyx / foster 等会社里带 MT-32 / GS 变体的作品，并标出本地有没有包。"""
import os
import re

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')
PDIR = os.path.join(H, 'pc98')
local = {f[:-4] for f in os.listdir(PDIR) if f.lower().endswith('.zip')}

for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    rows = []
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        name = nm.group(1)
        if 'MT-32' not in name and '(GS)' not in name:
            continue
        mark = '【本地】' if a.group(1) in local else ''
        rows.append((name, a.group(1), mark))
    if rows:
        print('===', fn[:-4])
        for name, arch, mark in rows:
            print('   %-44s %-16s %s' % (name[:42], arch, mark))
