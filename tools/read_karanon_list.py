# -*- coding: utf-8 -*-
import os

P = r'D:\music\90S Galgame music\壳中的小鸟'
for f in ('Kara no Naka no Kotori.txt', 'Kara no Naka no Kotori.m3u'):
    p = os.path.join(P, f)
    raw = open(p, 'rb').read()
    t = None
    for enc in ('utf-8-sig', 'cp932', 'utf-8', 'latin1'):
        try:
            t = raw.decode(enc)
            print('=== %s (%s)' % (f, enc))
            break
        except Exception:
            continue
    print(t[:900] if t else '(解码失败)')
    print()
