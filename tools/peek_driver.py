# -*- coding: utf-8 -*-
"""列出本地含指定驱动的包，以及包内文件构成。"""
import os
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231'
PDIR = os.path.join(H, 'pc98')

target = (sys.argv[1] if len(sys.argv) > 1 else 'MMD.COM').upper()

for f in sorted(os.listdir(PDIR)):
    if not f.lower().endswith('.zip'):
        continue
    zp = os.path.join(PDIR, f)
    try:
        names = zipfile.ZipFile(zp).namelist()
    except Exception:
        continue
    up = [n.upper() for n in names]
    if target not in up:
        continue
    drv = [n for n in names if n.upper().endswith(('.COM', '.SYS', '.DRV'))]
    data = [n for n in names if n not in drv]
    ext = {}
    for d in data:
        e = os.path.splitext(d)[1].upper() or '(无扩展名)'
        ext[e] = ext.get(e, 0) + 1
    print('【%s】 %d 个文件' % (f[:-4], len(names)))
    print('   驱动:', ', '.join(sorted(drv)))
    print('   数据:', ', '.join('%s×%d' % (k, v) for k, v in sorted(ext.items())))
    print()
