# -*- coding: utf-8 -*-
"""给雀鬼和 Filsnown 的导出 MIDI 改名。

曲名来源：
  DR² Night Janki    「NIGHT JANKI ~ Team-Ios GAME Sound collection Vol.1」(LFCD-0001)
  Filsnown           「Filsnown ~ Team-Ios GAME Sound collection Vol.2」(LFCD-0002)
  两者在 VGMRips 的 pack 页面上有完整对照。
"""
import glob
import os
import re

BASE = r'D:\music\MSCOM_TEST'

JANKI = {
    'LEF_GSLG': '01 Brand Logo',
    'MRJ_GS01': '02 Trance Mind',
    'MRJ_GS02': '03 Maido Okini!!',
    'MRJ_GS03': '04 Spirit Rhythm',
    'MRJ_GS04': '05 Illusion',
    'MRJ_GS05': '06 Attack the Time',
    'MRJ_GS06': '07 Hard 2 Ghost',
    'MRJ_GS07': "08 Do' it Groovin",
    'MRJ_GS08': '09 Chinese Heaven',
    'MRJ_GS09': '10 Out Hall',
    'MRJ_GS10': '11 Now',
    'MRJ_GS11': '12 Fly Jacket',
    'MRJ_GS12': '13 Kick Out!!',
    'MRJ_GS13': '14 Piece for Memory',
    'MRJ_GSG1': '15 Game Over',
    'MRJ_GSG2': '16 Player Win!!',
    'MRJ_GSG3': '17 Player Lost',
    'MRJ_GSG4': '18 Appearance!!',
}

FILSNOWN = [
    '01 Brand Logo', '02 Opening 1', '03 Opening 2', '04 Main Field',
    '05 Castle 1', '06 Castle 2', '07 Town 1', '08 Town 2', '09 Village',
    '10 Normal Battle', '11 Mid-Boss Battle 1', '12 Mid-Boss Battle 2',
    '13 Mid-Boss Battle 3', '14 Temple 1', '15 Temple 2', '16 Forest, Ruins',
    '17 Cave', '18 Forest Spring', '19 Snow', '20 Pyramid', '21 Field 1',
    '22 Field 2', '23 Field 3', '24 Critical Moment', '25 Past World',
    '26 Event 1', '27 Event 2', '28 Event 3', '29 Event 4', '30 Event 5',
    '31 Bar', '32 Ted', '33 Ocean', '34 Airship Indy', '35 Evil Shadow',
    '36 Bad End', '37 Happy End', '38 Victory', '39 Requiem', '40 Inn',
    '41 Treasure Chest', '42 Level Up', "43 Ted's Flute",
]

BAD = '\\/:*?"<>|'


def safe(s):
    for c in BAD:
        s = s.replace(c, '_')
    return s


def rename_janki():
    n = 0
    for f in glob.glob(os.path.join(BASE, 'DR2ナイト雀鬼', '*.mid')):
        base = os.path.splitext(os.path.basename(f))[0]
        m = re.match(r'(?:dr2_)?(.+)$', base)
        key = m.group(1) if m else base
        title = JANKI.get(key)
        if not title:
            print('  未匹配:', base)
            continue
        dst = os.path.join(BASE, 'DR2ナイト雀鬼', safe(title) + '.mid')
        if os.path.abspath(f) != os.path.abspath(dst):
            os.replace(f, dst)
            n += 1
    return n


def rename_filsnown():
    n = 0
    for f in glob.glob(os.path.join(BASE, 'Filsnown', '*.mid')):
        base = os.path.splitext(os.path.basename(f))[0]
        m = re.search(r'FR_GS(\d\d)', base, re.I)
        if not m:
            print('  未匹配:', base)
            continue
        i = int(m.group(1))
        if i >= len(FILSNOWN):
            print('  越界:', base)
            continue
        dst = os.path.join(BASE, 'Filsnown', safe(FILSNOWN[i]) + '.mid')
        if os.path.abspath(f) != os.path.abspath(dst):
            os.replace(f, dst)
            n += 1
    return n


if __name__ == '__main__':
    print('雀鬼：改名', rename_janki(), '个')
    print('Filsnown：改名', rename_filsnown(), '个')
