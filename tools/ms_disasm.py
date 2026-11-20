# -*- coding: utf-8 -*-
"""反汇编 MSDRV4.EXE 的关键片段。"""
import struct
import sys
import zipfile

import capstone

H = r'D:\GamedataUnpack\hoot20251231\pc98'
d = zipfile.ZipFile(H + r'\karanon_98.zip').read('MSDRV4.EXE')
hdr = 0x2C0
cs = 0x1E

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
md.detail = False


def dis(off, count=40):
    base = hdr
    seg = cs + (off - base) // 16
    ip0 = (off - base) % 16
    print('--- 文件 0x%05X  %04X:%04X ---' % (off, seg, ip0))
    code = d[off:off + 200]
    n = 0
    for insn in md.disasm(code, (seg << 4) + ip0 if False else 0):
        print('  %04X  %-22s %s %s' % (insn.address, insn.bytes.hex(' '),
                                       insn.mnemonic, insn.op_str))
        n += 1
        if n >= count:
            break


if __name__ == '__main__':
    start = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1B00
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    dis(start, count)
