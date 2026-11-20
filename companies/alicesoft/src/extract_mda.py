# -*- coding: utf-8 -*-
"""从 system3.exe 的 .rsrc 里导出 MDA 音色库资源，并初步看格式。"""
from __future__ import annotations
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import exe_dis

OUT = os.path.join(HERE, 'mda')
RSRC_RVA = 0x25000
RSRC_RAW = 0x24000


def R2O(r):
    return RSRC_RAW + (r - RSRC_RVA)


def walk(d, off, path, out):
    chars, ts, mj, mn, named, ids = struct.unpack_from('<IIHHHH', d, off)
    for i in range(named + ids):
        e = off + 16 + i * 8
        name, off2 = struct.unpack_from('<II', d, e)
        if name & 0x80000000:
            so = R2O(RSRC_RVA + (name & 0x7FFFFFFF))
            ln = struct.unpack_from('<H', d, so)[0]
            nm = d[so + 2:so + 2 + ln * 2].decode('utf-16le')
        else:
            nm = '#%d' % name
        if off2 & 0x80000000:
            walk(d, R2O(RSRC_RVA + (off2 & 0x7FFFFFFF)), path + [nm], out)
        else:
            de = R2O(RSRC_RVA + off2)
            rva, size, cp = struct.unpack_from('<III', d, de)
            out.append(('/'.join(path + [nm]), R2O(rva), size))


def main():
    d = exe_dis.load()
    out = []
    walk(d, R2O(RSRC_RVA), [], out)
    os.makedirs(OUT, exist_ok=True)
    print('%-34s %8s  %s' % ('resource', 'size', 'head'))
    for name, off, size in out:
        data = d[off:off + size]
        print('%-34s %8d  %s' % (name, size, data[:32].hex(' ')))
        if name.startswith('MDA'):
            rid = name.split('/')[1].lstrip('#')
            open(os.path.join(OUT, 'mda%s.bin' % rid), 'wb').write(data)
    # 引擎里保存"游戏 ID"的全局
    for g in (0x4230bc,):
        o = exe_dis.va2off(g)
        print('global 0x%X = %s' % (g, d[o:o + 4].hex(' ')))


if __name__ == '__main__':
    main()
