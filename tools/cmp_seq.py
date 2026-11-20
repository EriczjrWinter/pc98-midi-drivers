# -*- coding: utf-8 -*-
"""看某通道在某时间段内的音符序列，判断是否被重复播了两遍。"""
import sys

import mido


def seq(path, ch, t0, t1):
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
    return out


a, b, ch = sys.argv[1], sys.argv[2], int(sys.argv[3])
t0, t1 = float(sys.argv[4]), float(sys.argv[5])
sa = seq(a, ch, t0, t1)
sb = seq(b, ch, t0, t1)
print('参考 %d 音:' % len(sa), [n for _, n in sa][:24])
print('我们 %d 音:' % len(sb), [n for _, n in sb][:24])
