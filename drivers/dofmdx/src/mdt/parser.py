# -*- coding: utf-8 -*-
""".MDT (MDRV2) 静态解析：头部 + 轨道表 + 事件流。

事件格式（从 MDRV98.COM v3.4E 反推，并用 unicorn 跑驱动逐事件校验）：

文件头
  00 u16 版本（0x0302）
  02 u8  表项数 N（一般是 0x0D）
  03 u8  标志（bit7 → [0x139]）
  04 u8  → [0x1a5]
  06 N × {u16 起点, u8 类型, u8 0}
     类型：bit7=FM  bit6=SSG  bit4=节奏  bit5=ADPCM；低 4 位是通道号
  06+N*4 {u16 音色库起点, u16 音色库终点}

轨道事件
  < 0xE0           音符/休止：0x90=休止；下跟时值字节（tick 数）；
                   音高 = (高 nibble)*12 + (低 nibble)，对应 MIDI = 值+12
                   0x91 表示同音延续（时值累加）
  0xE0 nn          循环开始 n 次
  0xE1             循环出口
  0xE2             循环结束（回跳）
  0xE3 nn / E4 / E5  第二组循环
  0xE6 nn          音高微调
  0xE7 nn          移调
  0xE8 a,b,c,d     LFO/包络
  0xE9 nn          速度（BPM）
  0xEA nn          门限倍率（1/8 单位，8=1.0）
  0xEB nn          音色号（节奏轨：鼓位掩码）
  0xEC nn          音量（节奏轨 bit7=0 时后面再跟 6 个鼓音量）
  0xED ...         颤音
  0xEE reg,val     直写 FM 寄存器
  0xEF nn
  0xF0 nn          淡入/淡出
  0xF1 nn          LFO/AM
  0xF2 pitch,dur16 绝对时值音符
  0xF3 off16       相对跳转
  0xF4/F5 nn       移调 +/-（按轨道类型不同）
  0xF6 val,off16   写字节
  0xF7 ...
  0xF8 nn          状态
  0xF9 off16       条件跳转
  0xFA off16       跳转并记循环点
  0xFB/FC/FD       包络/LFO 定义
  0xFE             空操作
  0xFF             轨道结束
"""

DEFAULT_PARAM = {
    0xE0: 1, 0xE1: 0, 0xE2: 0, 0xE3: 1, 0xE4: 0, 0xE5: 0,
    0xE6: 1, 0xE7: 1, 0xE8: 4, 0xE9: 1, 0xEA: 1, 0xEB: 1, 0xEC: 1,
    0xED: 4, 0xEE: 2, 0xEF: 1,
    0xF0: 1, 0xF1: 1, 0xF2: 4, 0xF3: 3, 0xF4: 1, 0xF5: 1, 0xF6: 3,
    0xF7: 1, 0xF8: 1, 0xF9: 3, 0xFA: 3, 0xFB: 4, 0xFC: 4, 0xFD: 4,
    0xFE: 0,
}

# 节奏轨的鼓位 → GM 打击乐音高
DRUM_GM = [
    (0x01, 37),   # RIM  → Side Stick
    (0x02, 45),   # TOM  → Low Tom
    (0x04, 42),   # HH   → Closed Hi-Hat
    (0x08, 49),   # TOP  → Crash Cymbal 1
    (0x10, 38),   # SD   → Acoustic Snare
    (0x20, 36),   # BD   → Bass Drum 1
]


def note_to_midi(p):
    # ? nibble ????? A4 ? block ?? 3 ???? 8-15 ????0xC0 ? 0x40 ???
    return ((p >> 4) & 7) * 12 + (p & 0x0F) + 12


class Track:
    def __init__(self, idx, start, type_id, data):
        self.idx = idx
        self.start = start
        self.type_id = type_id
        self.data = data
        self.end = len(data)
        self.tempo = 0
        self.program = 0
        self.volume = 100
        self.transpose = 0
        self.dur_mult = 8
        self.octave = 0
        self.drum_mask = 0
        self.events = []       # (tick, kind, a, b)
        self.stream = []       # (off, opcode, span, tick) 供查错

    def kind(self):
        if self.type_id & 0x80:
            return 'fm'
        if self.type_id & 0x40:
            return 'ssg'
        if self.type_id & 0x10:
            return 'rhythm'
        if self.type_id & 0x20:
            return 'adpcm'
        return 'none'


def span_of(track, op, data, ptr):
    """返回指令总字节数（含 opcode）。节奏轨的 EC 是变长。"""
    if op == 0xEC and track.kind() == 'rhythm' and ptr < len(data):
        if data[ptr] & 0x80:
            return 3        # bit7=1：鼓号 + 1 字节
        return 8            # 音量 + 6 个鼓音量
    return 1 + DEFAULT_PARAM[op]


