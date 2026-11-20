# -*- coding: utf-8 -*-
"""SMF 写出（标准 MIDI type-1）+ 读取（用于对照参考 MIDI）。不依赖第三方库。"""
from __future__ import annotations
import struct


def _vlq(v: int) -> bytes:
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(out))


class Track:
    def __init__(self):
        self.ev = []          # (tick, order, raw_bytes)

    def add(self, tick, raw, order=0):
        self.ev.append((int(tick), order, raw))

    def meta(self, tick, mtype, payload: bytes):
        self.add(tick, b'\xFF' + bytes([mtype]) + _vlq(len(payload)) + payload, -3)

    def render(self):
        self.ev.sort(key=lambda x: (x[0], x[1]))
        out = bytearray()
        last = 0
        for tick, _, raw in self.ev:
            out += _vlq(tick - last) + raw
            last = tick
        out += b'\x00\xFF\x2F\x00'
        return bytes(out)


def write_smf(path, tracks, tpq, tempo_us=500000, names=None):
    data = bytearray()
    t0 = Track()
    t0.meta(0, 0x03, b'AMUS')
    t0.meta(0, 0x51, bytes([(tempo_us >> 16) & 0xFF, (tempo_us >> 8) & 0xFF, tempo_us & 0xFF]))
    t0.meta(0, 0x58, bytes([4, 2, 24, 8]))
    all_tracks = [t0.render()] + [t.render() for t in tracks]
    data += b'MThd' + struct.pack('>IHHH', 6, 1, len(all_tracks), tpq)
    for t in all_tracks:
        data += b'MTrk' + struct.pack('>I', len(t)) + t
    open(path, 'wb').write(bytes(data))


# ---------------- 读取（只用于分析参考 MIDI） ----------------
def _read_vlq(buf, i, end):
    v = 0
    for _ in range(4):
        b = buf[i]; i += 1
        v = (v << 7) | (b & 0x7F)
        if not (b & 0x80):
            return v, i
    raise ValueError('vlq')


def read_smf(path):
    data = open(path, 'rb').read()
    assert data[:4] == b'MThd'
    hlen, fmt, ntrk, div = struct.unpack_from('>IHHH', data, 4)
    pos = 8 + hlen
    notes = []   #(tick, kind, ch, note, vel)
    tempos = []
    for _ in range(ntrk):
        assert data[pos:pos + 4] == b'MTrk'
        tlen = struct.unpack_from('>I', data, pos + 4)[0]
        i = pos + 8; end = i + tlen
        tick = 0; rs = 0
        while i < end:
            delta, i = _read_vlq(data, i, end)
            tick += delta
            b = data[i]
            if b & 0x80:
                if b < 0xF0:
                    rs = b
                st = b; i += 1
            else:
                st = rs
            if st == 0xFF:
                meta = data[i]; i += 1
                ln, i = _read_vlq(data, i, end)
                if meta == 0x51:
                    p = data[i:i + ln]
                    tempos.append((tick, (p[0] << 16) | (p[1] << 8) | p[2]))
                i += ln
                continue
            k = st & 0xF0; ch = st & 0x0F
            if k in (0xC0, 0xD0):
                i += 1; continue
            d1 = data[i]; d2 = data[i + 1]; i += 2
            if k in (0x90, 0x80):
                notes.append((tick, k, ch, d1, d2))
        pos = end
    return notes, tempos, div, fmt
