# -*- coding: utf-8 -*-
"""导出 殻の中の小鳥 的 .MS → MIDI。

tempo 还没解出来，所以按「官方时长 ÷ tick 数」给每首算一个**整体速度**。
同曲内的变速会丢失，但总时长和大致节奏是对的。
"""
import io
import os
import re
import struct
import sys
import zipfile

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\msdrv\src')
import ms_parser as M
import mido

H = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\music\90S Galgame music\壳中的小鸟\PC98-MIDI'
TXT = (r'D:\music\90S Galgame music\壳中的小鸟'
       r'\Kara_no_Naka_no_Kotori_(NEC_PC-9801,_OPNA)\Kara no Naka no Kotori.txt')

# 曲名（VGM 包的英文标题）
TITLES = {
    1: 'Heels Beat on the Stone Paving',
    2: 'Drops are Dots, Vessels are Faces',
    3: 'One and Two and Three',
    4: 'A Bird Flies Even Without Wind',
    5: 'An Erased Voice is Noise',
    6: 'An Invisible Chain Hurts Her Neck',
    7: 'A Broken Piano Will Not Play',
    8: 'White Virgin, Black Slave',
    9: "To Dream is a Lady's Privilege",
}

ref = {
    1: 57,    # 0:57
    2: 46,    # 0:46
    3: 53,    # 0:53
    4: 231,   # 3:51
    5: 125,   # 2:05
    6: 92,    # 1:32
    7: 44,    # 0:44
    8: 78,    # 1:18
    9: 51,    # 0:51
}


def build(data, tempo_us):
    """同 ms_parser.build_smf，但让 tempo 可指定。"""
    table = M.read_table(data)
    all_ev = []
    for k, (idx, off) in enumerate(table):
        ch = idx & 0x0F
        limit = table[k + 1][1] if k + 1 < len(table) else len(data)
        ev, _, _ = M.parse_track(data, off, ch, limit=limit)
        for tick, kind, a, b in ev:
            if kind == 'on':
                all_ev.append((tick, 0, bytes([0x90 | ch, a, b])))
            elif kind == 'off':
                all_ev.append((tick, 0, bytes([0x80 | ch, a, 0])))
            else:
                st = a | ch
                if isinstance(b, tuple):
                    all_ev.append((tick, 1, bytes([st, b[0], b[1]])))
                else:
                    all_ev.append((tick, 1, bytes([st, b])))

    def vlq(v):
        out = bytearray([v & 0x7F])
        v >>= 7
        while v:
            out.insert(0, (v & 0x7F) | 0x80)
            v >>= 7
        return bytes(out)

    all_ev.sort(key=lambda e: (e[0], e[1]))
    body = bytearray(b'\x00\xFF\x51\x03' + struct.pack('>I', tempo_us)[1:])
    last = 0
    for tick, prio, raw in all_ev:
        body += vlq(tick - last) + raw
        last = tick
    body += b'\x00\xFF\x2F\x00'
    out = bytearray(b'MThd' + struct.pack('>IHHH', 6, 1, 1, M.TPQ))
    out += b'MTrk' + struct.pack('>I', len(body)) + body
    return bytes(out)


def safe(s):
    for ch in '\\/:*?"<>|':
        s = s.replace(ch, '_')
    return s


z = zipfile.ZipFile(H + r'\karanon_98.zip')
os.makedirs(OUT, exist_ok=True)
for i in range(1, 10):
    r = ref.get(i, 0)
    for suf, label in (('GS', 'SC-55'), ('88', 'SC-88')):
        name = 'MD_%02d_%s.MS' % (i, suf)
        try:
            d = z.read(name)
        except KeyError:
            continue
        table = M.read_table(d)
        mx = 0
        for k, (idx, off) in enumerate(table):
            limit = table[k + 1][1] if k + 1 < len(table) else len(d)
            ev, _, _ = M.parse_track(d, off, idx & 0x0F, limit=limit)
            for tick, kind, a, b in ev:
                mx = max(mx, tick)
        # 按官方时长反推整体速度
        tempo_us = int(r * 1e6 / mx * M.TPQ) if (mx and r) else 500000
        smf = build(d, tempo_us)
        fn = '%02d %s [%s].mid' % (i, safe(TITLES.get(i, 'unknown')), label)
        p = os.path.join(OUT, fn)
        open(p, 'wb').write(smf)
        m = mido.MidiFile(file=io.BytesIO(smf))
        notes = sum(1 for tr in m.tracks for x in tr
                    if x.type == 'note_on' and x.velocity > 0)
        print('%-44s %6.1f 秒 (官方 %3d)  %5d 音符' % (fn[:42], m.length, r, notes))
print()
print('输出目录:', OUT)
