# -*- coding: utf-8 -*-
"""MDRV98 MIDI 变体导出器。

抓包（表 B + Timer B）→ 去掉板初始化字节 → 写 SMF。

时间校准：用 Win95 GM 版（同曲）对齐出来的 1 tick = 4.908 ms。
每首的导出长度 = 参考 MIDI 的时长 / 4.908ms，这样和参考逐首对齐。
"""
import os
import struct
import sys

import mido

from . import capture as midicap
from . import smf as view

TICK_MS = 4.9082          # 一次 Timer B 中断
REF_DIRS = {
    'cl_98': r'D:\music\90S Galgame music\水晶迷宫-逢魔的迷宫',
    'you4_98': r'D:\music\90S Galgame music\水晶迷宫-逢魔的迷宫',
    'zatuon_98': r'D:\music\90S Galgame music\杂音领域',
}


def ref_dir_for(pack):
    return REF_DIRS.get(pack)


def strip_leading_board(stream):
    out = list(stream)
    while out and out[0][1] in (0xFF, 0x3F):
        out.pop(0)
    return out


def collect_msgs(pack, name, ticks):
    sim, n = midicap.capture(midicap.load_track(pack, name), ticks=ticks)
    stream = strip_leading_board(sim.midi)
    msgs = view.parse(stream)
    clean = []
    for t, m in msgs:
        if not m or m[0] >= 0xF0:
            continue
        need = 2 if 0xC0 <= m[0] < 0xE0 else 3
        if len(m) != need:
            continue
        if 0x90 <= m[0] < 0xA0 and len(m) > 2 and m[1] == 0 and m[2] == 0:
            continue
        clean.append((t, bytes(m)))
    return clean, n


def ref_info(path):
    """返回 (时长秒, tempo_us, ppq)。"""
    m = mido.MidiFile(path)
    tempo = [msg.tempo for tr in m.tracks for msg in tr if msg.type == 'set_tempo']
    return m.length, (tempo[0] if tempo else 500000), m.ticks_per_beat


def vlq(v):
    out = bytearray([v & 0x7F])
    v >>= 7
    while v:
        out.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(out)


def build(msgs, ppq, tempo_us, tick_ms):
    midi_ticks_per_sec = ppq * 1e6 / tempo_us
    events = []
    for t, m in msgs:
        mt = int(round(t * (tick_ms / 1000.0) * midi_ticks_per_sec))
        if 0x90 <= m[0] < 0xA0 and m[2] > 0:
            prio = 1
        elif (0x90 <= m[0] < 0xA0 and m[2] == 0) or 0x80 <= m[0] < 0x90:
            prio = 0
        else:
            prio = 0
        events.append((mt, prio, m))
    events.sort(key=lambda e: (e[0], e[1]))
    # 结尾补 note-off：抓包在循环点截断，会有几个音挂着
    active = set()
    for mt, _p, m in events:
        if 0x90 <= m[0] < 0xA0 and m[2] > 0:
            active.add((m[0] & 0x0F, m[1]))
        elif 0x80 <= m[0] < 0x90 or (0x90 <= m[0] < 0xA0 and m[2] == 0):
            active.discard((m[0] & 0x0F, m[1]))
    end_tick = events[-1][0] if events else 0
    for ch, note in sorted(active):
        events.append((end_tick, 0, bytes([0x80 | ch, note, 0])))
    track = bytearray(b'\x00\xff\x51\x03' + int(tempo_us).to_bytes(3, 'big'))
    last = 0
    for mt, _p, m in events:
        track += vlq(max(0, mt - last)) + m
        last = mt
    track += b'\x00\xff\x2f\x00'
    return (b'MThd' + struct.pack('>IHHH', 6, 0, 1, ppq)
            + b'MTrk' + struct.pack('>I', len(track)) + bytes(track))


def export_track(pack, name, out_path, ref_path=None, tick_ms=TICK_MS,
                 max_seconds=430.0):
    if ref_path and os.path.exists(ref_path):
        dur, tempo_us, ppq = ref_info(ref_path)
        ticks = int(round(dur * 1000.0 / tick_ms)) + 2
    else:
        tempo_us, ppq = 857142, 480
        ticks = int(max_seconds * 1000.0 / tick_ms)
    msgs, n = collect_msgs(pack, name, ticks)
    smf = build(msgs, ppq, tempo_us, tick_ms)
    with open(out_path, 'wb') as f:
        f.write(smf)
    return {'ticks': n, 'msgs': len(msgs), 'seconds': ticks * tick_ms / 1000.0}


if __name__ == '__main__':
    pack = sys.argv[1] if len(sys.argv) > 1 else 'cl_98'
    name = sys.argv[2] if len(sys.argv) > 2 else 'CR001C.FMD'
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.getcwd(), 'out.mid')
    base = os.path.splitext(os.path.basename(name))[0]      # CR001C
    num = base[:-1] if base and base[-1] in 'CFG' else base
    rd = ref_dir_for(pack)
    ref = os.path.join(rd, num + '.MID') if rd else None
    if ref and not os.path.exists(ref):
        ref = None
    info = export_track(pack, name, out, ref)
    print('%s/%s -> %s  %s' % (pack, name, out, info))
