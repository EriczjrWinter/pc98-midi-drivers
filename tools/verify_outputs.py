# -*- coding: utf-8 -*-
"""校验所有已交付的 MIDI：数量、可读性、总时长。"""
import glob
import os

import mido

FOLDERS = [
    ('雀鬼 (MS.COM)', r'D:\music\90S Galgame music\DR2ナイト雀鬼'),
    ('Filsnown (MS.COM)', r'D:\music\90S Galgame music\Filsnown'),
    ('eime (MMD)', r"D:\music\90S Galgame music\Amy's Fantasies (1996)\PC98-MDI"),
    ('雫 (MMDR)', r'D:\music\90S Galgame music\雫'),
    ('痕 (MMDR)', r'D:\music\90S Galgame music\痕\Kizuato_GS_MIDI'),
    ('二律背反 (AMUS)', r'D:\music\90S Galgame music\二律背反\AMUS_MIDI'),
    ('壳中的小鸟 (MSDRV4)', r'D:\music\90S Galgame music\壳中的小鸟\PC98-MIDI'),
]

total_files = 0
for name, path in FOLDERS:
    if not os.path.isdir(path):
        print('%-24s 目录不存在' % name)
        continue
    files = glob.glob(os.path.join(path, '*.mid'))
    if not files:
        print('%-24s 没有 .mid' % name)
        continue
    bad, total = [], 0.0
    for f in files:
        try:
            total += mido.MidiFile(f).length
        except Exception:
            bad.append(os.path.basename(f))
    total_files += len(files)
    print('%-24s %3d 首  可读 %3d  损坏 %d  %5.1f 分钟'
          % (name, len(files), len(files) - len(bad), len(bad), total / 60))
    for b in bad:
        print('     ✗', b)

print('\n合计 %d 首' % total_files)
