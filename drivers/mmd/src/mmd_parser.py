# -*- coding: utf-8 -*-
"""MMD (.MMD) → MIDI 解析器。

MMD = "Music Driver M.M.D. for PC9801/MIDI"，作者 M.Kajihara (KAJA)，
是 PMD 的 MIDI 版兄弟。格式参考 Devin Acker 2015 年的转换器（WTFPL）：
https://gist.github.com/devinacker/bdc58cfdba6a1ee80449

本实现相对那份的改动（都是实测踩出来的）：
  - 补 0xD8–0xDF 一族（原版只认 0xE8–0xEF，漏了触后和弯音）
  - c0 == 0 视为休止/空操作（原版会当成「音符 0」）
  - 无限循环只走一遍
  - 曲名按 Shift-JIS 解

文件结构
--------
+0x00  u8    bpm
+0x01  u8    transpose（有符号）
+0x02  16 × (u16 轨道偏移, u8 key, u8 channel)     ch==255 表示空轨
+0x50  曲名（Shift-JIS，NUL 结尾）

轨道数据
--------
循环读一个 cmd 字节：
  (cmd & 0xF0) == 0x80  →  位掩码形式
        bit3 (0x08) → buf[0] 存在
        bit2 (0x04) → buf[1] 存在
        bit1 (0x02) → buf[2] 存在
        bit0 (0x01) → buf[3] 存在
        未出现的字节沿用上一次的值（运行状态）
  否则                   →  buf[0] = cmd，再读 buf[1..3]

时间语义：buf[1] 是「本命令执行之后」要等的 tick 数。
"""
import os
import struct

TPQ = 48                      # MMD 原生分辨率
MAX_LOOP = 64
INFINITE_EXTRA_PASS = False  # 无限循环默认只走一遍（官方 MIDI 也是一遍）
IGNORE_LOOP_COUNT = False    # 用数据里的循环次数（TH02 若忽略次数会明显偏短）
MAX_TICKS = 120000           # 单轨上限，防止循环嵌套失控


class MMD:
    def __init__(self, data):
        self.data = data
        self.bpm = data[0]
        self.transpose = struct.unpack('b', data[1:2])[0]
        if not -36 <= self.transpose <= 36:
            self.transpose = 0
        self.tracks = []
        for i in range(16):
            off, key, ch = struct.unpack_from('<HBB', data, 2 + 4 * i)
            k = key if key <= 64 else key - 128
            self.tracks.append({'off': off, 'key': k, 'ch': ch})
        raw = data[0x50:0x50 + 256].split(b'\x00')[0]
        try:
            self.title = raw.decode('cp932')
        except Exception:
            self.title = raw.decode('ascii', 'replace')


def parse_track(data, off, key, transpose, bpm, max_cmds=200000):
    """跑一条轨道，返回 (events, tempos, warnings)。

    events: [(绝对tick, 'on'/'off'/'msg', a, b)]
    """
    events = []
    tempos = []
    warnings = []
    pending = []          # (结束tick, note)
    pos = off
    t = 0
    delay = 0
    buf = [0, 0, 0, 0]
    loop_stack = []
    infinite_done = False
    last_loop_pos = None
    stray_done = False
    n = len(data)
    guard = 0

    def flush(upto):
        keep = []
        for end, note in pending:
            if end <= upto:
                events.append((end, 'off', note, 0))
            else:
                keep.append((end, note))
        pending[:] = keep

    while guard < max_cmds:
        guard += 1
        if pos >= n:
            warnings.append('轨道越界')
            break
        cmd = data[pos]
        pos += 1

        if (cmd & 0xF0) == 0x80:
            if cmd & 0x08:
                buf[0] = data[pos]; pos += 1
            if cmd & 0x04:
                buf[1] = data[pos]; pos += 1
            if cmd & 0x02:
                buf[2] = data[pos]; pos += 1
            if cmd & 0x01:
                buf[3] = data[pos]; pos += 1
        else:
            buf[0] = cmd
            for k in (1, 2, 3):
                buf[k] = data[pos] if pos < n else 0
                pos += 1

        c0 = buf[0]
        if c0 == 0xFE:
            break

        if t > MAX_TICKS:
            warnings.append('超过 %d tick，强制结束（疑似循环嵌套失控）' % MAX_TICKS)
            break

        # 结算上一条命令留下的等待
        t += delay
        delay = 0

        if c0 == 0x00:                      # 休止 / 空操作
            flush(t)
            delay = buf[1]
            continue

        if c0 < 0x80:                       # 音符
            flush(t)
            note = (c0 + key + transpose) & 0x7F
            length = buf[2] if buf[2] > 0 else 1
            # 同音连打：不重新触发，而是延长正在响的那个音（与参考实现一致）
            extended = False
            for i, (end, pn) in enumerate(pending):
                if pn == note:
                    if t + length > end:
                        pending[i] = (t + length, pn)
                    extended = True
                    break
            if not extended:
                events.append((t, 'on', note, buf[3] & 0x7F))
                pending.append((t + length, note))
            delay = buf[1]
        elif c0 == 0xE7:                    # 变速
            flush(t)
            if buf[2]:
                us = int(64 * 60000000 / (bpm * buf[2])) if bpm else 500000
                tempos.append((t, us))
            if buf[3]:
                warnings.append('t=%d 有 tempo 渐变（未支持）' % t)
            delay = buf[1]
        elif (c0 & 0xF8) in (0xE8, 0xD8):   # 其它 MIDI 消息
            flush(t)
            kind = c0 & 0x0F
            if kind > 0xE:
                warnings.append('t=%d 未知消息 %02X（已跳过）' % (t, c0))
                continue
            if kind in (0xC, 0xD):
                events.append((t, 'msg', (kind << 4), buf[2] & 0x7F))
            else:
                events.append((t, 'msg', (kind << 4),
                               (buf[2] & 0x7F, buf[3] & 0x7F)))
            delay = buf[1]
        elif c0 == 0xF9:                    # 循环开始
            loop_stack.append((pos, None, 0))
            last_loop_pos = pos
        elif c0 == 0xF8:                    # 循环结束
            if not loop_stack:
                # 数据里存在没有配对 F9 的 F8（实测轨 9 就是这样）。
                # 试过「复用最近的循环点」，结果音符反而偏多，所以按忽略处理。
                warnings.append('t=%d 无配对的循环结束（已忽略）' % t)
                continue
            ret, target, done = loop_stack[-1]
            count = buf[1]
            if count == 0:
                # 无限循环：再走一遍，让结尾完整（驱动会一直重复，录音只是按 CD 长度截断）
                if INFINITE_EXTRA_PASS and not infinite_done:
                    infinite_done = True
                    pos = ret
                    continue
                break
            done += 1
            if IGNORE_LOOP_COUNT or done >= count or len(loop_stack) > MAX_LOOP:
                loop_stack.pop()
            else:
                loop_stack[-1] = (ret, target, done)
                pos = ret
        else:
            warnings.append('未知命令 %02X' % c0)

    flush(1 << 30)
    return events, tempos, warnings


