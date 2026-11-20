# -*- coding: utf-8 -*-
"""在两个 MIDI 之间尝试半音平移，找最佳音高重合度。"""
import collections
import sys

import mido


def pitch_counter(path):
    m = mido.MidiFile(path)
    c = collections.Counter()
    for tr in m.tracks:
        for msg in tr:
            if msg.type == 'note_on' and msg.velocity > 0:
                c[msg.note] += 1
    return c, m.length


a, b = sys.argv[1], sys.argv[2]
ca, la = pitch_counter(a)
cb, lb = pitch_counter(b)
print('A: %d 音 %.1f 秒   B: %d 音 %.1f 秒' % (sum(ca.values()), la, sum(cb.values()), lb))
best = None
for shift in range(-24, 25):
    shifted = collections.Counter()
    for n, v in ca.items():
        k = n + shift
        if 0 <= k <= 127:
            shifted[k] += v
    inter = sum((shifted & cb).values())
    union = sum((shifted | cb).values())
    j = inter / union if union else 0
    if best is None or j > best[1]:
        best = (shift, j)
    if j > 0.5:
        print('  平移 %+d → 重合 %.2f' % (shift, j))
print('最佳平移 %+d，重合 %.2f' % best)
