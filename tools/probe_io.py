# -*- coding: utf-8 -*-
"""解出某个包里的驱动，跑安装，打印 I/O 序列 —— 用来看它怎么探测硬件。"""
import os
import sys
import tempfile
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')
import mmdr_emu as M

pack = sys.argv[1] if len(sys.argv) > 1 else 'eime_98'
member = sys.argv[2] if len(sys.argv) > 2 else 'MMD.COM'

z = zipfile.ZipFile(os.path.join(H, pack + '.zip'))
data = z.read(member)
p = os.path.join(tempfile.gettempdir(), member.replace('/', '_'))
open(p, 'wb').write(data)

m = M.MMDR(driver=p, verbose=True)
m.load_driver()
ok = m.install()
print('\n安装:', ok, ' 大小:', len(data))
print('I/O 序列:')
for kind, port, val in m.io_log:
    print('   %s 0x%04X %s 0x%02X' % (kind, port, '->' if kind == 'in' else '<-', val))
