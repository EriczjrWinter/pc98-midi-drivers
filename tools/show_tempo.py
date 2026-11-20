# -*- coding: utf-8 -*-
import sys

import mido

m = mido.MidiFile(sys.argv[1])
print('TPQ =', m.ticks_per_beat)
t = 0
for tr in m.tracks:
    t = 0
    for msg in tr:
        t += msg.time
        if msg.type == 'set_tempo':
            print('  tempo %d us/qn (%.2f BPM) @tick %d' % (msg.tempo, 60e6 / msg.tempo, t))
print('总长 %.2f 秒' % m.length)
