# -*- coding: utf-8 -*-
import os
import re
import zipfile

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')

want = r'(?i)MMD\.COM'
shown = 0
for fn in sorted(os.listdir(XDIR)):
    if not fn.endswith('.xml'):
        continue
    t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
    for b in re.split(r'<game>', t):
        if not re.search(want, b):
            continue
        nm = re.search(r'<name>([^<]+)</name>', b)
        a = re.search(r'archive="([^"]+)"', b)
        if not nm or not a:
            continue
        zp = os.path.join(H, 'pc98', a.group(1) + '.zip')
        if not os.path.exists(zp):
            continue
        print('【%s】  archive=%s' % (nm.group(1), a.group(1)))
        try:
            names = zipfile.ZipFile(zp).namelist()
        except Exception as e:
            print('  读取失败', e)
            continue
        drv = [n for n in names if re.search(r'(?i)\.(com|sys|drv)$', n)]
        data = [n for n in names if not re.search(r'(?i)\.(com|sys|drv)$', n)]
        print('   驱动:', ', '.join(sorted(drv)))
        print('   其它: %d 个, 例: %s' % (len(data), ', '.join(sorted(data)[:6])))
        print()
        shown += 1
        if shown >= 4:
            raise SystemExit
