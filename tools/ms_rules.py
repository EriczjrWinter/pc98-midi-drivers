# -*- coding: utf-8 -*-
"""比较几种掩码规则，看哪种未知命令最少。"""
import collections
import struct
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'


def scan(data, off, mask_test):
    pos = off
    buf = [0, 0, 0, 0]
    n = len(data)
    cnt = collections.Counter()
    steps = 0
    while pos < n and steps < 60000:
        steps += 1
        cmd = data[pos]
        pos += 1
        if mask_test(cmd):
            if cmd & 0x08:
                buf[0] = data[pos] if pos < n else 0; pos += 1
            if cmd & 0x04:
                buf[1] = data[pos] if pos < n else 0; pos += 1
            if cmd & 0x02:
                buf[2] = data[pos] if pos < n else 0; pos += 1
            if cmd & 0x01:
                buf[3] = data[pos] if pos < n else 0; pos += 1
        else:
            buf[0] = cmd
            for k in (1, 2, 3):
                buf[k] = data[pos] if pos < n else 0
                pos += 1
        c0 = buf[0]
        if c0 == 0xFE:
            cnt['FE'] += 1
            break
        if c0 < 0x80:
            cnt['音符'] += 1
        elif c0 == 0xE6:
            cnt['E6'] += 1
        elif c0 == 0xE7:
            cnt['E7'] += 1
        elif (c0 & 0xF8) in (0xE8, 0xD8):
            cnt['%02X' % (c0 & 0xF0)] += 1
        elif 0x90 <= c0 <= 0x9F:
            cnt['9x单字节'] += 1
        else:
            cnt['未知%02X' % c0] += 1
    return cnt


RULES = {
    'A 只有 0x80-0x8F': lambda c: 0x80 <= c <= 0x8F,
    'B 0x80-0x8F + 0x90-0x97': lambda c: 0x80 <= c <= 0x8F or 0x90 <= c <= 0x97,
    'C 0x80-0x8F + 0x90-0x9F': lambda c: 0x80 <= c <= 0x8F or 0x90 <= c <= 0x9F,
}

z = zipfile.ZipFile(H + r'\karanon_98.zip')
for name in ('MD_04_GS.MS', 'MD_01_GS.MS'):
    d = z.read(name)
    print('===', name, len(d), '字节')
    for label, test in RULES.items():
        tot = collections.Counter()
        offs = [struct.unpack_from('<I', d, i * 4)[0] for i in range(36)]
        for i, off in enumerate(offs):
            if not (0 < off < len(d)):
                continue
            tot.update(scan(d, off, test))
        unk = sum(v for k, v in tot.items() if k.startswith('未知'))
        print('  %-26s 音符=%-5d 未知合计=%-4d %s' % (
            label, tot.get('音符', 0), unk,
            dict((k, v) for k, v in tot.most_common(8) if k.startswith('未知'))))
    print()
