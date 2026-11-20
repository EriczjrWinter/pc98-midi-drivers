# -*- coding: utf-8 -*-
"""导出 殻の中の小鳥 的 .MS → MIDI（用解出来的 8A 速度）。"""
import io
import os
import sys
import zipfile

import mido

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\msdrv\src')
import ms_parser as M

OUT = r'D:\music\90S Galgame music\壳中的小鸟\PC98-MIDI'
TITLES = {
    1: 'Heels Beat on the Stone Paving',
    2: 'Drops are Dots, Vessels are Faces',
    3: 'One and Two and Three',
    4: 'A Bird Flies Even Without Wind',
    5: 'An Erased Voice is Noise',
    6: 'An Invisible Chain Hurts Her Neck',
    7: 'A Broken Piano Will Not Play',
    8: 'White Virgin, Black Slave',
    9: "To Dream is a Lady's Privilege",
}
BAD = '\\/:*?"<>|'


def safe(s):
    for c in BAD:
        s = s.replace(c, '_')
    return s


z = zipfile.ZipFile(r'D:\GamedataUnpack\hoot20251231\pc98\karanon_98.zip')
os.makedirs(OUT, exist_ok=True)
n = 0
for i in range(1, 10):
    for suf, lab in (('GS', 'SC-55'), ('88', 'SC-88')):
        name = 'MD_%02d_%s.MS' % (i, suf)
        try:
            d = z.read(name)
        except KeyError:
            continue
        smf, w = M.build_smf(d)
        m = mido.MidiFile(file=io.BytesIO(smf))
        fn = '%02d %s [%s].mid' % (i, safe(TITLES[i]), lab)
        open(os.path.join(OUT, fn), 'wb').write(smf)
        notes = sum(1 for tr in m.tracks for x in tr
                    if x.type == 'note_on' and x.velocity > 0)
        chs = sorted(set(x.channel for tr in m.tracks for x in tr
                         if x.type == 'note_on'))
        print('%-44s %6.1f秒 %5d音符 ch=%d' % (fn[:42], m.length, notes, len(chs)))
        n += 1
print('共', n, '个')
