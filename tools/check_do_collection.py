# -*- coding: utf-8 -*-
"""检查 D.O. 系 26 部 MIDI 作品中，用户收藏里已有现成 MIDI 的有几部。"""
import os
import re

MUS = r'D:\music\90S Galgame music'
X = r'D:\GamedataUnpack\hoot20251231\xml'

# 收集 do/foster/zyx 里「有真 MIDI 变体」的作品名
MIDI_LIKE = ('MT-32', 'GS', 'GM', 'SC-88', 'CM-64')
works = []
for company in ('do', 'foster', 'zyx'):
    t = open(os.path.join(X, company + '.xml'), encoding='utf-8',
             errors='replace').read()
    seen = {}
    for b in re.split(r'<game>', t):
        nm = re.search(r'<name>([^<]+)</name>', b)
        if not nm:
            continue
        title = nm.group(1)
        base = re.sub(r'^\[[^\]]*\]\s*', '', title)
        base = re.sub(r'\([^)]*\)\s*$', '', base).strip()
        m = re.search(r'\(([^)]+)\)\s*$', title)
        var = m.group(1) if m else ''
        midi = bool(re.search(r'name="midiout"\s+value="1"', b))
        if midi and any(k.upper() in var.upper() for k in MIDI_LIKE):
            seen.setdefault(base, set()).add(company)
    for k in seen:
        works.append(k)

works = sorted(set(works))
print('有真 MIDI 变体的作品:', len(works))

# 收藏目录
folders = [d for d in os.listdir(MUS) if os.path.isdir(os.path.join(MUS, d))]


def norm(s):
    s = s.lower()
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = re.sub(r'\([^)]*\)', '', s)
    return re.sub(r'[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]', '', s)


have, no = [], []
for w in works:
    nw = norm(w)
    hit = None
    for f in folders:
        nf = norm(f)
        if not nw or not nf:
            continue
        # 取较长的一方做包含判断
        if nw[:6] and nw[:6] in nf or (len(nf) >= 4 and nf[:6] in nw):
            hit = f
            break
    if hit:
        have.append((w, hit))
    else:
        no.append(w)

print('\n收藏里疑似已有 MIDI 的: %d 部' % len(have))
for w, f in have:
    print('   %-34s ← %s' % (w[:32], f[:34]))
print('\n没有的: %d 部' % len(no))
for w in no:
    print('   ', w[:40])
