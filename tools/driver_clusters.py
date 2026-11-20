# -*- coding: utf-8 -*-
"""基于 triage2 的清单，按内容哈希聚类驱动。"""
import collections
import hashlib
import json
import os
import zipfile

PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
SRC = r'D:\gf\pc98-midi-drivers\build\triage2.json'
OUT = r'D:\gf\pc98-midi-drivers\build\driver_clusters.json'

rows = json.load(open(SRC, encoding='utf-8'))
print('包数', len(rows))

clusters = collections.defaultdict(lambda: {'games': set(), 'names': set(),
                                            'size': 0, 'kind': ''})
for r in rows:
    zp = os.path.join(PC98, r['archive'] + '.zip')
    if not os.path.exists(zp):
        continue
    exe = [f for f in r['files'] if f['kind'] in ('COM-跳转', 'COM-代码', 'MZ')]
    if not exe:
        continue
    try:
        z = zipfile.ZipFile(zp)
    except Exception:
        continue
    names = {n.upper(): n for n in z.namelist()}
    # 每包取体积最大的那个当"主驱动"，其余也一起算
    for f in exe:
        real = names.get(f['file'].upper())
        if not real:
            continue
        try:
            data = z.read(real)
        except Exception:
            continue
        h = hashlib.md5(data).hexdigest()[:12]
        c = clusters[h]
        c['games'].add((r['archive'], r['name'], r['company']))
        c['names'].add(f['file'].upper())
        c['size'] = len(data)
        c['kind'] = f['kind']

print('不同驱动:', len(clusters))
shared = [(h, c) for h, c in clusters.items() if len(c['games']) >= 2]
shared.sort(key=lambda x: -len(x[1]['games']))
print('被 2 个以上作品共用:', len(shared))
print()
print('%-14s %4s %8s %-9s %s' % ('hash', '作品', '大小', '形态', '文件名'))
print('-' * 74)
for h, c in shared[:28]:
    print('%-14s %4d %8d %-9s %s'
          % (h, len(c['games']), c['size'], c['kind'],
             ','.join(sorted(c['names']))[:32]))

json.dump({h: {'size': c['size'], 'kind': c['kind'],
               'names': sorted(c['names']),
               'games': sorted(c['games'])}
           for h, c in clusters.items()},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n明细:', OUT)
