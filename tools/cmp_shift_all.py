# -*- coding: utf-8 -*-
"""按文件名里的编号配对（我们的 EMI_NN ↔ 参考 Track NN），求最佳半音平移。"""
import collections
import glob
import os
import re
import sys

import mido


def num_of(path):
    m = re.search(r'(\d+)', os.path.basename(path))
    return int(m.group(1)) if m else -1


def prof(path):
    m = mido.MidiFile(path)
    c = collections.Counter()
    n = 0
    for tr in m.tracks:
        for msg in tr:
            if msg.type == 'note_on' and msg.velocity > 0:
                c[msg.note] += 1
                n += 1
    return c, n, m.length


da, db = sys.argv[1], sys.argv[2]
pa, pb = sys.argv[3], sys.argv[4]
ours = {num_of(f): f for f in glob.glob(os.path.join(da, pa))}
refs = {num_of(f): f for f in glob.glob(os.path.join(db, pb))}

print('%-28s %6s %6s %7s %7s %5s %6s' % ('曲', '音', '参考音', '时长', '参考时长', '平移', '重合'))
print('-' * 78)
agree = 0
for k in sorted(ours):
    if k not in refs:
        print('%-28s  (参考缺 %02d)' % (os.path.basename(ours[k])[:26], k))
        continue
    ca, na, la = prof(ours[k])
    cb, nb, lb = prof(refs[k])
    best = (0, 0.0)
    for s in range(-24, 25):
        sh = collections.Counter({n + s: v for n, v in ca.items() if 0 <= n + s <= 127})
        inter = sum((sh & cb).values())
        union = sum((sh | cb).values())
        j = inter / union if union else 0
        if j > best[1]:
            best = (s, j)
    if best[1] > 0.25:
        agree += 1
    print('%-28s %6d %6d %7.1f %7.1f %+5d %6.2f' % (
        os.path.basename(ours[k])[:26], na, nb, la, lb, best[0], best[1]))
print('\n重合 > 0.25 的：%d 首' % agree)