def parse_track(track, base_off, data, end_off, tick0=0, max_events=50000):
    d = data
    ptr = base_off
    tick = tick0
    stack = []
    loops2 = []
    count = 0
    iters = 0
    while count < max_events:
        iters += 1
        if iters > 400000:          # 死循环保护（0xFF/jump 路径不计数）
            break
        if ptr >= end_off or ptr >= len(d):
            break
        ev_off = ptr
        op = d[ptr]
        ptr += 1
        if op == 0xFF:
            track.stream.append((ev_off, 0xFF, 1, tick))
            if stack and stack[-1][0] == 'fa':
                ptr = stack[-1][3]
                continue
            ptr = ev_off + 1
            break
        if op < 0xE0:
            if ptr >= len(d):
                break
            if op == 0x90:
                dur = d[ptr]
                ptr += 1
                if ptr < len(d) and d[ptr] == 0x91:
                    ptr += 1        # 0x91 ??????????????????
                t_ev = tick
                track.events.append((t_ev, 'rest', dur, 0))
                tick += dur
                track.stream.append((ev_off, op, ptr - ev_off, t_ev))
                count += 1
                continue
            pitch = op
            dur = d[ptr]
            ptr += 1
            # 连音：<音高> <时值> (0x91 <同音高> <时值>)*
            while ptr + 2 < len(d) and d[ptr] == 0x91:
                p2 = d[ptr + 1]
                if p2 != pitch:
                    ptr += 1        # 0x91 吃掉，音高字节留给下一个事件
                    break
                dur += d[ptr + 2]
                ptr += 3
            mult = track.dur_mult & 7
            gate = dur if mult == 0 else (dur * mult) >> 3
            if gate <= 0:
                gate = 1
            t_ev = tick
            if track.kind() == 'rhythm':
                track.events.append((t_ev, 'drum', track.drum_mask, gate))
            else:
                midi = note_to_midi((pitch + track.transpose) & 0xFF)
                track.events.append((t_ev, 'note', midi, gate))
            tick += dur
            track.stream.append((ev_off, op, ptr - ev_off, t_ev))
            count += 1
            continue

        # 命令
        span = span_of(track, op, d, ptr)
        if op == 0xE0:
            stack.append(('e0', d[ptr], ptr + 1, None))
        elif op == 0xE2:
            if stack and stack[-1][0] == 'e0':
                kind, cnt, lp, _ = stack.pop()
                cnt -= 1
                if cnt > 0:
                    stack.append((kind, cnt, lp, None))
                    ptr = lp
                    track.stream.append((ev_off, op, 0, tick))
                    continue
        elif op == 0xE3:
            loops2.append((d[ptr], ptr + 1))
        elif op == 0xE4:
            if loops2:
                cnt, lp = loops2[-1]
                if cnt > 1:
                    loops2[-1] = (cnt - 1, lp)
                    ptr = lp
                    track.stream.append((ev_off, op, 0, tick))
                    continue
                loops2.pop()
        elif op == 0xE6:
            track.octave = d[ptr]
        elif op == 0xE7:
            track.transpose = d[ptr] - 256 if d[ptr] & 0x80 else d[ptr]
        elif op == 0xE9:
            track.tempo = d[ptr]
            track.events.append((tick, 'tempo', d[ptr], 0))
        elif op == 0xEA:
            track.dur_mult = d[ptr]
        elif op == 0xEB:
            track.program = d[ptr] & 0x3F
            if track.kind() == 'rhythm':
                track.drum_mask = d[ptr] & 0x3F
            else:
                track.events.append((tick, 'program', track.program, 0))
        elif op == 0xEC:
            track.volume = d[ptr]
            if track.kind() == 'rhythm' and not (d[ptr] & 0x80):
                track.events.append((tick, 'volume', d[ptr] & 0x7F, 0))
                track.events.append((tick, 'drum_levels',
                                     list(d[ptr + 1:ptr + 7]), 0))
        elif op == 0xFA:
            off = d[ptr] | (d[ptr + 1] << 8)
            stack.append(('fa', 0, ptr + 2, base_off + off))
            track.stream.append((ev_off, op, span, tick))
            ptr = base_off + off
            continue
        elif op == 0xF3:
            off = d[ptr] | (d[ptr + 1] << 8)
            track.stream.append((ev_off, op, span, tick))
            ptr = ptr + 2 + off
            continue
        track.stream.append((ev_off, op, span, tick))
        ptr = ev_off + span
        count += 1
    return tick


class Mdt:
    def __init__(self, data):
        self.data = data
        self.version = data[0] | (data[1] << 8)
        self.count = data[2]
        self.flags = data[3]
        self.byte4 = data[4]
        self.entries = []
        for i in range(self.count):
            off = 6 + i * 4
            start = data[off] | (data[off + 1] << 8)
            tid = data[off + 2] | (data[off + 3] << 8)
            self.entries.append((start, tid))
        off = 6 + self.count * 4
        self.tone_start = data[off] | (data[off + 1] << 8)
        self.tone_end = data[off + 2] | (data[off + 3] << 8)
        self.tracks = [Track(i, s, t, data) for i, (s, t) in enumerate(self.entries)]

    def parse(self):
        for i, tr in enumerate(self.tracks):
            if not tr.type_id or tr.start == 0:
                continue
            nxt = None
            for j in range(i + 1, len(self.entries)):
                if self.entries[j][0]:
                    nxt = self.entries[j][0]
                    break
            if nxt is None:
                nxt = self.tone_start or len(self.data)
            tr.end = nxt
            parse_track(tr, tr.start, self.data, len(self.data))
        return self


def load(path):
    return Mdt(open(path, 'rb').read())
