# -*- coding: utf-8 -*-
"""对比 04 号曲子和参考 MIDI（自带音程比对，不依赖其它脚本）。"""
import collections
import glob
import os

import mido

REF_DIR = r'D:\music\90S Galgame music\壳中的小鸟'
OURS = r'D:\music\90S Galgame music\壳中的小鸟\PC98-MIDI'
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


refs = glob.glob(os.path.join(REF_DIR, '*.mid'))
ours = glob.glob(os.path.join(OURS, '04*.mid'))
print('参考:', [os.path.basename(x) for x in refs])
print('我们:', [os.path.basename(x) for x in ours])
print()
for o in ours:
    mo = mido.MidiFile(o)
    no = sum(1 for tr in mo.tracks for x in tr
             if x.type == 'note_on' and x.velocity > 0)
    so = chan_seqs(o)
    for r in refs:
        mr = mido.MidiFile(r)
        nr = sum(1 for tr in mr.tracks for x in tr
                 if x.type == 'note_on' and x.velocity > 0)
        print('%-44s vs %-30s %5.0f/%5.0f秒 %4d/%4d音  音程 %.2f'
              % (os.path.basename(o)[:42], os.path.basename(r)[:28],
                 mo.length, mr.length, no, nr, best_sim(so, chan_seqs(r))))
