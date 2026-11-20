# -*- coding: utf-8 -*-
"""诊断：逐轨打印解析到哪、算出多长。"""
import struct
import sys
import zipfile

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\msdrv\src')
import ms_parser as M

H = r'D:\GamedataUnpack\hoot20251231\pc98'

name = sys.argv[1] if len(sys.argv) > 1 else 'MD_08_GS.MS'
z = zipfile.ZipFile(H + r'\karanon_98.zip')
d = z.read(name)
table = M.read_table(d)
print('%s  %d 字节  %d 条轨' % (name, len(d), len(table)))
print('%-4s %-8s %-8s %-8s %7s %6s %s' % ('轨', '起点', '上限', '结束处', '最大tick', '音符', '警告'))
for k, (idx, off) in enumerate(table):
    limit = table[k + 1][1] if k + 1 < len(table) else len(d)
    ev, tp, wn = M.parse_track(d, off, idx & 0x0F, limit=limit)
    mx = max((t for t, _, _, _ in ev), default=0)
    notes = sum(1 for e in ev if e[1] == 'on')
    print('%-4d 0x%04X   0x%04X   —        %7d %6d %s'
          % (idx, off, limit, mx, notes, wn[:2] if wn else ''))
