# -*- coding: utf-8 -*-
"""列出没有独立驱动文件的 D.O. 包里的可执行文件。"""
import os
import zipfile

PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
PACKS = ['brm2_98', 'cybalpha_98', 'rouge_d_98', 'hsuna3_98',
         'heart_r_98', 'yojus2_98', 'trigger2_98']

for p in PACKS:
    zp = os.path.join(PC98, p + '.zip')
    if not os.path.exists(zp):
        print('%-16s 包不存在' % p)
        continue
    z = zipfile.ZipFile(zp)
    exe = [(i.filename, i.file_size) for i in z.infolist()
           if not i.is_dir()
           and (i.filename.upper().endswith(('.EXE', '.COM', '.DRV', '.BIN'))
                or '.' not in os.path.basename(i.filename))]
    print('%-16s' % p)
    for n, s in sorted(exe, key=lambda x: -x[1])[:5]:
        print('     %-16s %7d' % (n, s))
