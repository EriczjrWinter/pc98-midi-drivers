# -*- coding: utf-8 -*-
"""扫描 HOOT 的全部 XML，找出「带 MIDI 音源」的作品。

判据：
  1. <option name="midiout" value="1"/>  —— HOOT 会把驱动的 MIDI 输出送出去
  2. 数据里有 .MD / .MID / .SEQ 之类
  3. ROM 列表里有非 PMD 的驱动（PMD 是通用 FM 驱动，不算私有 MIDI）

XML 文件名即会社/分类。
"""
import os
import re
import sys

H = r'D:\GamedataUnpack\hoot20251231'
XDIR = os.path.join(H, 'xml')


def scan():
    rows = []
    for fn in sorted(os.listdir(XDIR)):
        if not fn.endswith('.xml'):
            continue
        company = fn[:-4]
        try:
            t = open(os.path.join(XDIR, fn), encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for b in re.split(r'<game>', t):
            nm = re.search(r'<name>([^<]+)</name>', b)
            if not nm:
                continue
            midiout = re.search(r'name="midiout"\s+value="1"', b) is not None
            roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
            drv = sorted(set(r.upper() for r in roms
                             if re.match(r'(?i).*(\.com|\.sys|\.drv|\.bin)$', r)))
            data = sorted(set(r for r in roms if re.search(r'(?i)\.(md|mid|seq|m2)$', r)))
            if midiout:
                rows.append((company, nm.group(1), drv, data))
    return rows


def main():
    rows = scan()
    print('带 midiout 的作品：%d 个\n' % len(rows))
    cur = None
    for company, name, drv, data in rows:
        if company != cur:
            print('【%s】' % company)
            cur = company
        d = ','.join(drv)[:34]
        print('   %-46s 驱动: %-34s 数据%d' % (name[:44], d or '-', len(data)))
    if '--drivers' in sys.argv:
        from collections import Counter
        c = Counter()
        for _, _, drv, _ in rows:
            for d in drv:
                c[d] += 1
        print('\n驱动出现频次：')
        for k, v in c.most_common(30):
            print('   %-24s %d' % (k, v))


if __name__ == '__main__':
    main()
