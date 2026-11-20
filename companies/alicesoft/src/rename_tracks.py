# -*- coding: utf-8 -*-
"""用 ADISK.DAT 里 BGM 鉴赏菜单的曲名给导出的 MIDI 改名。

曲名位置：ADISK.DAT 约 0x30A5 起，按「每页 6 条」分块列出，条目以 24 24 分隔。
第 1 条「オープニング」与我们对上的第 1 首（OP）一致，可作为顺序锚点；
菜单共 20 条，而 AMUS.DAT 有 21 首，第 21 首没有出现在菜单里。
"""
from __future__ import annotations
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADISK = r'D:\Galgame\PC98-DOS-WIN95\GAME\AMBIVALENZ\ADISK.DAT'
OUT = os.path.join(HERE, 'out')

# 按菜单顺序（第 1 条已用 OP 验证）
NAMES = [
    'オープニング',
    '緊迫',
    '廃ビル',
    '美術館',
    '黄泉',
    '繭',
    '深層心理',
    '聖堂',
    'ネロ',
    '街',
    '女型戦闘',
    '男型戦闘',
    'ディアドラ',
    'エンディング',
    'シィア',
    '濡れ場',
    '花梨',
    'オルゴール',
    '悲哀',
    '家',
    '（未収録／名称不明）',
]


def dump_raw_names():
    d = open(ADISK, 'rb').read()
    seg = d[0x30A0:0x3230]
    parts = seg.split(b'\x24\x24')
    out = []
    for p in parts:
        best, cur, i = b'', b'', 0
        while i < len(p):
            b = p[i]
            if (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC):
                if i + 1 < len(p) and 0x40 <= p[i + 1] <= 0xFC and p[i + 1] != 0x7F:
                    cur += p[i:i + 2]
                    i += 2
                    continue
            if 0xA1 <= b <= 0xDF and cur:
                cur += p[i:i + 1]
                i += 1
                continue
            if len(cur) > len(best):
                best = cur
            cur = b''
            i += 1
        if len(cur) > len(best):
            best = cur
        try:
            t = best.decode('cp932')
        except Exception:
            continue
        if not t:
            continue
        if 'ペ' in t or t == '戻':
            continue
        out.append(t)
    return out


def main():
    raw = dump_raw_names()
    print('菜单里读到的条目：')
    for i, t in enumerate(raw, 1):
        print('  %2d %s' % (i, t))
    print()
    for i in range(1, 22):
        src = os.path.join(OUT, 'AMUS_%02d.mid' % i)
        if not os.path.exists(src):
            continue
        name = NAMES[i - 1]
        dst = os.path.join(OUT, '%02d %s.mid' % (i, name))
        shutil.copyfile(src, dst)
        print('%s -> %s' % (os.path.basename(src), os.path.basename(dst)))


if __name__ == '__main__':
    main()
