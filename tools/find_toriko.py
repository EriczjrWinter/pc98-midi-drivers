# -*- coding: utf-8 -*-
"""在 HOOT XML 里找「虜」。"""
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
hits = 0
for fn in sorted(os.listdir(X)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        nm = re.search(r'<name>([^<]+)</name>', b)
        a = re.search(r'archive="([^"]+)"', b)
        if not nm or not a:
            continue
        if '虜' not in nm.group(1):
            continue
        midi = bool(re.search(r'name="midiout"\s+value="1"', b))
        print('%-14s %-46s %-14s %s'
              % (fn[:-4], nm.group(1)[:44], a.group(1), 'MIDI' if midi else '-'))
        hits += 1
if not hits:
    print('HOOT 里没有「虜」')
