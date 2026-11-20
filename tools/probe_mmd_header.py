# -*- coding: utf-8 -*-
"""按 Devi Acker 文档的布局，验证 .MMD 头部结构。"""
import os
import struct
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'

pack = sys.argv[1] if len(sys.argv) > 1 else 'eime_98'
z = zipfile.ZipFile(os.path.join(H, pack + '.zip'))
mmds = [n for n in z.namelist() if n.upper().endswith('.MMD')][:3]
if not mmds:
    print('这个包里没有 .MMD')
    sys.exit()

for name in mmds:
    d = z.read(name)
    bpm = d[0]
    tr = struct.unpack('b', d[1:2])[0]
    print('【%s】 %d 字节' % (name, len(d)))
    print('   bpm=%d  transpose=%d' % (bpm, tr))
    for i in range(16):
        off, key, ch = struct.unpack_from('<HBB', d, 2 + 4 * i)
        k = key if key <= 64 else key - 128
        print('   轨%2d  off=0x%04X  key=%4d  ch=%2d' % (i, off, k, ch))
    title = d[0x50:].split(b'\x00')[0]
    print('   曲名:', title.decode('ascii', 'replace'))
    print()
