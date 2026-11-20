# -*- coding: utf-8 -*-
"""把 TH02 的 .MMD 转出来，按曲名匹配官方 MIDI 并对比。"""
import io
import os
import re
import sys
import zipfile

import mido

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\mmd\src')
import mmd_parser as P

ZIP = r'D:\GamedataUnpack\hoot20251231\pc98\tohofuma_98.zip'
OFF = r'D:\music\东方Project官方MIDI\01 - [TH02] 東方封魔録　～ The Story of Eastern Wonderland'


def norm(s):
    return re.sub(r'[\s\u3000]+', '', s).lower()


def stats_mido(m):
    notes = sum(1 for tr in m.tracks for msg in tr
                if msg.type == 'note_on' and msg.velocity > 0)
    return notes, m.length


z = zipfile.ZipFile(ZIP)
ours = []
for n in sorted(z.namelist()):
    if not n.upper().endswith('.MMD'):
        continue
    d = z.read(n)
    mm = P.MMD(d)
    smf, w = P.build_smf(mm)
    m = mido.MidiFile(file=io.BytesIO(smf))
    notes, ln = stats_mido(m)
    ours.append((os.path.basename(n), mm.title.strip(), notes, ln, smf, w))

off_files = [f for f in os.listdir(OFF) if f.lower().endswith('.mid')]
print('官方 MIDI: %d 个\n' % len(off_files))
print('%-10s %-24s %7s %7s  %s' % ('我们的', '曲名', '音符', '时长', '匹配到的官方文件'))
print('-' * 92)
used = set()
for name, title, notes, ln, smf, w in ours:
    key = norm(title)
    hit = None
    for f in off_files:
        if key and key[:8] in norm(f):
            hit = f
            break
    if hit:
        used.add(hit)
        mo = mido.MidiFile(os.path.join(OFF, hit))
        on, ol = stats_mido(mo)
        print('%-10s %-24s %7d %7.1f  %s (%d 音 / %.1f 秒)'
              % (name, title[:22], notes, ln, hit[:34], on, ol))
    else:
        print('%-10s %-24s %7d %7.1f  —' % (name, title[:22], notes, ln))
print('\n未匹配到的官方文件:', [f for f in off_files if f not in used][:8])
