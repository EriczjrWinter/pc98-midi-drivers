# -*- coding: utf-8 -*-
""".MDT（MDRV2）→ SMF。

时间：tick 网格 48 tick/四分音符；速度命令 E9 的值就是 BPM
（MDRV98 v3.4E 的 0x15E0：timer = 256 - 4340/BPM，按 Timer B 单位反算，
 48 tick ≈ 一个四分音符）。音符时值字节 = 占用的 tick 数，
 门限时间 = 时值 * EA 倍率 / 8。
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


from . import parser as mdtparse      # noqa: E402

TPQ = 480
TICK_SCALE = TPQ // 48               # 10
DEFAULT_BPM = 120
MAX_SMF_TICKS = 48 * 420             # 7 分钟上限（48 tick/s? 见下）

# 轨道类型 → MIDI 通道
CH_FM = [0, 1, 2, 3, 4, 5]
CH_SSG = [6, 7, 8]
CH_RHY = 9
CH_ADP = 10


def vlq(v):
    out = bytearray([v & 0x7F])
    v >>= 7
    while v:
        out.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(out)


def smf_track(events, last_prio=0):
    """events: [(smf_tick, prio, bytes)]"""
    body = bytearray()
    last = 0
    for tick, prio, msg in sorted(events, key=lambda e: (e[0], e[1])):
        body += vlq(max(0, tick - last)) + msg
        last = tick
    body += b'\x00\xFF\x2F\x00'
    return bytes(body)


def assign_channels(mdt):
    """按类型给每条轨道分配 MIDI 通道。"""
    out = {}
    fi = si = ai = 0
    for tr in mdt.tracks:
        k = tr.kind()
        if k == 'fm':
            out[tr.idx] = CH_FM[fi % len(CH_FM)]
            fi += 1
        elif k == 'ssg':
            out[tr.idx] = CH_SSG[si % len(CH_SSG)]
            si += 1
        elif k == 'rhythm':
            out[tr.idx] = CH_RHY
        elif k == 'adpcm':
            out[tr.idx] = CH_ADP
    return out


def convert(data, max_ticks=MAX_SMF_TICKS):
    mdt = mdtparse.Mdt(data).parse()
    chans = assign_channels(mdt)
    conductor = bytearray()
    # 先把默认 tempo 写上，后面按事件覆盖
    tempo_events = []
    title = os.path.splitext(os.path.basename(getattr(data, 'name', '')))[0]

    per_channel = {}
    active = {}          # (ch, note) -> end tick
    warnings = []
    total_ticks = 0

    for tr in mdt.tracks:
        if tr.idx not in chans:
            continue
        ch = chans[tr.idx]
        evs = per_channel.setdefault(ch, [])
        prog = None
        vol = None
        for tick, kind, a, b in tr.events:
            if tick > max_ticks:
                break
            if kind == 'note':
                note = a
                if not 0 <= note <= 127:
                    warnings.append('轨%d 音高越界 %d' % (tr.idx, note))
                    continue
                # 单声道：上一个音在同一通道就没法共存，截断
                for (c2, n2), end in list(active.items()):
                    if c2 == ch and end > tick:
                        evs.append((end, 3, bytes([0x80 | ch, n2, 0])))
                        del active[(c2, n2)]
                end = tick + max(1, b)
                evs.append((tick, 5, bytes([0x90 | ch, note, 100])))
                active[(ch, note)] = end
                total_ticks = max(total_ticks, end)
            elif kind == 'drum':
                mask = a
                gate = b
                for bit, gm in mdtparse.DRUM_GM:
                    if mask & bit:
                        note = gm
                        for (c2, n2), end in list(active.items()):
                            if c2 == ch and n2 == note and end > tick:
                                evs.append((end, 3, bytes([0x80 | ch, n2, 0])))
                                del active[(c2, n2)]
                        evs.append((tick, 5, bytes([0x90 | ch, note, 100])))
                        active[(ch, note)] = tick + max(1, gate)
                        total_ticks = max(total_ticks, tick + max(1, gate))
            elif kind == 'program':
                if a != prog:
                    prog = a
                    evs.append((tick, 2, bytes([0xC0 | ch, a & 0x7F])))
            elif kind == 'volume':
                if a != vol:
                    vol = a
                    evs.append((tick, 2, bytes([0xB0 | ch, 7, a & 0x7F])))
            elif kind == 'tempo':
                tempo_events.append((tick, a))
    # 收尾 note-off
    for (ch, note), end in active.items():
        per_channel.setdefault(ch, []).append(
            (max(end, total_ticks), 3, bytes([0x80 | ch, note, 0])))

    # 速度轨
    tempo_events.sort()
    if not tempo_events:
        tempo_events = [(0, DEFAULT_BPM)]
    last = 0
    seen_first = False
    for tick, bpm in tempo_events:
        if bpm <= 0:
            continue
        us = int(60000000 / bpm)
        conductor += vlq(tick - last) + b'\xFF\x51\x03' + us.to_bytes(3, 'big')
        last = tick
        seen_first = True
    if not seen_first:
        conductor += b'\x00\xFF\x51\x03' + int(60000000 / DEFAULT_BPM).to_bytes(3, 'big')
    conductor += b'\x00\xFF\x2F\x00'

    tracks = [bytes(conductor)]
    for ch in sorted(per_channel):
        evs = [(t * TICK_SCALE, p, m) for t, p, m in per_channel[ch]]
        tracks.append(smf_track(evs))
    out = bytearray(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), TPQ))
    for t in tracks:
        out += b'MTrk' + struct.pack('>I', len(t)) + t
    stats = {
        'tracks': len(mdt.tracks),
        'channels': len(per_channel),
        'notes': sum(1 for tr in mdt.tracks for e in tr.events if e[1] == 'note'),
        'ticks': total_ticks,
        'tempo': tempo_events[0][1] if tempo_events else DEFAULT_BPM,
        'warnings': warnings,
    }
    return bytes(out), stats


def convert_file(path, out_path=None, max_seconds=420.0):
    data = bytearray(open(path, 'rb').read())
    smf, stats = convert(data, max_ticks=int(max_seconds * 48))
    if out_path is None:
        out_path = os.path.splitext(path)[0] + '.mid'
    with open(out_path, 'wb') as f:
        f.write(smf)
    return out_path, stats


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    for p in sys.argv[1:]:
        out, st = convert_file(p)
        print('%s -> %s  轨%d 通道%d 音符%d tick%d tempo%d'
              % (os.path.basename(p), os.path.basename(out), st['tracks'],
                 st['channels'], st['notes'], st['ticks'], st['tempo']))
        for w in st['warnings'][:5]:
            print('  !', w)
