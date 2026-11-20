# -*- coding: utf-8 -*-
"""看 archive 以 _21 结尾的条目都属于哪些机种。"""
import collections
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
c = collections.Counter()
ex = []
tot = 0

for fn in sorted(os.listdir(X)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        if not re.search(r'_21$', a.group(1)):
            continue
        tot += 1
        m = re.match(r'\[([^\]]+)\]', nm.group(1))
        c[m.group(1) if m else '?'] += 1
        if len(ex) < 8:
            ex.append((a.group(1), nm.group(1)[:46]))

print('archive 以 _21 结尾的条目:', tot)
for k, v in c.most_common():
    print('   %-14s %d' % (k, v))
print()
for a, n in ex:
    print('   %-18s %s' % (a, n))
