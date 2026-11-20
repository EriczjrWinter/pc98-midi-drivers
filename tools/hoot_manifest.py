# -*- coding: utf-8 -*-
"""生成「本地缺哪些 MIDI 作品」的清单。

数据来源：
  HOOT 的目录索引（hoot.joshw.info/pc98/）→ 文件名 + 大小
  本地 xml/*.xml                       → 每个作品的 archive 名与 midiout 标志
"""
import json
import os
import re

INDEX = r'D:\gf\pc98-midi-drivers\build\hoot_index.html'
XMLDIR = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\gf\pc98-midi-drivers\build\missing_midi.json'

UNIT = {'K': 1024, 'M': 1024 * 1024, 'G': 1024 ** 3, 'B': 1}


def parse_size(s):
    s = s.strip().replace(',', '')
    m = re.match(r'([\d.]+)\s*([KMG]?)', s, re.I)
    if not m:
        return 0
    return int(float(m.group(1)) * UNIT.get(m.group(2).upper() or 'B', 1))


def parse_index():
    """返回 {文件名: 字节数}"""
    t = open(INDEX, encoding='utf-8', errors='replace').read()
    out = {}
    # 形如： <a href="xxx.zip">xxx.zip</a>  2020-01-01 12:00   12K
    for m in re.finditer(
            r'href="([^"]+\.zip)"[^>]*>[^<]*</a>\s*[\d-]+\s+[\d:]+\s+([\d.]+[KMG]?)',
            t, re.I):
        out[m.group(1)] = parse_size(m.group(2))
    return out


def parse_xmls():
    """返回 [(会社, 作品名, archive, 是否 MIDI)]"""
    rows = []
    for fn in sorted(os.listdir(XMLDIR)):
        if not fn.endswith('.xml'):
            continue
        company = fn[:-4]
        t = open(os.path.join(XMLDIR, fn), encoding='utf-8', errors='replace').read()
        for b in re.split(r'<game>', t):
            a = re.search(r'archive="([^"]+)"', b)
            nm = re.search(r'<name>([^<]+)</name>', b)
            if not a or not nm:
                continue
            midi = bool(re.search(r'name="midiout"\s+value="1"', b))
            rows.append((company, nm.group(1), a.group(1), midi))
    return rows


def main():
    idx = parse_index()
    print('索引里的包:', len(idx))

    local = {f[:-4] for f in os.listdir(PC98) if f.lower().endswith('.zip')}
    print('本地已有包:', len(local))

    rows = parse_xmls()
    midi = [r for r in rows if r[3]]
    print('MIDI 作品（XML 标注 midiout=1）:', len(midi))

    missing, unknown, have = [], 0, 0
    for company, name, arch, _ in midi:
        if arch in local:
            have += 1
            continue
        if arch + '.zip' in idx:
            missing.append({'archive': arch, 'name': name, 'company': company,
                            'size': idx[arch + '.zip']})
        else:
            unknown += 1

    missing.sort(key=lambda x: (x['company'], x['archive']))
    total = sum(x['size'] for x in missing)
    print('本地已有 MIDI 包:', have)
    print('本地缺、索引里有:', len(missing), '  合计 %.1f MB' % (total / 1024 / 1024))
    print('本地缺、索引里也没有:', unknown)

    json.dump(missing, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('清单已写入', OUT)

    print('\n按会社分布（前 15）:')
    from collections import Counter
    c = Counter(x['company'] for x in missing)
    for k, v in c.most_common(15):
        print('   %-18s %d' % (k, v))


if __name__ == '__main__':
    main()
