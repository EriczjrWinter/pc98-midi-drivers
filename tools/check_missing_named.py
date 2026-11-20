# -*- coding: utf-8 -*-
"""查「XML 里有、索引里没有」的包是什么情况。"""
import os
import re

INDEX = r'D:\gf\pc98-midi-drivers\build\hoot_index.html'
XMLDIR = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'

idx = open(INDEX, encoding='utf-8', errors='replace').read()
names = set(m.group(1).lower() for m in re.finditer(r'href="([^"]+\.zip)"', idx, re.I))
local = {f[:-4].lower() for f in os.listdir(PC98) if f.lower().endswith('.zip')}

miss = []
for fn in sorted(os.listdir(XMLDIR)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(XMLDIR, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        if not re.search(r'name="midiout"\s+value="1"', b):
            continue
        ar = a.group(1)
        if ar.lower() in local:
            continue
        if (ar + '.zip').lower() not in names:
            miss.append((ar, nm.group(1)[:44], fn[:-4]))

print('索引里确实没有的:', len(miss))
for x in miss[:15]:
    print('   %-16s %-46s %s' % x)

# 看看会不会是以别的后缀存在（比如 .7z / 没有 _98）
print()
print('索引里含该名前缀的条目（前 5 个样本）：')
for ar, nm, co in miss[:5]:
    base = re.sub(r'_98$', '', ar, flags=re.I)
    hit = [n for n in names if base.lower() in n][:5]
    print('   %-14s → %s' % (ar, hit))
