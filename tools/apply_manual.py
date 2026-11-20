# -*- coding: utf-8 -*-
"""把 manual_sources.json 合并进 catalog/win95.json，并重算 A/B/C/D。

人工来源的优先级高于 VNDB 推断——它们是实际确认过有 MIDI 的目录。
"""
import json
import os

CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
MANUAL = r'D:\gf\pc98-midi-drivers\catalog\manual_sources.json'


def main():
    rows = json.load(open(CAT, encoding='utf-8'))
    man = json.load(open(MANUAL, encoding='utf-8'))['sources']

    for r in rows:
        r.setdefault('win_midi', None)
        r.setdefault('other_midi', None)
        r.setdefault('source', None)
        r.setdefault('local_midi', 0)

    matched, unmatched = 0, []
    for m in man:
        hit = [r for r in rows if r['title'] == m['title']]
        if not hit:
            unmatched.append(m['title'])
            continue
        for r in hit:
            r['win_midi'] = True
            r['source'] = m['folder']
            r['local_midi'] = m['midi']
            r['platform_note'] = m['platform']
            r['note'] = m.get('note', '')
            matched += 1

    # 重算分类
    for r in rows:
        any_midi = bool(r.get('win_midi')) or bool(r.get('other_midi'))
        if r.get('pc98_midi') and not any_midi:
            r['status'] = 'A'
        elif any_midi and not r.get('pc98_midi'):
            r['status'] = 'B'
        elif any_midi and r.get('pc98_midi'):
            r['status'] = 'C'
        else:
            r['status'] = 'D'

    json.dump(rows, open(CAT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print('手工来源:', len(man), ' 匹配到条目:', matched)
    if unmatched:
        print('未匹配（标题对不上）:', unmatched)

    from collections import Counter
    c = Counter(r['status'] for r in rows)
    print('\n分类结果:')
    for k in 'ABCD':
        print('   %s 类: %d' % (k, c.get(k, 0)))
    print('\nC 类（两边都有，用现成的）:')
    for r in rows:
        if r['status'] == 'C':
            print('   %-32s %-10s %d 首  %s'
                  % (r['title'][:30], r['company'], r['local_midi'],
                     r['source'][:34]))


if __name__ == '__main__':
    main()
