# -*- coding: utf-8 -*-
"""看 D.O. 系其余包用的是哪个驱动文件。"""
import collections
import json
import os
import re
import zipfile

PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
X = r'D:\GamedataUnpack\hoot20251231\xml'
CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'

rows = json.load(open(CAT, encoding='utf-8'))
archives = set()
for r in rows:
    if r['company'] in ('do', 'foster', 'zyx'):
        archives.update(r['archives'])

# 从 XML 里拿每个包的 code rom 名
code = {}
for company in ('do', 'foster', 'zyx'):
    t = open(os.path.join(X, company + '.xml'), encoding='utf-8',
             errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        if not a:
            continue
        roms = re.findall(r'<rom type="code"[^>]*>([^<]+)</rom>', b)
        if roms:
            code.setdefault(a.group(1), set()).update(roms)

print('包 → code rom:')
for a in sorted(archives):
    roms = sorted(code.get(a, []))
    print('  %-14s %s' % (a, ', '.join(roms) if roms else '(XML 里没有 code rom)'))

print('\n按 code rom 聚合:')
c = collections.Counter()
for a in archives:
    for r in code.get(a, []):
        c[r.upper()] += 1
for k, v in c.most_common():
    print('  %-18s %d 个包' % (k, v))
