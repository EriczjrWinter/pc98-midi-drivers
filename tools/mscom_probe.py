# -*- coding: utf-8 -*-
"""扫描 MS.COM：用了哪些中断、哪些端口。"""
import collections
import os
import zipfile

import capstone

H = r'D:\GamedataUnpack\hoot20251231\pc98'
z = zipfile.ZipFile(os.path.join(H, 'filsnown_98.zip'))
d = z.read('MS.COM')
print('MS.COM %d 字节  前16: %s' % (len(d), d[:16].hex(' ')))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

ints = collections.Counter()
ports_out = collections.Counter()
ports_in = collections.Counter()

# 线性扫描（COM 从 0x100 开始）
for insn in md.disasm(d, 0x100):
    if insn.mnemonic == 'int':
        ints[insn.op_str] += 1
    elif insn.mnemonic == 'out':
        ports_out[insn.op_str] += 1
    elif insn.mnemonic == 'in':
        ports_in[insn.op_str] += 1

print('\n中断:')
for k, v in ints.most_common():
    print('   INT %-4s ×%d' % (k, v))
print('\nout 端口:')
for k, v in ports_out.most_common(10):
    print('   %-16s ×%d' % (k, v))
print('\nin 端口:')
for k, v in ports_in.most_common(10):
    print('   %-16s ×%d' % (k, v))

# CD xx 原始字节搜索（线性扫描可能漏）
cd = collections.Counter()
i = 0
while True:
    j = d.find(b'\xcd', i)
    if j < 0:
        break
    cd[d[j + 1] if j + 1 < len(d) else -1] += 1
    i = j + 1
print('\nCD xx 原始统计:')
for k, v in cd.most_common(10):
    print('   CD %02X ×%d' % (k, v))
