# -*- coding: utf-8 -*-
"""用官方时长反推 tempo：implied_us_per_tick = 官方秒数 / tick 数。"""
import re
import struct
import sys
import zipfile

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\msdrv\src')
import ms_parser as M

H = r'D:\GamedataUnpack\hoot20251231\pc98'
TXT = (r'D:\music\90S Galgame music\壳中的小鸟'
       r'\Kara_no_Naka_no_Kotori_(NEC_PC-9801,_OPNA)\Kara no Naka no Kotori.txt')

# 官方时长
ref = {}
t = open(TXT, encoding='utf-8-sig').read()
for m in re.finditer(r'^(\d\d)\s+(.+?)\s+(\d+):(\d\d)', t, re.M):
    ref[int(m.group(1))] = int(m.group(3)) * 60 + int(m.group(4))

z = zipfile.ZipFile(H + r'\karanon_98.zip')


def e7_of(d):
    """读轨道 0 前部的 e7 值。"""
    table = M.read_table(d)
    off = table[0][1]
    limit = table[1][1] if len(table) > 1 else len(d)
    pos, buf, n = off, [0, 0, 0, 0], min(limit, len(d))
    vals = []
    steps = 0
    while pos < n and steps < 20000:
        steps += 1
        cmd = d[pos]; pos += 1
        if cmd == 0x9E:
            continue
        if 0x80 <= cmd <= 0x8F:
            for bit, k in ((0x08, 0), (0x04, 1), (0x02, 2), (0x01, 3)):
                if cmd & bit:
                    buf[k] = d[pos] if pos < n else 0; pos += 1
        else:
            buf[0] = cmd
            for k in (1, 2, 3):
                buf[k] = d[pos] if pos < n else 0; pos += 1
        if buf[0] == 0xFE:
            break
        if buf[0] == 0xE7:
            vals.append(buf[2])
    return vals


print('%-12s %8s %8s %10s %10s %8s' %
      ('文件', '官方秒', 'tick数', 'us/tick', 'BPM(48tpq)', 'e7值'))
for i in range(1, 10):
    n = 'MD_%02d_GS.MS' % i
    try:
        d = z.read(n)
    except KeyError:
        continue
    table = M.read_table(d)
    mx = 0
    for k, (idx, off) in enumerate(table):
        limit = table[k + 1][1] if k + 1 < len(table) else len(d)
        ev, _, _ = M.parse_track(d, off, idx & 0x0F, limit=limit)
        for tick, kind, a, b in ev:
            mx = max(mx, tick)
    r = ref.get(i, 0)
    if not mx or not r:
        continue
    us_per_tick = r * 1e6 / mx
    bpm = 60e6 / (us_per_tick * 48)
    print('%-12s %8d %8d %10.1f %10.1f %8s'
          % (n, r, mx, us_per_tick, bpm, e7_of(d)[:3]))
