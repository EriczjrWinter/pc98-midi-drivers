# -*- coding: utf-8 -*-
"""给 VNDB 匹配结果打置信度，剔掉模糊搜索抓错的。"""
import difflib
import json
import re
import unicodedata

CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
OUT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'


def norm(s):
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]', '', s)
    return s


rows = json.load(open(CAT, encoding='utf-8'))
cache = json.load(open(r'D:\gf\pc98-midi-drivers\build\vndb_cache.json',
                       encoding='utf-8'))

good = doubt = 0
for r in rows:
    v = r.get('vndb')
    if not v:
        r['conf'] = None
        continue
    cands = [v['title']]
    for c in (cache.get(r['title']) or []):
        if c.get('id') == v['id']:
            cands.append(c.get('alttitle') or '')
    a = norm(r['title'])
    best = 0.0
    for t in cands:
        b = norm(t)
        if not a or not b:
            continue
        if a == b:
            best = 1.0
            break
        best = max(best, difflib.SequenceMatcher(None, a, b).ratio())
    r['conf'] = round(best, 2)
    if best >= 0.85:
        good += 1
    else:
        doubt += 1

json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('高置信（>=0.85）:', good)
print('低置信:', doubt)
print()
print('低置信样例:')
for r in rows:
    if r.get('conf') is not None and r['conf'] < 0.85 and r.get('vndb'):
        print('   %-28s 置信 %.2f  VNDB 标题 %s'
              % (r['title'][:26], r['conf'], r['vndb']['title'][:30]))
