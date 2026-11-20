# -*- coding: utf-8 -*-
"""比对 D.O. 系各驱动的哈希，判断哪些其实是同一个文件。"""
import collections
import hashlib
import json
import os
import zipfile

PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'

rows = json.load(open(CAT, encoding='utf-8'))
archives = set()
for r in rows:
    if r['company'] in ('do', 'foster', 'zyx'):
        archives.update(r['archives'])

TARGETS = ('MDRV98', 'ZYXMD', 'ZYXMDP', 'MV23', 'DOFMD_98.BIN')
byhash = collections.defaultdict(list)

for a in sorted(archives):
    zp = os.path.join(PC98, a + '.zip')
    if not os.path.exists(zp):
        continue
    try:
        z = zipfile.ZipFile(zp)
    except Exception:
        continue
    names = {n.upper(): n for n in z.namelist()}
    for t in TARGETS:
        real = names.get(t.upper())
        if not real:
            continue
        d = z.read(real)
        h = hashlib.md5(d).hexdigest()[:10]
        byhash[h].append((a, t, len(d)))

print('驱动内容分组:')
for h, v in sorted(byhash.items(), key=lambda x: -len(x[1])):
    files = sorted(set(t for _, t, _ in v))
    sizes = sorted(set(s for _, _, s in v))
    print('  %s  %2d 个包  大小%s  文件名%s'
          % (h, len(v), sizes, files))
    print('       ', ', '.join(a for a, _, _ in v[:16]))