def build_smf(mm, verbose=False):
    """把解析结果写成 SMF（format 1，TPQ=48）。"""
    tracks = []
    tempo_track = bytearray()

    def vlq(v):
        out = bytearray([v & 0x7F])
        v >>= 7
        while v:
            out.insert(0, (v & 0x7F) | 0x80)
            v >>= 7
        return bytes(out)

    base_us = int(60000000 / mm.bpm) if mm.bpm else 500000
    tempo_track += b'\x00\xFF\x51\x03' + struct.pack('>I', base_us)[1:]
    if mm.title:
        tt = mm.title.encode('cp932', 'replace')
        tempo_track += b'\x00\xFF\x03' + vlq(len(tt)) + tt

    chan_events = {}
    all_tempos = []
    warnings = []
    for idx, tr in enumerate(mm.tracks):
        if tr['ch'] >= 16:
            continue
        ev, tp, wn = parse_track(mm.data, tr['off'], tr['key'],
                                 mm.transpose, mm.bpm)
        warnings += ['轨%d: %s' % (idx, w) for w in wn]
        all_tempos += tp
        ch = tr['ch']
        bucket = chan_events.setdefault(ch, [])
        for tick, kind, a, b in ev:
            if kind == 'on':
                bucket.append((tick, bytes([0x90 | ch, a, b]), 2))
            elif kind == 'off':
                bucket.append((tick, bytes([0x80 | ch, a, 0]), 0))
            else:                           # msg
                st = a | ch
                if isinstance(b, tuple):
                    bucket.append((tick, bytes([st, b[0], b[1]]), 1))
                else:
                    bucket.append((tick, bytes([st, b]), 1))

    all_tempos.sort()
    last = 0
    for tick, us in all_tempos:
        tempo_track += vlq(tick - last) + b'\xFF\x51\x03' + struct.pack('>I', us)[1:]
        last = tick
    tempo_track += b'\x00\xFF\x2F\x00'
    tracks.append(bytes(tempo_track))

    for ch in sorted(chan_events):
        body = bytearray()
        last = 0
        for tick, raw, prio in sorted(chan_events[ch], key=lambda x: (x[0], x[2])):
            body += vlq(tick - last) + raw
            last = tick
        body += b'\x00\xFF\x2F\x00'
        tracks.append(bytes(body))

    out = bytearray(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), TPQ))
    for t in tracks:
        out += b'MTrk' + struct.pack('>I', len(t)) + t
    return bytes(out), warnings


def convert_file(path, out_path=None, verbose=False):
    data = open(path, 'rb').read()
    mm = MMD(data)
    smf, warnings = build_smf(mm)
    out_path = out_path or os.path.splitext(path)[0] + '.mid'
    open(out_path, 'wb').write(smf)
    if verbose:
        print('%s  bpm=%d  转调=%+d  《%s》'
              % (os.path.basename(path), mm.bpm, mm.transpose, mm.title))
        for w in warnings[:6]:
            print('   !', w)
    return out_path, mm, warnings


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    for p in sys.argv[1:]:
        convert_file(p, verbose=True)
