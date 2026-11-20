# -*- coding: utf-8 -*-
"""把 MMDR 吐出的 MIDI 字节流整理成 SMF。

字节流是标准 MIDI（驱动本来就发给外部音源），所以只需要处理运行状态。
"""
import struct


class Parser:
    def __init__(self):
        self.events = []        # (tick, bytes)
        self.status = 0
        self.buf = []
        self.pending = 0        # 还需要几个数据字节
        self.sysex = None

    def feed(self, tick, b):
        if self.sysex is not None:
            self.sysex.append(b)
            if b == 0xF7:
                self.events.append((tick, bytes([0xF0] + self.sysex)))
                self.sysex = None
            return

        if b & 0x80:                       # 状态字节
            if b == 0xF0:
                self.sysex = []
                self.pending = 0
                self.buf = []
                return
            if b == 0xF7:
                self.pending = 0
                self.buf = []
                return
            if b >= 0xF8:                  # 实时消息，忽略
                return
            if b >= 0xF0:                  # 其它系统消息：按长度吞掉
                self.pending = {0xF1: 1, 0xF2: 2, 0xF3: 1}.get(b, 0)
                self.status = 0
                self.buf = [b]
                return
            self.status = b
            hi = b & 0xF0
            self.pending = 1 if hi in (0xC0, 0xD0) else 2
            self.buf = []
            return

        # 数据字节
        if self.pending == 0:
            return                          # 无运行状态，丢弃
        self.buf.append(b)
        self.pending -= 1
        if self.pending == 0:
            self.events.append((tick, bytes([self.status] + self.buf)))
            self.buf = []


def build_ms(stream_ms, tpq=480):
    """stream_ms: [(毫秒, byte)] —— 时间已按驱动设定的定时器换算好。

    固定 tempo=500000（1 拍 = 480 tick = 500ms），于是 1ms = 0.96 tick，
    这样文件播放时长就是真实时长，与曲目自身的 tempo 无关。
    """
    p = Parser()
    for t, b in stream_ms:
        p.feed(t, b)

    tempo = 500000
    ticks_per_ms = tpq / 500.0

    meta = bytearray()
    meta += b'\x00\xFF\x51\x03' + bytes([(tempo >> 16) & 0xFF, (tempo >> 8) & 0xFF, tempo & 0xFF])
    meta += b'\x00\xFF\x58\x04\x04\x02\x18\x08'
    last_meta = 0

    def vlq(v):
        out = bytearray([v & 0x7F])
        v >>= 7
        while v:
            out.insert(0, (v & 0x7F) | 0x80)
            v >>= 7
        return bytes(out)

    tracks = {}
    for t, msg in p.events:
        mt = int(round(t * ticks_per_ms))
        if msg[0] == 0xF0:
            meta += vlq(mt - last_meta) + b'\xF0' + vlq(len(msg) - 1) + msg[1:]
            last_meta = mt
            continue
        tracks.setdefault(msg[0] & 0x0F, []).append((mt, msg))

    chunks = [bytes(meta) + b'\x00\xFF\x2F\x00']
    for ch in sorted(tracks):
        body = bytearray()
        last = 0
        for mt, msg in tracks[ch]:
            body += vlq(mt - last) + msg
            last = mt
        body += b'\x00\xFF\x2F\x00'
        chunks.append(bytes(body))

    out = bytearray(b'MThd' + struct.pack('>IHHH', 6, 1, len(chunks), tpq))
    for c in chunks:
        out += b'MTrk' + struct.pack('>I', len(c)) + c
    return bytes(out), tempo, p
