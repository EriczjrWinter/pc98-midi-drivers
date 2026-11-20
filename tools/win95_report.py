# -*- coding: utf-8 -*-
"""生成 catalog/WIN95.md：有 Windows 移植版 / 有现成 MIDI 的作品清单。"""
import json

CAT = r'D:\gf\pc98-midi-drivers\catalog\win95.json'
MANUAL = r'D:\gf\pc98-midi-drivers\catalog\manual_sources.json'
OUT = r'D:\gf\pc98-midi-drivers\catalog\WIN95.md'

rows = json.load(open(CAT, encoding='utf-8'))
man = json.load(open(MANUAL, encoding='utf-8'))['sources']

conf = [r for r in rows if (r.get('conf') or 0) >= 0.85 and r.get('vndb')]
maybe = [r for r in rows if 0.5 <= (r.get('conf') or 0) < 0.85 and r.get('vndb')]
low = [r for r in rows if r.get('vndb') and (r.get('conf') or 0) < 0.5]
nomat = [r for r in rows if not r.get('vndb')]

A = [r for r in rows if r.get('status') == 'A']
C = [r for r in rows if r.get('status') == 'C']
B = [r for r in rows if r.get('status') == 'B']
D = [r for r in rows if r.get('status') == 'D']

L = []
L.append('# 有 Windows 移植版 / 有现成 MIDI 的作品')
L.append('')
L.append('来源：HOOT（PC-98 侧，414 部有 MIDI）+ VNDB（平台信息）+ 本地收藏（人工确认）。')
L.append('')
L.append('## 分类')
L.append('')
L.append('| 类 | 含义 | 数量 |')
L.append('|---|---|---|')
L.append('| **A** | PC-98 有 MIDI，别处没有 → **必须逆向驱动** | %d |' % len(A))
L.append('| **B** | PC-98 无 MIDI，别处有 → 直接用 | %d |' % len(B))
L.append('| **C** | 两边都有 → **用现成的** | %d |' % len(C))
L.append('| **D** | 都没有 → 跳过 | %d |' % len(D))
L.append('')
L.append('> 现成 MIDI 的成本是零，逆向驱动的成本是几小时。所以 C 类不用碰驱动。')
L.append('')
L.append('## 免责声明')
L.append('')
L.append('本清单里的「本地已有 MIDI」来自**上传者个人收藏**的扫描结果，')
L.append('只用来判断「这个作品是不是已经有现成 MIDI」，**不代表这些文件可用**。')
L.append('')
L.append('- 部分文件是从 PS1 / SS / SFC 等平台的类 MIDI 序列转换而来，')
L.append('  年代未必与 PC-98 对应，转换质量参差，**仅供参考**')
L.append('- 部分文件的确切来源已不可考')
L.append('- **这些文件不在本仓库中**，仓库只记录「存在性」')
L.append('')
L.append('需要可靠音源时，应以 PC-98 驱动提取的结果或官方发布物为准。')
L.append('')

if C:
    L.append('## C 类：已确认有现成 MIDI（%d 部）\n' % len(C))
    L.append('| 作品 | 会社 | 平台 | MIDI | 本地目录 |')
    L.append('|---|---|---|---|---|')
    for r in sorted(C, key=lambda x: -x.get('local_midi', 0)):
        L.append('| %s | %s | %s | %d | %s |'
                 % (r['title'][:34], r['company'],
                    r.get('platform_note', 'Win95'),
                    r.get('local_midi', 0),
                    (r.get('source') or '')[:36]))
    L.append('')

L.append('## VNDB 查到的 Windows 版')
L.append('')
L.append('| 分类 | 数量 |')
L.append('|---|---|')
L.append('| 高置信（≥0.85） | %d |' % len(conf))
L.append('| 可能（0.5–0.85） | %d |' % len(maybe))
L.append('| 低置信（<0.5，多半错配） | %d |' % len(low))
L.append('| VNDB 查不到 | %d |' % len(nomat))
L.append('')

for title, group in (('高置信', conf), ('可能', maybe), ('低置信（建议人工核对）', low)):
    if not group:
        continue
    L.append('### %s —— %d 部\n' % (title, len(group)))
    L.append('| 作品 | 会社 | 年份 | 平台 | 置信 | PC-98 驱动 |')
    L.append('|---|---|---|---|---|---|')
    for r in sorted(group, key=lambda x: (x['company'], x['title'])):
        L.append('| %s | %s | %s | %s | %.2f | %s |'
                 % (r['title'][:34], r['company'],
                    (r['vndb'].get('released') or '')[:4],
                    ' '.join(r['vndb']['platforms']),
                    r.get('conf') or 0,
                    ','.join(r['drivers'])[:24] or '—'))
    L.append('')

L.append('## 人工维护的来源')
L.append('')
L.append('自动扫描扫不出来的，记在 `catalog/manual_sources.json`。')
L.append('')
L.append('| 作品 | 平台 | MIDI | 目录 |')
L.append('|---|---|---|---|')
for m in man:
    L.append('| %s | %s | %d | %s |'
             % (m['title'][:32], m.get('platform', ''), m.get('midi', 0),
                m.get('folder', '')[:36]))
L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('A=%d B=%d C=%d D=%d' % (len(A), len(B), len(C), len(D)))
print('高置信 %d / 可能 %d / 低置信 %d / 查不到 %d'
      % (len(conf), len(maybe), len(low), len(nomat)))
print('写入', OUT)
