# -*- coding: utf-8 -*-
"""用 VGZ 的时长和我们导出的 MIDI 时长做匹配，建立专辑曲名 ↔ MMD 编号的对应。

VGZ 是 gzip 压缩的 VGM，头部 0x18 处是总采样数（44100Hz）。
"""
import glob
import gzip
import os
import struct
import sys

import mido


def vgz_seconds(path):
    raw = gzip.open(path, 'rb').read()
    if raw[:4] != b'Vgm ':
        return None, None, None
    total = struct.unpack_from('<I', raw, 0x18)[0]
    loop = struct.unpack_from('<I', raw, 0x1C)[0]
    return total / 44100.0, (loop / 44100.0 if loop else 0.0), raw[:0x40]


def midi_seconds(path):
    m = mido.MidiFile(path)
    return m.length


def main():
    vdir, mdir = sys.argv[1], sys.argv[2]
    vg = sorted(glob.glob(os.path.join(vdir, '*.vgz')))
    mids = sorted(glob.glob(os.path.join(mdir, 'SZ_GS*.mid')))
    if not mids:
        mids = sorted(glob.glob(os.path.join(mdir, '[0-9][0-9] *.mid')))
    print('VGZ: %d 个   MIDI: %d 个' % (len(vg), len(mids)))

    vs = []
    for f in vg:
        sec, loop, _ = vgz_seconds(f)
        if sec:
            vs.append((os.path.basename(f), sec, loop))
    ms = [(os.path.basename(f), midi_seconds(f)) for f in mids]

    print('\n%-38s %8s %8s' % ('VGZ', '时长', '循环点'))
    for n, s, l in vs:
        print('%-38s %7.1f %8.1f' % (n[:36], s, l))
    print('\n%-16s %8s' % ('MIDI', '时长'))
    for n, s in ms:
        print('%-16s %7.1f' % (n, s))

    print('\n按时长匹配（全局最佳）：')
    pairs = []
    for vn, vs_, vl in vs:
        for mn, ms_ in ms:
            pairs.append((abs(ms_ - vs_), vn, mn, vs_, ms_))
    pairs.sort()
    used_v, used_m, out = set(), set(), []
    for d, vn, mn, vs_, ms_ in pairs:
        if vn in used_v or mn in used_m:
            continue
        used_v.add(vn); used_m.add(mn)
        out.append((vn, vs_, mn, ms_, d))
    out.sort()
    print('%-38s %7s -> %-30s %7s %6s' % ('VGZ', '时长', 'MIDI', '时长', '差'))
    for vn, vs_, mn, ms_, d in out:
        flag = '' if d < 3 else ('  ?' if d < 15 else '  ??')
        print('%-38s %7.1f -> %-30s %7.1f %6.1f%s'
              % (vn[:36], vs_, mn[:28], ms_, d, flag))


if __name__ == '__main__':
    main()
