# -*- coding: utf-8 -*-
"""从 VGMRips 缓存页里抽 Filsnown 的完整曲目表。"""
import re

P = (r'C:\Users\ericz\AppData\Local\Temp\dsh-spill-EMoT1X'
     r'\session-5b04afc5a6be\b801c6348f2a-web_fetch.txt')
t = open(P, encoding='utf-8', errors='replace').read()

rows = []
for m in re.finditer(r'data-order="(\d\d)"[^>]*?(?:.*?)<a class="beginPlay"[^>]*>([^<]+)</a>',
                     t, re.S):
    rows.append((m.group(1), m.group(2)))

# 去重（页面里每行出现两次）
seen = set()
out = []
for n, ti in rows:
    if n in seen:
        continue
    seen.add(n)
    out.append((n, ti))
out.sort()
for n, ti in out:
    print(n, ti)
print('共', len(out))
