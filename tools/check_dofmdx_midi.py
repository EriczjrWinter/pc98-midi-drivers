# -*- coding: utf-8 -*-
"""精确统计：D.O. 系作品的变体构成（哪些是真 MIDI）。"""
import collections
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
MIDI_LIKE = ('MT-32', 'GS', 'GM', 'SC-88', 'CM-64')

for company in ('do', 'foster', 'zyx'):
    t = open(os.path.join(X, company + '.xml'), encoding='utf-8',
             errors='replace').read()
    kinds = collections.Counter()
    works_midi = set()
    works_all = set()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm:
            continue
        midi = bool(re.search(r'name="midiout"\s+value="1"', b))
        title = nm.group(1)
        base = re.sub(r'^\[[^\]]*\]\s*', '', title)
        base = re.sub(r'\([^)]*\)\s*$', '', base).strip()
        m = re.search(r'\(([^)]+)\)\s*$', title)
        var = m.group(1) if m else '(无)'
        works_all.add(base)
        kinds[var] += 1
        if midi and any(k.upper() in var.upper() for k in MIDI_LIKE):
            works_midi.add(base)

    allm = sum(v for k, v in kinds.items()
               if any(x.upper() in k.upper() for x in MIDI_LIKE))
    print('%s: 共 %d 作品 / %d 条目；有真 MIDI 变体的作品 %d 部，MIDI 条目 %d 个'
          % (company, len(works_all), sum(kinds.values()), len(works_midi), allm))
    print('   变体分布:', dict(kinds.most_common(8)))
