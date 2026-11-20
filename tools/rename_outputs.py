# -*- coding: utf-8 -*-
"""按官方曲名重命名导出的 MIDI。

痕：HOOT 的 leaf.xml 给了完整的 26 首曲名。
雫：HOOT 给的是场景名；其中 5 首有官方曲名（来自实机录音的文件名），
    采用「曲名(场景)」的形式，与参考文件一致。

注意雫的 GS15 / GS18 与 HOOT 曲名表**正好对调**（已用录音验证）。
"""
import os
import sys

# ---- 痕 ----
KIZUATO = {
    0: 'リーフ', 1: '寝覚月', 2: 'ためいき', 3: '夏の追憶', 4: '千鶴',
    5: '梓', 6: '楓', 7: '初音', 8: '日のあたる場所', 9: '長瀬刑事',
    10: 'もう一人の自分', 11: '迷妄', 12: '見えない月', 13: '光の粒',
    14: '夜の風', 15: 'UKIUKI気分', 16: 'スト3', 17: '鬼の伝説',
    18: '見えざる敵', 19: '鬼神楽', 20: 'つつまれて', 21: '醒めない夢',
    22: 'やすらぎ', 23: 'それは…現実', 24: '終わりそして始まり',
    25: 'まだ癒えぬ痕',
}

# ---- 雫 ----
# 专辑名来自「雫 ORIGINAL SOUND TRACK」（リニューアル版附赠，24 曲）。
# 与场景的对应关系取自用户自己的 WAV 文件名，以及角色名一致的几首。
# 编号 -> (专辑曲名, 场景)
SHIZUKU_OFFICIAL = {
    2:  ('退屈', '授業中'),
    6:  ('トモダチ -Theme of MIZUHO-', '瑞穂'),
    7:  ('sunny-side up -Theme of SAORI-', '沙織'),
    8:  ('世界が変わるとき -Theme of RURIKO-', '瑠璃子'),
    13: ('BLUE HEAVEN', 'Hシーン2'),
    15: ('雫 -しずく -', 'オープニング'),      # 注意：GS15 实际是 OP
    16: ('MOON PHASE', 'トゥルーエンド'),
    18: ('月蝕', 'バッドエンド'),              # 注意：GS18 实际是 BAD END
    20: ('HEAT WAVE', 'バトル'),
    21: ('狂気', '狂気'),
    22: ('music box', 'オルゴール1'),
}
# 其余用 HOOT 的场景名
SHIZUKU_SCENE = {
    0: 'ブランドロゴ', 1: '精神世界', 3: '学園生活',
    4: '叔父さん', 5: '推理・憶測', 9: '調査', 10: '回想',
    11: '捜索', 12: 'Hシーン1', 14: 'ブランドロゴ',
    17: 'ハッピーエンド', 19: '敵',
    23: 'オルゴール2', 24: '（空）',
}


def safe(name):
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, '_')
    return name.strip()


def rename(folder, prefix, mapping, official=None):
    files = [f for f in os.listdir(folder)
             if f.upper().startswith(prefix.upper()) and f.lower().endswith('.mid')]
    n = 0
    for f in sorted(files):
        try:
            num = int(f[len(prefix):len(prefix) + 2])
        except ValueError:
            continue
        title = None
        if official and num in official:
            song, scene = official[num]
            title = '%02d %s(%s)' % (num, song, scene)
        elif num in mapping:
            title = '%02d %s' % (num, mapping[num])
        if not title:
            continue
        dst = os.path.join(folder, safe(title) + '.mid')
        if os.path.abspath(os.path.join(folder, f)) == os.path.abspath(dst):
            continue
        os.replace(os.path.join(folder, f), dst)
        n += 1
    return n


if __name__ == '__main__':
    k = r'D:\music\90S Galgame music\痕\Kizuato_GS_MIDI'
    s = r'D:\music\90S Galgame music\雫'
    nk = rename(k, 'KZ_GS', KIZUATO)
    ns = rename(s, 'SZ_GS', SHIZUKU_SCENE, SHIZUKU_OFFICIAL)
    print('痕：重命名 %d 个' % nk)
    print('雫：重命名 %d 个' % ns)
