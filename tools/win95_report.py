# -*- coding: utf-8 -*-
"""生成「有 Windows 移植版 + PC-98 有 MIDI」的清单（带置信度）。"""
import csv
import json
import os
import re
import unicodedata

CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
MUSIC = r'D:\music\90S Galgame music'
OUT_MD = r'D:\gf\pc98-midi-drivers\catalog\WIN95.md'
OUT_CSV = r'D:\gf\pc98-midi-drivers\catalog\win95.csv'


def norm(s):
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]', '', s)
    return s


def scan_music():
    out = {}
    if os.path.isdir(MUSIC):
        for d in os.listdir(MUSIC):
            p = os.path.join(MUSIC, d)
            if not os.path.isdir(p):
                continue
            n = 0
            for root, _, files in os.walk(p):
                n += sum(1 for f in files if f.lower().endswith('.mid'))
            out[norm(d)] = (d, n)
    return out


rows = json.load(open(CAT, encoding='utf-8'))
cache = json.load(open(r'D:\gf\pc98-midi-drivers\build\vndb_cache.json',
                       encoding='utf-8'))
music = scan_music()

win = [r for r in rows if r.get('vndb') and 'win' in r['vndb']['platforms']]

for r in win:
    cands = [r['title']]
    for c in (cache.get(r['title']) or []):
        if c.get('id') == r['vndb']['id']:
            cands.append(c.get('alttitle') or '')
    hit = None
    for t in cands:
        if t and norm(t) in music:
            hit = music[norm(t)]
            break
    r['local_dir'] = hit[0] if hit else ''
    r['local_midi'] = hit[1] if hit else 0

conf = [r for r in win if (r.get('conf') or 0) >= 0.85]
maybe = [r for r in win if 0.5 <= (r.get('conf') or 0) < 0.85]
low = [r for r in win if (r.get('conf') or 0) < 0.5]
with_midi = [r for r in win if r['local_midi'] > 0]

with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['作品', '会社', '年份', '平台', '置信度', 'VNDB',
                'PC98驱动', '本地目录', '本地MIDI数'])
    for r in sorted(win, key=lambda x: -(x.get('conf') or 0)):
        w.writerow([r['title'], r['company'],
                    (r['vndb'].get('released') or '')[:4],
                    ' '.join(r['vndb']['platforms']),
                    r.get('conf'), r['vndb']['id'],
                    ','.join(r['drivers']), r['local_dir'], r['local_midi']])

L = ['# 有 Windows 移植版的 PC-98 MIDI 作品', '']
L.append('来源：HOOT（PC-98 侧，414 部有 MIDI）+ VNDB（平台信息）。')
L.append('')
L.append('**置信度**是 HOOT 标题与 VNDB 标题/日文名的相似度：')
L.append('- `>=0.85` 基本确定')
L.append('- `0.5–0.85` 可能对（常见于日文 vs 罗马字）')
L.append('- `<0.5` 多半是 VNDB 搜索抓错了')
L.append('')
L.append('| 分类 | 数量 |')
L.append('|---|---|')
L.append('| 有 Windows 版（VNDB 匹配到） | %d |' % len(win))
L.append('| 其中高置信 | %d |' % len(conf))
L.append('| 可能 | %d |' % len(maybe))
L.append('| 低置信（疑似错配） | %d |' % len(low))
L.append('| 本地确认有 MIDI | %d |' % len(with_midi))
L.append('')

for title, group in (('高置信（基本确定有 Win 版）', conf),
                     ('可能（0.5–0.85）', maybe),
                     ('低置信（建议人工核对）', low)):
    L.append('## %s —— %d 部\n' % (title, len(group)))
    L.append('| 作品 | 会社 | 年份 | 平台 | 置信 | PC-98 驱动 | 本地 MIDI |')
    L.append('|---|---|---|---|---|---|---|')
    for r in sorted(group, key=lambda x: (x['company'], x['title'])):
        L.append('| %s | %s | %s | %s | %.2f | %s | %s |'
                 % (r['title'][:38], r['company'],
                    (r['vndb'].get('released') or '')[:4],
                    ' '.join(r['vndb']['platforms']),
                    r.get('conf') or 0,
                    ','.join(r['drivers'])[:26] or '—',
                    ('✅ %d' % r['local_midi']) if r['local_midi'] else '—'))
    L.append('')

if with_midi:
    L.append('## 本地已确认有 MIDI 的\n')
    L.append('| 作品 | 会社 | 本地目录 | MIDI 数 |')
    L.append('|---|---|---|---|')
    for r in sorted(with_midi, key=lambda x: -x['local_midi']):
        L.append('| %s | %s | %s | %d |'
                 % (r['title'][:38], r['company'],
                    r['local_dir'][:32], r['local_midi']))
    L.append('')

open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(L))
print('高置信 %d / 可能 %d / 低置信 %d / 本地有MIDI %d'
      % (len(conf), len(maybe), len(low), len(with_midi)))
print('写入', OUT_MD)
