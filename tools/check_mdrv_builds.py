# -*- coding: utf-8 -*-
"""检查 D.O. 系各包里的 MDRV98 / dofmd_98.bin 是不是同一构建。"""
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

print('相关包:', len(archives))
hashes = collections.defaultdict(list)
missing = []
for a in sorted(archives):
    zp = os.path.join(PC98, a + '.zip')
    if not os.path.exists(zp):
        missing.append(a)
        continue
    try:
        z = zipfile.ZipFile(zp)
    except Exception:
        missing.append(a)
        continue
    names = {n.upper(): n for n in z.namelist()}
    found = False
    for key in ('MDRV98', 'MDRV98.COM', 'ZYXMD'):
        if key in names:
            d = z.read(names[key])
            hashes[hashlib.md5(d).hexdigest()[:10]].append((a, len(d)))
            found = True
    if not found:
        missing.append(a)

print('\nMDRV98 的构建分布:')
for h, v in sorted(hashes.items(), key=lambda x: -len(x[1])):
    sizes = sorted(set(s for _, s in v))
    print('  %s  %2d 个包  大小 %s' % (h, len(v), sizes))
    print('       ', ', '.join(a for a, _ in v[:14]))

if missing:
    print('\n没找到 MDRV98 的包 (%d):' % len(missing))
    print('   ', ', '.join(missing[:20]))
