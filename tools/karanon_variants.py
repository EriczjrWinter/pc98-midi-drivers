# -*- coding: utf-8 -*-
"""列出 karanon_98 每个变体各加载哪些数据文件。"""
import os
import re
from collections import Counter

H = r'D:\GamedataUnpack\hoot20251231\xml'
t = open(os.path.join(H, 'blackpackage.xml'), encoding='utf-8',
         errors='replace').read()

for b in re.split(r'<game>', t):
    a = re.search(r'archive="([^"]+)"', b)
    nm = re.search(r'<name>([^<]+)</name>', b)
    if not a or not nm or a.group(1) != 'karanon_98':
        continue
    roms = re.findall(r'<rom type="([^"]+)"[^>]*>([^<]+)</rom>', b)
    code = [f for typ, f in roms if typ == 'code']
    bgm = [f for typ, f in roms if typ != 'code']
    suf = Counter()
    for f in bgm:
        m = re.search(r'(?:MD_\d+)?(_?)(GS|88|B2|SB|N)?\.(MS)$', f, re.I)
        e = os.path.splitext(f)[1].upper()
        k = re.sub(r'^MD_\d+', '', os.path.splitext(f)[0]).upper()
        suf[k[:4]] += 1
    print('===', nm.group(1))
    print('   驱动:', code[:3])
    print('   数据 %d 个，后缀分布: %s'
          % (len(bgm), dict(suf.most_common(6))))
