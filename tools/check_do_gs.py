# -*- coding: utf-8 -*-
"""列出 do 里带 GS 的条目，确认那些数字是"作品"还是"同作品的多个条目"。"""
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
t = open(os.path.join(X, 'do.xml'), encoding='utf-8', errors='replace').read()

rows = []
for b in re.split(r'<game>', t):
    nm = re.search(r'<name>([^<]+)</name>', b)
    a = re.search(r'archive="([^"]+)"', b)
    if not nm or not a:
        continue
    if '(GS)' not in nm.group(1):
        continue
    midi = bool(re.search(r'name="midiout"\s+value="1"', b))
    rows.append((nm.group(1), a.group(1), midi))

print('do 里带 GS 的条目:', len(rows))
for name, arch, midi in rows:
    print('   %-48s %-14s %s' % (name[:46], arch, 'MIDI' if midi else '-'))

from collections import Counter
c = Counter(a for _, a, _ in rows)
print('\n按 archive 聚合（同一作品多个条目）:')
for k, v in c.most_common():
    print('   %-16s %d 个条目' % (k, v))
