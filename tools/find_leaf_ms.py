# -*- coding: utf-8 -*-
"""精确找 雀鬼 / Filsnown。"""
import os
import re

H = r'D:\GamedataUnpack\hoot20251231\xml'
KEYS = ('雀鬼', 'Filsnown', 'FILS', 'ふぃるす')

for fn in sorted(os.listdir(H)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(H, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        nm = re.search(r'<name>([^<]+)</name>', b)
        a = re.search(r'archive="([^"]+)"', b)
        if not nm or not a:
            continue
        name = nm.group(1)
        if not any(k in name or k in name.upper() for k in KEYS):
            continue
        roms = re.findall(r'<rom type="code"[^>]*>([^<]+)</rom>', b)
        print('%-14s %-42s %s' % (a.group(1), name[:40], roms[:3]))
