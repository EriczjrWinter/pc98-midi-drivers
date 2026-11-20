# -*- coding: utf-8 -*-
"""按 10 秒分桶比较两个 MIDI 在指定通道上的音符密度。"""
import collections
import sys

import mido


def load(path, ch):
    m = mido.MidiFile(path)
    sec = 60.0 / 500000.0 / m.ticks_per_beat   # 默认 tempo 假设
    # 用 mido 的实际时间更准
    out = []
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0 and msg.channel == ch:
                out.append(t)
    # mido 的 time 已是 tick，需要换算
    return m, out


def ticks_to_sec(m):
    """用 mido 遍历一次求平均值——简化：按 500000us/qn 计算。"""
    return 500000.0 / 1e6 / m.ticks_per_beat


def buckets(path, ch, width=10.0):
    m = mido.MidiFile(path)
    sec_per_tick = ticks_to_sec(m)
    c = collections.Counter()
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0 and msg.channel == ch:
                c[int(t * sec_per_tick / width)] += 1
    return c


a, b, ch = sys.argv[1], sys.argv[2], int(sys.argv[3])
ca = buckets(a, ch)
cb = buckets(b, ch)
print('通道 %d，每 %d 秒的音符数' % (ch, 10))
print('%-8s %6s %6s' % ('时间段', '参考', '我们'))
for k in sorted(set(ca) | set(cb)):
    flag = '  <<<' if cb.get(k, 0) > ca.get(k, 0) * 1.5 + 5 else ''
    print('%3d-%3d   %6d %6d%s' % (k * 10, k * 10 + 10, ca.get(k, 0), cb.get(k, 0), flag))
