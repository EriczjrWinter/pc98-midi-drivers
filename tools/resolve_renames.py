# -*- coding: utf-8 -*-
"""把 XML 里的旧 archive 名映射到现在的 zip 名。

HOOT 改过名（gaogao3 → gao3_98、karanonaka_98 → karanon_98），
按编辑距离 + 前缀/后缀规则匹配，只接受高置信度的。
"""
import difflib
import json
import os
import re

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\gf\pc98-midi-drivers\build\rename_map.json'

zips = {f[:-4] for f in os.listdir(PC98) if f.lower().endswith('.zip')}
lower = {z.lower(): z for z in zips}


def norm(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    s = re.sub(r'(98|21|68)$', '', s)
    return s


def main():
    packs = {}
    for fn in sorted(os.listdir(X)):
        if not fn.endswith('.xml'):
            continue
        t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
        for b in re.split(r'<game>', t):
            a = re.search(r'archive="([^"]+)"', b)
            if not a:
                continue
            if not re.search(r'name="midiout"\s*value="1"', b):
                continue
            packs.setdefault(a.group(1), 0)
            packs[a.group(1)] += 1

    missing = [k for k in packs if k.lower() not in lower]
    print('XML 里的包:', len(packs), ' 对不上的:', len(missing))

    by_norm = {}
    for z in zips:
        by_norm.setdefault(norm(z), []).append(z)
    norm_keys = list(by_norm)

    mapping, unresolved = {}, []
    for old in missing:
        n = norm(old)
        cand = []
        if n in by_norm:
            cand = by_norm[n]
        else:
            close = difflib.get_close_matches(n, norm_keys, n=3, cutoff=0.82)
            for c in close:
                cand += by_norm[c]
        cand = [c for c in cand if c not in mapping.values()]
        if len(cand) == 1:
            mapping[old] = cand[0]
        else:
            unresolved.append((old, cand[:3]))

    print('自动解析:', len(mapping), ' 未解析:', len(unresolved))
    json.dump(mapping, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('映射写入', OUT)

    print('\n样例:')
    for old, new in list(mapping.items())[:10]:
        print('   %-20s → %s' % (old, new))
    if unresolved:
        print('\n未解析样例:')
        for old, c in unresolved[:8]:
            print('   %-20s 候选 %s' % (old, c))


if __name__ == '__main__':
    main()
