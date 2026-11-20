# -*- coding: utf-8 -*-
"""给所有 MIDI 作品分诊：每个作品用的驱动是什么形态。

分类依据是驱动文件本身：
  MZ       DOS EXE（有重定位，装载复杂）
  COM-跳转  开头是 e9 xx xx（COM 程序）
  COM-代码  其它小体积 .COM
  STUB     < 400 字节，多半是 HOOT 的装载桩
  BIN/DATA 其它（.BIN/.DRV/.SYS，可能是被装载的数据）

输出 build/triage.json，并按「驱动」聚合出统计。
"""
import collections
import json
import os
import re
import zipfile

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\gf\pc98-midi-drivers\build\triage.json'

CODE_EXT = ('.COM', '.EXE', '.DRV', '.SYS', '.BIN', '.X', '')


def classify(data, name):
    n = len(data)
    if name.upper().endswith('.EXE') or data[:2] == b'MZ':
        return 'MZ'
    if n < 400:
        return 'STUB'
    if data[:1] == b'\xe9':
        return 'COM-跳转'
    if name.upper().endswith('.COM'):
        return 'COM-代码'
    return 'BIN/DATA'


def main():
    packs = {}
    for fn in sorted(os.listdir(X)):
        if not fn.endswith('.xml'):
            continue
        company = fn[:-4]
        t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
        for b in re.split(r'<game>', t):
            a = re.search(r'archive="([^"]+)"', b)
            nm = re.search(r'<name>([^<]+)</name>', b)
            if not a or not nm:
                continue
            if not re.search(r'name="midiout"\s+value="1"', b):
                continue
            roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
            roms = [r for r in roms if re.match(r'.*\.(COM|SYS|DRV)$', r, re.I)]
            if not roms:
                continue
            key = a.group(1)
            ent = packs.setdefault(key, {'name': nm.group(1), 'company': company,
                                         'drivers': set()})
            for r in roms:
                ent['drivers'].add(r)

    print('MIDI 包:', len(packs))
    rows = []
    for key, ent in sorted(packs.items()):
        zp = os.path.join(PC98, key + '.zip')
        info = []
        if os.path.exists(zp):
            try:
                z = zipfile.ZipFile(zp)
                names = {n.upper(): n for n in z.namelist()}
                for d in sorted(ent['drivers']):
                    real = names.get(d.upper())
                    if not real:
                        info.append({'file': d, 'size': 0, 'kind': '缺失'})
                        continue
                    data = z.read(real)
                    info.append({'file': d, 'size': len(data),
                                 'kind': classify(data, d)})
            except Exception as e:
                info.append({'file': '?', 'size': 0, 'kind': '打不开'})
        rows.append({'archive': key, 'name': ent['name'], 'company': ent['company'],
                     'drivers': info})

    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('明细已写入', OUT)

    kinds = collections.Counter()
    for r in rows:
        for d in r['drivers']:
            kinds[d['kind']] += 1
    print('\n驱动形态分布:')
    for k, v in kinds.most_common():
        print('   %-10s %d' % (k, v))

    print('\n按驱动聚合（出现最多的 15 个主驱动）:')
    agg = collections.defaultdict(lambda: {'n': 0, 'kinds': collections.Counter(),
                                           'sizes': []})
    for r in rows:
        for d in r['drivers']:
            if d['kind'] == 'STUB':
                continue
            a = agg[d['file'].upper()]
            a['n'] += 1
            a['kinds'][d['kind']] += 1
            a['sizes'].append(d['size'])
    for k, v in sorted(agg.items(), key=lambda x: -x[1]['n'])[:15]:
        mid = sorted(v['sizes'])[len(v['sizes']) // 2]
        print('   %-16s %3d 部   中位大小 %6d   %s'
              % (k, v['n'], mid, dict(v['kinds'])))


if __name__ == '__main__':
    main()
