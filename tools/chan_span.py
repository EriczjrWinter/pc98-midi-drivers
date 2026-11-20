# -*- coding: utf-8 -*-
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timer import note_seconds

for label, p in (('参考', sys.argv[1]), ('我们', sys.argv[2])):
    ns = note_seconds(p)
    last = collections.defaultdict(float)
    first = collections.defaultdict(lambda: 1e9)
    for t, c, v in ns:
        last[c] = max(last[c], t)
        first[c] = min(first[c], t)
    print('%s: %d 音，末音 %.1f 秒' % (label, len(ns), max(t for t, _, _ in ns)))
    print('   各通道 首音→末音:',
          {c: '%.0f→%.0f' % (first[c], last[c]) for c in sorted(last)})
