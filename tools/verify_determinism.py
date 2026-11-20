# -*- coding: utf-8 -*-
"""确定性检验：重跑各管线，和已交付的文件比对 md5。

如果 md5 一致，说明后续的代码改动没有改变输出。
"""
import hashlib
import io
import os
import sys
import zipfile

import mido

H = r'D:\GamedataUnpack\hoot20251231\pc98'
MUS = r'D:\music\90S Galgame music'


def md5(b):
    return hashlib.md5(b).hexdigest()


def check(label, generated, delivered):
    if not os.path.exists(delivered):
        print('%-22s 交付文件不存在: %s' % (label, os.path.basename(delivered)))
        return
    a = md5(generated)
    b = md5(open(delivered, 'rb').read())
    ok = '✅ 一致' if a == b else '❌ 不一致'
    print('%-22s %s  gen=%s  file=%s' % (label, ok, a[:10], b[:10]))


# ---- MS.COM ----
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\mscom\src')
import mscom_emu as MS

z = zipfile.ZipFile(os.path.join(H, 'dr^2_98.zip'))
data = z.read('MRJ_GS01.MID')
# 驱动本体不入库，现场从 zip 解到临时目录
import tempfile
tmpd = tempfile.mkdtemp()
drv = os.path.join(tmpd, 'ms.com')
open(drv, 'wb').write(zipfile.ZipFile(os.path.join(H, 'filsnown_98.zip')).read('MS.COM'))
m = MS.MSCom(driver=drv)
stream = m.export(data)
period = MS.scan_timer_writes(m.timer_writes, m.tick)
acc = [0.0] * (m.tick + 2)
for i in range(1, m.tick + 2):
    acc[i] = acc[i - 1] + period[i - 1]
ms = [(acc[t], b) for t, b in stream]
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')
import smf_build
smf, _, _ = smf_build.build_ms(ms)
check('MS.COM 雀鬼 02', smf,
      os.path.join(MUS, 'DR2ナイト雀鬼', '02 Trance Mind.mid'))

# ---- MMD ----
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\mmd\src')
import mmd_parser as MP

d = zipfile.ZipFile(os.path.join(H, 'eime_98.zip')).read('EMI_01.MMD')
mm = MP.MMD(d)
smf2, _ = MP.build_smf(mm)
import glob
cand = glob.glob(os.path.join(MUS, "Amy's Fantasies (1996)", 'PC98-MDI', 'EMI_01*.mid'))
if cand:
    check('MMD eime EMI_01', smf2, cand[0])

# ---- MSDRV4 ----
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\msdrv\src')
import ms_parser as MSd

d2 = zipfile.ZipFile(os.path.join(H, 'karanon_98.zip')).read('MD_04_GS.MS')
smf3, _ = MSd.build_smf(d2)
cand2 = glob.glob(os.path.join(MUS, '壳中的小鸟', 'PC98-MIDI', '04*.mid'))
if cand2:
    check('MSDRV4 壳鸟 04', smf3, cand2[0])
