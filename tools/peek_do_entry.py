# -*- coding: utf-8 -*-
import os
import re

H = r'D:\GamedataUnpack\hoot20251231'
t = open(os.path.join(H, 'xml', 'do.xml'), encoding='utf-8', errors='replace').read()

for b in re.split(r'<game>', t):
    a = re.search(r'archive="([^"]+)"', b)
    nm = re.search(r'<name>([^<]+)</name>', b)
    if not a or not nm or a.group(1) not in ('cl_98', 'zatuon_98'):
        continue
    roms = re.findall(r'<rom type="([^"]+)"[^>]*>([^<]+)</rom>', b)
    print('===', nm.group(1))
    print('   rom 数:', len(roms))
    for typ, f in roms[:6]:
        print('     %-10s %s' % (typ, f))
    print('     ...')
    for typ, f in roms[-4:]:
        print('     %-10s %s' % (typ, f))
    print()
