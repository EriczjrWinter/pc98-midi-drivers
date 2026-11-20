# -*- coding: utf-8 -*-
"""用 Win95 GM 版 MIDI 校准时间轴：DP 对齐音高序列 + 最小二乘拟合。"""
import os
import sys

import mido

from . import capture as midicap
from . import smf as view

REF_DIR = r'D:\music\90S Galgame music\水晶迷宫-逢魔的迷宫'


def ref_notes(path):
    m = mido.MidiFile(path)
    ev = []
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                ev.append((t, msg.note))
    ev.sort()
    return ev, m


def our_notes(pack, name, ticks=60000):
    sim, n = midicap.capture(midicap.load_track(pack, name), ticks=ticks)
    msgs = view.parse(sim.midi)
    out = []
    for t, m in msgs:
        if 0x90 <= m[0] < 0xA0 and len(m) > 2 and m[2] > 0 and m[1] > 0:
            if out and out[-1] == (t, m[1]):
                continue
            out.append((t, m[1]))
    return out


def dp_align(ref, ours, band=250):
    """返回 [(ri, oi)] —— 音高相同的对齐点。"""
    n, m = len(ref), len(ours)
    NEG = -10 ** 9
    # 只保留音高序列
    R = [r[1] for r in ref]
    O = [o[1] for o in ours]
    prev = [NEG] * (m + 1)
    prev[0] = 0
    back = [[2] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cur = [NEG] * (m + 1)
        lo = max(1, i - band)
        hi = min(m, i + band)
        for j in range(lo, hi + 1):
            best, bk = prev[j - 1] + (4 if R[i - 1] == O[j - 1] else -2), 1
            if prev[j] - 1 > best:
                best, bk = prev[j] - 1, 2
            if cur[j - 1] - 1 > best:
                best, bk = cur[j - 1] - 1, 3
            cur[j] = best
            back[i][j] = bk
        prev = cur
    # 回溯
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        bk = back[i][j]
        if bk == 1:
            if R[i - 1] == O[j - 1]:
                pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif bk == 2:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs


def fit(pairs, ref, ours):
    xs = [ours[j][0] for _, j in pairs]
    ys = [ref[i][0] for i, _ in pairs]
    k = len(xs)
    mx, my = sum(xs) / k, sum(ys) / k
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    return a, b


if __name__ == '__main__':
    ref, m = ref_notes(os.path.join(REF_DIR, 'CR001.MID'))
    ours = our_notes('cl_98', 'CR001C.FMD',
                     ticks=int(sys.argv[1]) if len(sys.argv) > 1 else 60000)
    pairs = dp_align(ref, ours)
    print('ref %d notes, ours %d notes, aligned %d' % (len(ref), len(ours), len(pairs)))
    a, b = fit(pairs, ref, ours)
    tempo = [msg.tempo for tr in m.tracks for msg in tr if msg.type == 'set_tempo'][0]
    ref_tick_ms = tempo / 1e6 / m.ticks_per_beat * 1000
    print('ref BPM %.2f, ref tick %.4f ms' % (60e6 / tempo, ref_tick_ms))
    print('ref_tick = %.4f * our_tick + %.1f  =>  our tick = %.4f ms'
          % (a, b, ref_tick_ms * a))
    print('first 8 pairs:', [(ref[i][0], ours[j][0]) for i, j in pairs[:8]])
