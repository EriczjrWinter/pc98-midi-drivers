# -*- coding: utf-8 -*-
"""全交叉：为每首「我们的」找最像的「参考」，允许半音平移。"""
import collections
import glob
import os
import re
import sys

import mido


def num_of(p):
    m = re.search(r'(\d+)', os.path.basename(p))
    return int(m.group(1)) if m else -1


def prof(path):
    m = mido.MidiFile(path)
    c = collections.Counter()
    for tr in m.tracks:
        for msg in tr:
            if msg.type == 'note_on' and msg.velocity > 0:
                c[msg.note] += 1
    return c, m.length


def best_shift(ca, cb):
    best = (0, 0.0)
    for s in range(-24, 25):
        sh = collections.Counter({n + s: v for n, v in ca.items() if 0 <= n + s <= 127})
        inter = sum((sh & cb).values())
        union = sum((sh | cb).values())
        j = inter / union if union else 0
        if j > best[1]:
            best = (s, j)
    return best


da, db = sys.argv[1], sys.argv[2]
fa = sorted(glob.glob(os.path.join(da, sys.argv[3])))
fb = sorted(glob.glob(os.path.join(db, sys.argv[4])))
pa = [(f, *prof(f)) for f in fa]
pb = [(f, *prof(f)) for f in fb]

print('%-26s → %-14s %5s %6s' % ('我们', '最像的参考', '平移', '重合'))
print('-' * 62)
for f, ca, la in pa:
    scored = []
    for g, cb, lb in pb:
        s, j = best_shift(ca, cb)
        scored.append((j, s, g, lb))
    scored.sort(reverse=True)
    j, s, g, lb = scored[0]
    flag = '' if j > 0.35 else ('  ?' if j > 0.15 else '  ??')
    print('%-26s → %-14s %+5d %6.2f%s' % (
        os.path.basename(f)[:24], os.path.basename(g)[:12], s, j, flag))
