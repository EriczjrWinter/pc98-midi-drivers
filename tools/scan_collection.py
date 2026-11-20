# -*- coding: utf-8 -*-
"""清点本地收藏：每个目录查 VNDB，拿到平台信息，并和 HOOT 目录对上。

用户的目录名多是从西方网站下的英文/罗马字名，正好对应 VNDB 的 title 字段。
"""
import json
import os
import ssl
import time
import urllib.request

MUSIC = r'D:\music\90S Galgame music'
CACHE = r'D:\gf\pc98-midi-drivers\build\collection_cache.json'
OUT = r'D:\gf\pc98-midi-drivers\catalog\collection.json'
API = 'https://api.vndb.org/kana/vn'
DELAY = 1.7
CTX = ssl._create_unverified_context()


def query(title):
    body = json.dumps({
        'filters': ['search', '=', title],
        'fields': 'title,alttitle,platforms,released,developers.name',
        'results': 5,
    }).encode('utf-8')
    req = urllib.request.Request(API, data=body,
                                 headers={'Content-Type': 'application/json',
                                          'User-Agent': 'pc98-midi-catalog/1.0'})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read())['results']


def scan():
    out = []
    for d in sorted(os.listdir(MUSIC)):
        p = os.path.join(MUSIC, d)
        if not os.path.isdir(p):
            continue
        midi = 0
        exts = {}
        for root, _, files in os.walk(p):
            for f in files:
                e = os.path.splitext(f)[1].lower()
                exts[e] = exts.get(e, 0) + 1
                if e in ('.mid', '.midi'):
                    midi += 1
        out.append({'dir': d, 'midi': midi, 'exts': exts})
    return out


def main():
    items = scan()
    print('收藏目录:', len(items))

    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding='utf-8'))

    # 用目录名去掉括号/年份再查
    def probe(d):
        import re
        t = re.sub(r'\[[^\]]*\]', ' ', d)
        t = re.sub(r'\([^)]*\)', ' ', t)
        t = re.sub(r'（[^）]*）', ' ', t)
        t = re.sub(r'^\s*[\d]{6,8}\s*', '', t)
        return t.strip()

    todo = [x for x in items if x['dir'] not in cache]
    print('待查:', len(todo))
    for i, x in enumerate(todo, 1):
        try:
            cache[x['dir']] = query(probe(x['dir']))
        except Exception as e:
            cache[x['dir']] = {'error': str(e)}
        if i % 20 == 0:
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
            print('  已查 %d/%d' % (i, len(todo)))
        time.sleep(DELAY)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    for x in items:
        res = cache.get(x['dir'])
        if isinstance(res, list) and res:
            b = res[0]
            x['vndb'] = {'id': b['id'], 'title': b.get('title'),
                         'alttitle': b.get('alttitle'),
                         'platforms': b.get('platforms') or [],
                         'released': b.get('released')}
        else:
            x['vndb'] = None

    json.dump(items, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ok = sum(1 for x in items if x['vndb'])
    print('\nVNDB 匹配到:', ok, '/', len(items))
    has = [x for x in items if x['midi'] > 0]
    print('含 MIDI 的目录:', len(has), ' 合计 %d 首'
          % sum(x['midi'] for x in has))
    print('写入', OUT)


if __name__ == '__main__':
    main()
