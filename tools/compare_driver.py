# -*- coding: utf-8 -*-
"""比较本地各包里同名驱动的实际内容。

用法：python compare_driver.py MMD.COM
"""
import hashlib
import os
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231'
PDIR = os.path.join(H, 'pc98')

target = (sys.argv[1] if len(sys.argv) > 1 else 'MMD.COM').upper()
rows = []
for f in sorted(os.listdir(PDIR)):
    if not f.lower().endswith('.zip'):
        continue
    try:
        z = zipfile.ZipFile(os.path.join(PDIR, f))
    except Exception:
        continue
    for n in z.namelist():
        if n.upper() == target:
            d = z.read(n)
            rows.append((f[:-4], len(d), hashlib.sha256(d).hexdigest()[:16],
                         d[:8].hex(' ')))

print('包内 %s 的样本：%d 个\n' % (target, len(rows)))
print('%-14s %7s  %-18s %s' % ('包', '大小', 'sha256前16', '前8字节'))
print('-' * 72)
sizes = {}
for arch, size, h, head in rows:
    print('%-14s %7d  %-18s %s' % (arch, size, h, head))
    sizes.setdefault(size, []).append((arch, h))

print()
print('不同大小：%d 种 → %s' % (len(sizes), sorted(sizes)))
if len(rows) > 1:
    uniq = set(h for _, _, h, _ in rows)
    print('不同内容：%d 种' % len(uniq))
