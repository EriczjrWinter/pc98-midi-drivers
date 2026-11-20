# -*- coding: utf-8 -*-
"""把几个包里同名驱动解出来，逐个跑安装，报告：装了什么向量、写了哪些端口。

用来判断「同名不同构建」是否接口兼容。
"""
import os
import struct
import sys
import tempfile
import zipfile

H = r'D:\GamedataUnpack\hoot20251231'
PDIR = os.path.join(H, 'pc98')
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')

import mmdr_emu as M   # 复用它的 16 位骨架

TARGET = (sys.argv[1] if len(sys.argv) > 1 else 'MMD.COM').upper()

tmp = tempfile.mkdtemp(prefix='drv_')
seen = {}
for f in sorted(os.listdir(PDIR)):
    if not f.lower().endswith('.zip'):
        continue
    try:
        z = zipfile.ZipFile(os.path.join(PDIR, f))
    except Exception:
        continue
    for n in z.namelist():
        if n.upper() != TARGET:
            continue
        data = z.read(n)
        key = len(data)
        if key in seen:
            continue
        p = os.path.join(tmp, '%s_%d.com' % (TARGET.split('.')[0], key))
        open(p, 'wb').write(data)
        seen[key] = (f[:-4], p)

for size, (arch, path) in sorted(seen.items()):
    m = M.MMDR(driver=path)
    m.load_driver()
    ok = m.install()
    u = m.uc
    vecs = []
    for v in range(256):
        ip, cs = struct.unpack('<HH', u.mem_read(v * 4, 4))
        if cs == M.PSP_SEG and ip != 0:
            vecs.append((v, ip))
    outports = {k: v for k, v in m.outports.items() if k != 0xE0D0}
    print('%-10s %5d B  来自 %-12s 安装=%s' % (TARGET, size, arch, ok))
    print('   向量:', ', '.join('INT%02X→%04X' % (v, ip) for v, ip in vecs) or '(无)')
    print('   端口:', outports or '(无)')
    print('   MIDI 口(0xE0D0)被写:', m.outports.get(0xE0D0, 0), '次')
    print('   DOS 调用:', [hex(a) for a in m.dos_calls][:24])
    print()
