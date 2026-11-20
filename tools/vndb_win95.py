# -*- coding: utf-8 -*-
"""查 VNDB，判断 PC-98 MIDI 作品有没有 Windows 移植版。

VNDB API 限制约 200 次 / 5 分钟，所以带节流和断点续跑。
结果缓存在 build/vndb_cache.json，重跑不会重复请求。
"""
import json
import os
import re
import time
import ssl
import urllib.request

CAT = r'D:\gf\pc98-midi-drivers\catalog\games.json'
CACHE = r'D:\gf\pc98-midi-drivers\build\vndb_cache.json'
OUT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
API = 'https://api.vndb.org/kana/vn'
DELAY = 1.7


def load_cache():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    return {}


def save_cache(c):
    json.dump(c, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def query(title):
    body = json.dumps({
        'filters': ['search', '=', title],
        'fields': 'title,alttitle,platforms,released,developers.name',
        'results': 5,
    }).encode('utf-8')
    req = urllib.request.Request(API, data=body,
                                 headers={'Content-Type': 'application/json',
                                          'User-Agent': 'pc98-midi-catalog/1.0'})
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read())['results']


def main():
    rows = json.load(open(CAT, encoding='utf-8'))
    targets = [r for r in rows if r['pc98_midi']]
    print('PC-98 有 MIDI 的作品:', len(targets))

    cache = load_cache()
    todo = [r for r in targets if r['title'] not in cache]
    print('待查:', len(todo), ' 已缓存:', len(cache))

    for i, r in enumerate(todo, 1):
        try:
            cache[r['title']] = query(r['title'])
        except Exception as e:
            print('  ! %-30s %s' % (r['title'][:28], e))
            cache[r['title']] = {'error': str(e)}
        if i % 20 == 0:
            save_cache(cache)
            print('  已查 %d/%d' % (i, len(todo)))
        time.sleep(DELAY)
    save_cache(cache)

    # 汇总
    out = []
    for r in targets:
        res = cache.get(r['title'])
        if not isinstance(res, list) or not res:
            r['vndb'] = None
            out.append(r)
            continue
        # 优先选标题最接近的
        best = res[0]
        for cand in res:
            if cand['title'].lower() == r['title'].lower():
                best = cand
                break
        r['vndb'] = {'id': best['id'], 'title': best['title'],
                     'platforms': best.get('platforms') or [],
                     'released': best.get('released'),
                     'developers': [d['name'] for d in
                                    (best.get('developers') or [])]}
        out.append(r)

    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    win = [r for r in out if r.get('vndb') and 'win' in r['vndb']['platforms']]
    print('\n查到 VNDB 的:', sum(1 for r in out if r.get('vndb')))
    print('其中有 Windows 版:', len(win))
    print('写入', OUT)
    print('\n样例:')
    for r in win[:12]:
        print('   %-32s %s' % (r['title'][:30], ','.join(r['vndb']['platforms'])))


if __name__ == '__main__':
    main()
