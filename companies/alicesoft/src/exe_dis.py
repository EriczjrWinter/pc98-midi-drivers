# -*- coding: utf-8 -*-
"""system3.exe 反汇编小工具：把指定 VA 范围反汇编成可读清单。"""
import sys
import struct
import capstone

EXE = r"D:\Galgame\PC98-DOS-WIN95\GAME\AMBIVALENZ\system3.exe"

SECS = [
    ('.text', 0x1000, 0x1B000, 0x1000),
    ('.rdata', 0x1C000, 0x3000, 0x1C000),
    ('.data', 0x1F000, 0x5900, 0x1F000),
    ('.rsrc', 0x25000, 0x1B210, 0x24000),
]
IMAGE_BASE = 0x400000


def load():
    return open(EXE, 'rb').read()


def va2off(va):
    if va >= IMAGE_BASE:
        va -= IMAGE_BASE
    for nm, va0, size, raw in SECS:
        if va0 <= va < va0 + size:
            return raw + (va - va0)
    return None


def disasm(va, nbytes, base_va=None):
    d = load()
    o = va2off(va)
    code = d[o:o + nbytes]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    out = []
    for ins in md.disasm(code, va):
        out.append('%06X  %-24s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('usage: dis.py VA [LEN]')
        sys.exit(1)
    va = int(sys.argv[1], 16)
    ln = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x100
    for line in disasm(va, ln):
        print(line)
