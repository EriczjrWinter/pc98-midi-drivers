# -*- coding: utf-8 -*-
"""统计 MDRV98 家族的三条打包路线，并按签名扫描本地包。

用法：
    python tools/mdrv98_routes.py            # 只看 XML 统计
    python tools/mdrv98_routes.py --scan     # 再扫一遍本地 zip（较慢）

签名是 MDRV98 跳转表 + 功能 0 的开头（32 字节），在驱动文件里位于 0x29。
"""
import glob
import os
import re
import sys
import zipfile
from collections import defaultdict

SIG = bytes.fromhex(
    '41002b029701300439044204dd026b04'
    '9b042401a1048e01b98801e4608ae0ba')

HOOT = os.environ.get('HOOT_PC98', r'D:\GamedataUnpack\hoot20251231\pc98')
XML = os.environ.get('HOOT_XML', r'D:\GamedataUnpack\hoot20251231\xml')


def classify(xml_dir=XML):
    per = defaultdict(set)
    cnt = defaultdict(int)
    for f in glob.glob(os.path.join(xml_dir, '*.xml')):
        t = open(f, encoding='utf-8', errors='ignore').read()
        for g in re.findall(r'(?s)<game>.*?</game>', t):
            low = g.lower()
            roms = [r.strip() for r in re.findall(r'<rom[^>]*>(.*?)</rom>', g)]
            arch = (re.search(r'<romlist archive="(.*?)"', g) or [None, '?'])[1]
            route = None
            if any(r.upper() in ('MDRV98', 'ZYXMD') for r in roms) and \
               any('dofmd_98.bin' in r.lower() for r in roms):
                route = 'A standalone'
            elif 'dofmdx98.com' in low:
                route = 'B dofmdx98'
            elif 'mdrv98.com' in low:
                route = 'C mdrv98.com'
            if route:
                per[route].add(re.sub(r'_\d+$', '', arch))
                cnt[route] += 1
    return {r: (cnt[r], sorted(per[r])) for r in per}


def scan(root=HOOT):
    zips = sorted(f for f in os.listdir(root) if f.lower().endswith('.zip'))
    hits = []
    for i, zf in enumerate(zips):
        try:
            z = zipfile.ZipFile(os.path.join(root, zf))
        except Exception:
            continue
        for info in z.infolist():
            if not info.file_size or info.file_size > 4 * 1024 * 1024:
                continue
            try:
                data = z.read(info)
            except Exception:
                continue
            off = data.find(SIG)
            if off >= 0:
                hits.append((zf[:-4], info.filename, off, len(data)))
        z.close()
        if (i + 1) % 500 == 0:
            print('  scanned %d/%d' % (i + 1, len(zips)), flush=True)
    return hits


def main():
    print('=== XML 路线统计')
    for route, (entries, packs) in sorted(classify().items()):
        print('%-14s entries=%3d packages=%3d' % (route, entries, len(packs)))
        print('   ', ' '.join(packs))
    if '--scan' in sys.argv:
        print('=== 签名扫描（本地 %s）' % HOOT)
        for pack, name, off, size in scan():
            print('%-16s %-16s off=0x%05X size=%d' % (pack, name, off, size))


if __name__ == '__main__':
    main()
