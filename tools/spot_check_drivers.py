# -*- coding: utf-8 -*-
"""抽查几个「我方计数说有 MIDI 变体、但对方没提」的作品。"""
import os
import re
import zipfile

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
TARGETS = ('yojus2', 'cybalpha', 'rouge_d', 'hsuna3', 'heart_r',
           'brm2', 'libido7', 'shinc', 'narumj', 'faladia')

for company in ('do', 'foster', 'zyx'):
    t = open(os.path.join(X, company + '.xml'), encoding='utf-8',
             errors='replace').read()
    for b in re.split(r'<game>', t):
        nm = re.search(r'<name>([^<]+)</name>', b)
        a = re.search(r'archive="([^"]+)"', b)
        if not nm or not a:
            continue
        if not any(k in a.group(1).lower() for k in TARGETS):
            continue
        midi = bool(re.search(r'name="midiout"\s+value="1"', b))
        code = re.findall(r'<rom type="code"[^>]*>([^<]+)</rom>', b)
        files = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
        ext = {}
        for f in files:
            e = os.path.splitext(f)[1].upper() or '(无)'
            ext[e] = ext.get(e, 0) + 1
        print('%-46s %-14s midi=%-5s code=%s'
              % (nm.group(1)[:44], a.group(1), midi, code[:3]))
        print('      数据: %s' % dict(sorted(ext.items(), key=lambda x: -x[1])[:5]))
