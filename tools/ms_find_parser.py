# -*- coding: utf-8 -*-
"""在 MSDRV4.EXE 里定位音乐数据解析器。"""
import struct
import sys
import zipfile

import capstone

H = r'D:\GamedataUnpack\hoot20251231\pc98'
d = zipfile.ZipFile(H + r'\karanon_98.zip').read('MSDRV4.EXE')
hdr = 0x2C0
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)


def find(pat):
    out = []
    i = 0
    while True:
        j = d.find(pat, i)
        if j < 0:
            break
        out.append(j)
        i = j + 1
    return out


PATS = {
    '3C 8A   cmp al,8Ah (设BPM)': b'\x3c\x8a',
    '3C 9C': b'\x3c\x9c',
    '3C 9E': b'\x3c\x9e',
    '3C E6   cmp al,E6h': b'\x3c\xe6',
    '3C E7': b'\x3c\xe7',
    '3C FE   cmp al,FEh': b'\x3c\xfe',
    '3C 80   cmp al,80h': b'\x3c\x80',
    '2C 80   sub al,80h': b'\x2c\x80',
    'AC      lodsb': b'\xac',
}

for lab, pat in PATS.items():
    hits = [h for h in find(pat) if h >= hdr]
    print('%-32s %3d 处  %s' % (lab, len(hits),
                                ' '.join(hex(h) for h in hits[:10])))
print()


def ctx(off, back=12, fwd=28):
    print('--- 0x%05X ---' % off)
    seg = 0x1E + (off - hdr) // 16
    ip = (off - hdr) % 16
    start = max(hdr, off - back)
    code = d[start:off + fwd]
    for insn in md.disasm(code, 0):
        mark = '  <<<' if start + insn.address == off else ''
        print('  %04X  %-20s %s %s%s' % (start + insn.address,
                                         insn.bytes.hex(' '),
                                         insn.mnemonic, insn.op_str, mark))


for pat in (b'\x3c\x8a', b'\x3c\xfe'):
    for h in [x for x in find(pat) if x >= hdr][:3]:
        ctx(h)
        print()
