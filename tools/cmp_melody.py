# -*- coding: utf-8 -*-
"""按「单通道的音程序列」判断两首是否同一曲（对移调免疫）。

对每个文件，取音符最多的那个通道作为旋律通道。
"""
import collections
import glob
import os
import sys

import mido

N = 16


def chan_seqs(path):
    m = mido.MidiFile(path)
    per = collections.defaultdict(list)
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                per[msg.channel].append((t, msg.note))
    out = {}
    for ch, lst in per.items():
        lst.sort()
        ps = [n for _, n in lst[:N]]
        if len(ps) >= 5:
            out[ch] = [ps[i + 1] - ps[i] for i in range(len(ps) - 1)]
    return out


def best_sim(A, B):
    best = 0.0
    for a in A.values():
        for b in B.values():
            k = min(len(a), len(b))
            if k < 4:
                continue
            hit = sum(1 for i in range(k) if a[i] == b[i])
            best = max(best, hit / k)
    return best


da, db = sys.argv[1], sys.argv[2]
fa = sorted(glob.glob(os.path.join(da, sys.argv[3])))
fb = sorted(glob.glob(os.path.join(db, sys.argv[4])))
sa = {f: chan_seqs(f) for f in fa}
sb = {f: chan_seqs(f) for f in fb}

print('%-26s → %-14s 音程相似' % ('我们', '最像的参考'))
print('-' * 55)
for f in fa:
    best = (0.0, None)
    for g in fb:
        s = best_sim(sa[f], sb[g])
        if s > best[0]:
            best = (s, g)
    s, g = best
    flag = '' if s > 0.8 else ('  ?' if s > 0.5 else '')
    print('%-26s → %-14s %5.2f%s' % (os.path.basename(f)[:24],
                                     os.path.basename(g)[:12] if g else '-', s, flag))
