# -*- coding: utf-8 -*-
"""列出本地 pc98 包里「未分析的 MIDI 驱动」及其所属游戏名。

方便和 D:\\music\\90S Galgame music 里已有的 MIDI 对照，判断能不能 PASS。
"""
import os
import re
import zipfile

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')
PDIR = os.path.join(H, 'pc98')

# 已分析
DONE = {'MMDR.COM', 'MMDR_98.COM', 'MMD.COM', 'MMP_HOOT.COM',
        'PMD.COM', 'PMD_98.COM', 'PMDB2.COM'}
# 明显是 FM 侧的，跳过
FMISH = {'OPNDRV.COM', 'FMP3.COM', 'TGLFMP.COM', 'TGLFMP2.COM',
         'IBGMP.COM', 'IBGMPM.COM', 'FGPLAY_H.COM'}

local = {f[:-4] for f in os.listdir(PDIR) if f.lower().endswith('.zip')}

info = {}
for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    company = fn[:-4]
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        a = re.search(r'archive="([^"]+)"', b)
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not a or not nm or a.group(1) not in local:
            continue
        if not re.search(r'name="midiout"\s+value="1"', b):
            continue
        roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
        drv = [r.upper() for r in roms if r.upper().endswith(('.COM', '.SYS', '.DRV'))]
        drv = [d for d in drv if d not in DONE and d not in FMISH]
        if not drv:
            continue
        data = [r for r in roms if not r.upper().endswith(('.COM', '.SYS', '.DRV'))]
        info.setdefault(a.group(1), []).append((company, nm.group(1), drv, data))

print('本地包中、带未分析 MIDI 驱动的：%d 个\n' % len(info))
for arch, entries in sorted(info.items()):
    for company, name, drv, data in entries:
        ext = {}
        for d in data:
            e = os.path.splitext(d)[1].upper() or '(无)'
            ext[e] = ext.get(e, 0) + 1
        print('%-14s %-40s' % (arch, name[:38]))
        print('    会社: %-14s 驱动: %s' % (company, ','.join(drv)))
        print('    数据: %s' % ', '.join('%s×%d' % (k, v) for k, v in sorted(ext.items())))
