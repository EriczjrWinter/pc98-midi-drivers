# -*- coding: utf-8 -*-
"""按用户的听感 + 专辑曲目表，给雫的 25 首定名。

格式：NN 专辑曲名(游戏内场景)
"""
import os
import re

S = r'D:\music\90S Galgame music\雫'

# GS 编号 -> 最终名字（不含编号）
# 曲名优先用「雫 ORIGINAL SOUND TRACK」的日文标题；
# 专辑里本来就是英文（或没有对应曲）的保留英文。
NAMES = {
    0:  'Leaf(ブランドロゴ)',
    1:  '退屈(精神世界)',
    2:  'Invitation to insanity(授業中)',
    3:  '狭間(学園生活)',
    4:  'Smoking Walk -Theme of NAGASE-(叔父さん)',
    5:  '翳り(推理・憶測)',
    6:  'トモダチ -Theme of MIZUHO-(瑞穂)',
    7:  'sunny-side-up -Theme of SAORI-(沙織)',
    8:  '世界が変わるとき -Theme of RURIKO-(瑠璃子)',
    9:  '不穏(調査)',
    10: '邂逅(回想)',
    11: '霧の向こう(捜索)',
    12: '全てが消え果ても(Hシーン1)',
    13: 'BLUE HEAVEN(Hシーン2)',
    14: 'Leaf(ブランドロゴ)',
    15: '雫-しずく-(オープニング)',
    16: 'MOON PHASE(トゥルーエンド)',
    17: 'Step under the moonlight(ハッピーエンド)',
    18: '月蝕(バッドエンド)',
    19: '対峙(敵)',
    20: 'HEAT WAVE(バトル)',
    21: '狂気(狂気)',
    22: 'music box(オルゴール1)',
    23: 'music box (ending)(オルゴール2)',
    24: 'School Bell(チャイム)',
}


def safe(name):
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, '_')
    return name


n = 0
for f in sorted(os.listdir(S)):
    if not f.lower().endswith('.mid'):
        continue
    m = re.match(r'^(\d\d)\s', f)
    if not m:
        continue
    num = int(m.group(1))
    if num not in NAMES:
        continue
    dst = '%02d %s.mid' % (num, safe(NAMES[num]))
    if f == dst:
        continue
    os.replace(os.path.join(S, f), os.path.join(S, dst))
    n += 1

print('重命名 %d 个' % n)
for f in sorted(os.listdir(S)):
    if f.lower().endswith('.mid') and re.match(r'^\d\d\s', f):
        print('   ', f)
