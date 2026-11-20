# -*- coding: utf-8 -*-
"""把 MIDI 的事件换算成「真实秒」，考虑文件自己的 tempo 映射。

用法：
  python timer.py <a.mid> <b.mid> [通道] [起始秒] [结束秒]
"""
import sys

import mido


def note_seconds(path, ch=None):
    m = mido.MidiFile(path)
    tempo = 500000
    out = []
    # 合并所有轨道的 delta 需要按绝对 tick 处理，这里逐轨累计再统一换算
    events = []      # (绝对tick, 类型, 通道, 值)
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'set_tempo':
                events.append((t, 'tempo', 0, msg.tempo))
            elif msg.type == 'note_on' and msg.velocity > 0:
                events.append((t, 'note', msg.channel, msg.note))
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'tempo' else 1))
    last_tick = 0
    sec = 0.0
    for tick, kind, c, v in events:
        sec += (tick - last_tick) * tempo / 1e6 / m.ticks_per_beat
        last_tick = tick
        if kind == 'tempo':
            tempo = v
        elif ch is None or c == ch:
            out.append((round(sec, 3), c, v))
    return out


def main():
    a, b = sys.argv[1], sys.argv[2]
    ch = int(sys.argv[3]) if len(sys.argv) > 3 else None
    t0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    t1 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
    na = [x for x in note_seconds(a, ch) if t0 <= x[0] < t1]
    nb = [x for x in note_seconds(b, ch) if t0 <= x[0] < t1]
    print('通道 %s  时间 %s..%s 秒' % (ch if ch is not None else '全部', t0, t1))
    print('参考 %d 音:' % len(na), [(t, v) for t, _, v in na][:20])
    print('我们 %d 音:' % len(nb), [(t, v) for t, _, v in nb][:20])
    if na and nb:
        print('首个音时间差: %.3f 秒' % (nb[0][0] - na[0][0]))


if __name__ == '__main__':
    main()
