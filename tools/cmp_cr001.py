# -*- coding: utf-8 -*-
"""对比 Win95 版 CR001.MID 和仿真器刚导出的 test_CR001C.mid。"""
import os
import sys

import mido


def info(path):
    m = mido.MidiFile(path)
    notes = sum(1 for tr in m.tracks for x in tr
                if x.type == 'note_on' and x.velocity > 0)
    progs = sorted({x.program for tr in m.tracks for x in tr
                    if x.type == 'program_change'})
    tempos = []
    t = 0
    for tr in m.tracks:
        t = 0
        for x in tr:
            t += x.time
            if x.type == 'set_tempo':
                tempos.append((round(t, 1), round(60e6 / x.tempo, 1)))
    return {'tracks': len(m.tracks), 'tpq': m.ticks_per_beat,
            'len': m.length, 'notes': notes, 'progs': progs, 'tempos': tempos}


REF = r'D:\music\90S Galgame music\水晶迷宫-逢魔的迷宫\CR001.MID'
GEN = r'D:\gf\pc98-midi-drivers\build\hootcap\test_CR001C.mid'

for label, p in (('Win95 CR001.MID', REF), ('仿真 test_CR001C', GEN)):
    if not os.path.exists(p):
        print('%-20s 不存在' % label)
        continue
    i = info(p)
    print('%-20s %d 轨 TPQ=%-3d %6.1f 秒 %5d 音符'
          % (label, i['tracks'], i['tpq'], i['len'], i['notes']))
    print('%-20s 音色 %s' % ('', i['progs'][:10]))
    print('%-20s tempo %s' % ('', i['tempos'][:6]))
