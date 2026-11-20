# -*- coding: utf-8 -*-
"""把 .MS（黒パッケージ MSDRV4）当 MMD 命令流解析，验证同源性。"""
import collections
import os
import struct
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\mmd\src')
import mmd_parser as P


def tracks(d):
    """读 40 项偏移表，返回 [(序号, 偏移)]，跳过 0 和文件末尾。"""
    out = []
    for i in range(40):
        if i * 4 + 4 > len(d):
            break
        v = struct.unpack_from('<I', d, i * 4)[0]
        if 0 < v < len(d):
            out.append((i, v))
    return out


def scan(d, off):
    """只统计命令种类，判断是不是 MMD 家族。"""
    pos = off
    buf = [0, 0, 0, 0]
    cnt = collections.Counter()
    n = len(d)
    guard = 0
    while pos < n and guard < 100000:
        guard += 1
        cmd = d[pos]; pos += 1
        if (cmd & 0xF0) == 0x80:
            for bit, k in ((0x08, 0), (0x04, 1), (0x02, 2), (0x01, 3)):
                if cmd & bit:
                    buf[k] = d[pos] if pos < n else 0
                    pos += 1
        else:
            buf[0] = cmd
            for k in (1, 2, 3):
                buf[k] = d[pos] if pos < n else 0
                pos += 1
        c0 = buf[0]
        if c0 == 0xFE:
            cnt['FE 结束'] += 1
            break
        if c0 < 0x80:
            cnt['音符'] += 1
        elif c0 == 0xE7:
            cnt['E7 变速'] += 1
        elif c0 == 0xE6:
            cnt['E6 轨选'] += 1
        elif (c0 & 0xF8) in (0xE8, 0xD8):
            cnt['%02X 消息' % (c0 & 0xF0)] += 1
        elif c0 == 0x9E:
            cnt['9E'] += 1
        else:
            cnt['未知 %02X' % c0] += 1
    return cnt


pack = 'karanon_98'
z = zipfile.ZipFile(os.path.join(H, pack + '.zip'))
for name in ('MD_01_GS.MS', 'MD_02_GS.MS', 'MD_01_88.MS'):
    d = z.read(name)
    ts = tracks(d)
    print('=== %s  %d 字节  %d 条轨' % (name, len(d), len(ts)))
    total = collections.Counter()
    for i, off in ts[:6]:
        c = scan(d, off)
        total.update(c)
        print('   轨%2d @0x%04X  %s' % (i, off, dict(c.most_common(6))))
    print()
