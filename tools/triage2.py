# -*- coding: utf-8 -*-
"""给每个 MIDI 包找出「真正的驱动」并分类。

HOOT 的 rom 列表里常有一个几百字节的加载桩 (.COM) 加一个真正的大驱动
(.BIN / 无扩展名)。所以按大小和形态判断，而不是只看扩展名。
"""
import collections
import json
import os
import re
import zipfile

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\gf\pc98-midi-drivers\build\triage2.json'

DRV_EXT = ('.COM', '.EXE', '.DRV', '.SYS', '.BIN', '.X', '')


def kind_of(name, data):
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
            roms = re.findall(r'<rom type="[^"]*"[^>]*>([^<]+)</rom>', b)
            ent = packs.setdefault(a.group(1), {'name': nm.group(1),
                                                'company': company,
                                                'files': set()})
            for r in roms:
                ent['files'].add(r)

    rows = []
    for key, ent in sorted(packs.items()):
        zp = os.path.join(PC98, key + '.zip')
        if not os.path.exists(zp):
            continue
        try:
            z = zipfile.ZipFile(zp)
            names = {n.upper(): n for n in z.namelist()}
        except Exception:
            continue
        cands = []
        for f in ent['files']:
            real = names.get(f.upper())
            if not real:
                continue
            try:
                data = z.read(real)
            except Exception:
                continue
            k = kind_of(f, data)
            cands.append({'file': f, 'size': len(data), 'kind': k})
        rows.append({'archive': key, 'name': ent['name'],
                     'company': ent['company'], 'files': cands})

    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('写出', OUT, ' 包数', len(rows))

    # 每个包的驱动 = 非桩、体积最大的可执行类文件
    agg = collections.defaultdict(lambda: {'n': 0, 'sizes': [], 'kinds': collections.Counter()})
    nostub = 0
    for r in rows:
        exe = [f for f in r['files'] if f['kind'] != 'STUB'
               and os.path.splitext(f['file'])[1].lower() in DRV_EXT
               and f['size'] > 400]
        if not exe:
            nostub += 1
            continue
        d = max(exe, key=lambda x: x['size'])
        a = agg[d['file'].upper()]
        a['n'] += 1
        a['sizes'].append(d['size'])
        a['kinds'][d['kind']] += 1

    print('找不到非桩驱动的包:', nostub)
    print('\n真正的驱动（出现次数 top 20）:')
    for k, v in sorted(agg.items(), key=lambda x: -x[1]['n'])[:20]:
        mid = sorted(v['sizes'])[len(v['sizes']) // 2]
        print('   %-16s %3d 部   中位 %6d   %s' % (k, v['n'], mid, dict(v['kinds'])))


if __name__ == '__main__':
    main()
