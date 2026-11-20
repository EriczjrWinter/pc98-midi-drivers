# -*- coding: utf-8 -*-
"""把一批「我们的转出」和一批「参考」做全矩阵比对，看排序是否对得上。

相似度 = 音高多重集的重合度（Jaccard 风格），再附上时长/音符数参考。
"""
import collections
import glob
import os
import sys

import mido


def profile(path):
    m = mido.MidiFile(path)
    notes = []
    for tr in m.tracks:
        for msg in tr:
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append((msg.channel, msg.note))
    return {
        'notes': len(notes),
        'len': m.length,
        'pitch': collections.Counter(n for _, n in notes),
        'chan': collections.Counter(c for c, _ in notes),
    }


def jaccard(a, b):
    inter = sum((a['pitch'] & b['pitch']).values())
    union = sum((a['pitch'] | b['pitch']).values())
    return inter / union if union else 0.0


def main():
    dir_a, dir_b = sys.argv[1], sys.argv[2]
    pat_a = sys.argv[3] if len(sys.argv) > 3 else '*.mid'
    pat_b = sys.argv[4] if len(sys.argv) > 4 else '*.mid'
    fa = sorted(glob.glob(os.path.join(dir_a, pat_a)))
    fb = sorted(glob.glob(os.path.join(dir_b, pat_b)))
    print('我们的: %d 个   参考: %d 个' % (len(fa), len(fb)))
    pa = [profile(f) for f in fa]
    pb = [profile(f) for f in fb]

    print('\n按文件名顺序一一对应：')
    print('%-28s %7s %7s %7s %7s  %s' % ('我们', '音符', '参考音符', '时长', '参考时长', '音高重合'))
    for i in range(min(len(fa), len(fb))):
        j = jaccard(pa[i], pb[i])
        flag = '' if j > 0.7 else ('  ← 差异大' if j > 0.2 else '  ← 几乎无关')
        print('%-28s %7d %7d %7.1f %7.1f  %5.2f%s' % (
            os.path.basename(fa[i])[:26], pa[i]['notes'], pb[i]['notes'],
            pa[i]['len'], pb[i]['len'], j, flag))

    print('\n每首我们最像的参考：')
    for i, f in enumerate(fa):
        best = max(range(len(pb)), key=lambda k: jaccard(pa[i], pb[k]))
        j = jaccard(pa[i], pb[best])
        print('%-28s → %-14s %.2f' % (os.path.basename(f)[:26],
                                      os.path.basename(fb[best])[:12], j))


if __name__ == '__main__':
    main()
