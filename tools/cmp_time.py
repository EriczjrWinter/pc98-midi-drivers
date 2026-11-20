# -*- coding: utf-8 -*-
"""打印某通道一时间段的 (秒, 音符) 序列，用于比对时间对齐。"""
import sys

import mido


def seq(path, ch, t0, t1, limit=30):
    m = mido.MidiFile(path)
    spt = 500000.0 / 1e6 / m.ticks_per_beat
    out = []
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0 and msg.channel == ch:
                s = t * spt
                if t0 <= s < t1:
                    out.append((round(s, 3), msg.note))
    out.sort()
    return out[:limit]


a, b, ch = sys.argv[1], sys.argv[2], int(sys.argv[3])
t0, t1 = float(sys.argv[4]), float(sys.argv[5])
for label, p in (('参考', a), ('我们', b)):
    s = seq(p, ch, t0, t1)
    print('%s (%d):' % (label, len(s)), s)
