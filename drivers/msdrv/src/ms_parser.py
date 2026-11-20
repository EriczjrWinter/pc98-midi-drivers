# -*- coding: utf-8 -*-
""".MS（黒パッケージ MSDRV4）→ MIDI。

`.MS` 的容器：40 项 u32 偏移表，前 36 项是轨道指针，第 39 项指向文件末尾。
每轨是一段 **MMD 家族的命令流**，轨道号 = MIDI 通道号。

与 MMD 的差异：
  - 掩码家族有两套：0x80–0x8F 和 0x90–0x9F
  - E6 00 NN = 选轨（等价于设通道）
  - 没有 16 轨头部，也没有曲名
"""
import os
import struct

TPQ = 48
MAX_STEPS = 300000


def read_table(data):
    """读 40 项偏移表，返回有效轨道 [(0-based 序号, 偏移)]。"""
    out = []
    for i in range(40):
        if i * 4 + 4 > len(data):
            break
        v = struct.unpack_from('<I', data, i * 4)[0]
        if 0 < v < len(data):
            out.append((i, v))
    return out


def parse_track(data, off, ch, limit=None, max_steps=MAX_STEPS):
    events = []
    tempos = []
    warnings = []
    pending = []
    pos = off
    started = False
    t = 0
    delay = 0
    buf = [0, 0, 0, 0]
    n = len(data) if limit is None else min(limit, len(data))
    steps = 0

    def flush(upto):
        keep = []
        for end, note in pending:
            if end <= upto:
                events.append((end, 'off', note, 0))
            else:
                keep.append((end, note))
        pending[:] = keep

    while steps < max_steps and pos < n:
        steps += 1
        cmd = data[pos]
        pos += 1

        if cmd == 0x9E:                     # 单字节命令（等待/同步）
            continue
        if cmd == 0x9C:                     # 3 字节参数（实测这个长度对得上时长）
            pos += 3
            continue
        if cmd == 0x8A:                     # 设 BPM（1 字节）
            bpm = data[pos] if pos < n else 0
            pos += 1
            if bpm:
                tempos.append((t, int(60000000 / bpm)))
            continue

        if 0x80 <= cmd <= 0x8F:             # 掩码家族（只有 0x80–0x8F）
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
            break

        t += delay
        delay = 0

        if c0 == 0xE6:                      # 选轨（设通道）
            started = True
            ch = buf[2] & 0x0F
            delay = buf[1]
            continue
        if c0 == 0x00:
            flush(t)
            delay = buf[1]
            continue
        if c0 < 0x80:                       # 音符
            if not started or buf[3] == 0:  # 轨道未开始 / 力度 0 都不是真音符
                delay = buf[1]
                continue
            flush(t)
            note = c0 & 0x7F
            length = buf[2] if buf[2] > 0 else 1
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
        elif c0 == 0xE7:                    # 语义未明（不是变速，速度走 8A）
            flush(t)
            delay = buf[1]
        elif (c0 & 0xF8) in (0xE8, 0xD8):   # MIDI 消息
            flush(t)
            kind = c0 & 0x0F
            if kind <= 0xE:
                if kind in (0xC, 0xD):
                    events.append((t, 'msg', kind << 4, buf[2] & 0x7F))
                else:
                    events.append((t, 'msg', kind << 4,
                                   (buf[2] & 0x7F, buf[3] & 0x7F)))
            else:
                warnings.append('t=%d 未知消息 %02X' % (t, c0))
            delay = buf[1]
        else:
            warnings.append('未知命令 %02X' % c0)

    flush(1 << 30)
    return events, tempos, warnings, ch


def build_smf(data, base_tempo=500000):
    """把整个 .MS 转成 SMF。"""
    tracks = []
    all_ev = []
    warnings = []
    tmax = 0

    table = read_table(data)
    all_tempos = []
    for k, (idx, off) in enumerate(table):
        ch = idx & 0x0F
        limit = table[k + 1][1] if k + 1 < len(table) else len(data)
        ev, tp, wn, ch = parse_track(data, off, ch, limit=limit)
        all_tempos += tp
        warnings += ['轨%d: %s' % (idx, w) for w in wn[:3]]
        for tick, kind, a, b in ev:
            if kind == 'on':
                all_ev.append((tick, 0, bytes([0x90 | ch, a, b])))
                tmax = max(tmax, tick)
            elif kind == 'off':
                all_ev.append((tick, 0, bytes([0x80 | ch, a, 0])))
            else:
                st = a | ch
                if isinstance(b, tuple):
                    all_ev.append((tick, 1, bytes([st, b[0], b[1]])))
                else:
                    all_ev.append((tick, 1, bytes([st, b])))

    def vlq(v):
        v = max(0, int(v))                  # 负数会让 while 永不结束
        out = bytearray([v & 0x7F])
        v >>= 7
        while v:
            out.insert(0, (v & 0x7F) | 0x80)
            v >>= 7
        return bytes(out)

    all_ev.sort(key=lambda e: (e[0], e[1]))
    body = bytearray()
    body += b'\x00\xFF\x51\x03' + struct.pack('>I', base_tempo)[1:]
    last = 0
    # tempo 事件（来自 8A 命令）并进同一个有序流
    merged = [(tick, -1, b'\xFF\x51\x03' + struct.pack('>I', us)[1:])
              for tick, us in sorted(set(all_tempos))]
    merged += [(tick, prio, raw) for tick, prio, raw in all_ev]
    merged.sort(key=lambda e: (e[0], e[1]))
    for tick, prio, raw in merged:
        body += vlq(tick - last) + raw
        last = max(last, tick)
    body += b'\x00\xFF\x2F\x00'
    tracks.append(bytes(body))

    out = bytearray(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), TPQ))
    for t in tracks:
        out += b'MTrk' + struct.pack('>I', len(t)) + t
    return bytes(out), warnings


def convert(data, out_path):
    smf, warnings = build_smf(data)
    open(out_path, 'wb').write(smf)
    return out_path, warnings


if __name__ == '__main__':
    import sys
    import zipfile
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    z = zipfile.ZipFile(sys.argv[1])
    outdir = sys.argv[2] if len(sys.argv) > 2 else '.'
    for name in sorted(z.namelist()):
        if not name.upper().endswith('.MS') or name.upper().startswith('INIT'):
            continue
        p, w = convert(z.read(name), os.path.join(outdir, os.path.splitext(name)[0] + '.mid'))
        print('%s → %s  警告 %d' % (name, p, len(w)))
        for x in w[:4]:
            print('   ', x)
