# -*- coding: utf-8 -*-
"""看对不上的包分别属于哪些机种。"""
import collections
import json
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
ZIPS = {f[:-4].lower() for f in
        os.listdir(r'D:\GamedataUnpack\hoot20251231\pc98')
        if f.lower().endswith('.zip')}
MP = json.load(open(r'D:\gf\pc98-midi-drivers\build\rename_map.json',
                    encoding='utf-8'))

miss = []
for fn in sorted(os.listdir(X)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        if not re.search(r'name="midiout"\s*value="1"', b):
            continue
        ar = a.group(1)
        if ar.lower() in ZIPS or ar in MP:
            continue
        miss.append((ar, nm.group(1)))

c = collections.Counter()
for ar, nm in miss:
    m = re.match(r'\[([^\]]+)\]', nm)
    c[m.group(1) if m else '?'] += 1

print('对不上且未解析:', len(miss))
for k, v in c.most_common(10):
    print('   %-14s %d' % (k, v))
print()
print('其中标记为 PC-98 的:')
for ar, nm in miss:
    if nm.startswith('[PC-98'):
        print('   %-18s %s' % (ar, nm[:50]))
