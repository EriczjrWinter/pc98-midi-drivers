# -*- coding: utf-8 -*-
"""检查：没有独立驱动文件的 D.O. 包，是不是把 MDRV98 嵌进了游戏 EXE。

做法：取 MDRV98 里一段有辨识度的字节，在包的 EXE 里搜。
"""
import os
import zipfile

PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
DRV = r'D:\gf\pc98-midi-drivers\drivers\dofmdx\src\MDRV98'

drv = open(DRV, 'rb').read()
# 取跳转表附近 + 函数 0 开头，辨识度高
sig = drv[0x29:0x29 + 32]
print('签名（MDRV98 0x29 起 32 字节）:', sig.hex(' '))
print()

PACKS = ['cl_98', 'zatuon_98', 'brm2_98', 'cybalpha_98', 'rouge_d_98',
         'hsuna3_98', 'heart_r_98', 'yojus2_98', 'cryswepr_21', 'trigger2_98']

for p in PACKS:
    zp = os.path.join(PC98, p + '.zip')
    if not os.path.exists(zp):
        print('%-16s 包不存在' % p)
        continue
    z = zipfile.ZipFile(zp)
    found = []
    for n in z.namelist():
        if not n.upper().endswith(('.EXE', '.COM', '.BIN', '')):
            continue
        try:
            d = z.read(n)
        except Exception:
            continue
        if sig in d:
            found.append('%s(%d)' % (n, len(d)))
    print('%-16s %s' % (p, ', '.join(found) if found else '★ 没找到签名'))
