# -*- coding: utf-8 -*-
"""探 MS.COM 的 INT 7Fh 功能号：试 AX=0..8，看哪个让驱动发 MIDI。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mscom_emu as E

HERE = os.path.dirname(os.path.abspath(__file__))
DRV = os.path.join(HERE, 'ms.com')
MUS = os.path.join(HERE, 'FR_GS00.MD')

data = open(MUS, 'rb').read()
print('数据 %d 字节  头: %s' % (len(data), data[:12].hex(' ')))

for ax in range(0, 9):
    m = E.MSCom(verbose=False, driver=DRV)
    m.load_driver()
    if not m.install():
        print('AX=%d 安装失败' % ax)
        continue
    m.load_music(data)
    m.midi.clear()
    m.call_api(ax=ax, dx=E.DATA_SEG)
    for _ in range(300):
        m.tick += 1
        if not m.fire_timer():
            break
    n = len(m.midi)
    head = ''.join('%02X ' % b for _, b in m.midi[:12])
    print('AX=%d  → MIDI %4d 字节  %s' % (ax, n, head))
