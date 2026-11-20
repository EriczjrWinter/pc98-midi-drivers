# -*- coding: utf-8 -*-
"""本地 HOOT 包里已经有哪些 MIDI 驱动（按覆盖的作品数排序）。

逆向一个驱动只需要一个样本，所以这里关心的是「驱动有没有样本」，
而不是「有多少游戏」。
"""
import os
import re
import zipfile
from collections import defaultdict

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')
PDIR = os.path.join(H, 'pc98')

# archive -> (company, game名, 驱动列表, midiout)
arch_info = {}
for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    company = fn[:-4]
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        midiout = re.search(r'name="midiout"\s+value="1"', b) is not None
        roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
        drv = [r.upper() for r in roms if re.match(r'(?i).*\.(com|sys|drv)$', r)]
        arch_info.setdefault(a.group(1), []).append(
            (company, nm.group(1), drv, midiout))

have = defaultdict(lambda: {'archives': set(), 'games': 0, 'companys': set()})
missing = defaultdict(int)
local = [f[:-4] for f in os.listdir(PDIR) if f.lower().endswith('.zip')]
print('本地 pc98 包数量:', len(local))

for arch, entries in arch_info.items():
    if not any(e[3] for e in entries):
        continue
    for company, name, drv, midi in entries:
        for d in drv:
            if os.path.exists(os.path.join(PDIR, arch + '.zip')):
                have[d]['archives'].add(arch)
                have[d]['companys'].add(company)
            else:
                missing[d] += 1

print()
print('%-22s %6s %8s  %s' % ('驱动', '本地样本', '缺的包', '会社'))
print('-' * 86)
for d, v in sorted(have.items(), key=lambda kv: -kv[1]['games']):
    comp = ', '.join(sorted(v['companys'])[:4])
    print('%-22s %6d %8d  %s' % (d, len(v['archives']), missing.get(d, 0), comp[:38]))
