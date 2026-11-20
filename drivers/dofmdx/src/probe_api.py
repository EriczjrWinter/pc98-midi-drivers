# -*- coding: utf-8 -*-
"""探 MDRV98 的 API：入口在 CS:0xCE，AH = 功能号（cmp ah,0Ch）。"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdrv_emu as E

HERE = os.path.dirname(os.path.abspath(__file__))
H = r'D:\GamedataUnpack\hoot20251231\pc98'
import zipfile

z = zipfile.ZipFile(os.path.join(H, 'cl_98.zip'))
data = z.read('CR001G.FMD')
print('FMD 数据 %d 字节  头 %s' % (len(data), data[:8]))

API_OFF = 0xCE          # MDRV98 在段内的起始偏移
DATA_OFF = 0x8000       # 我们放数据的偏移


def call(m, ax, dx=0, bx=0):
    u = m.uc
    m._push(u, E.SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, E.SEG)
    u.reg_write(E.UC_X86_REG_IP, API_OFF)
    u.reg_write(E.UC_X86_REG_AX, ax)
    u.reg_write(E.UC_X86_REG_DX, dx)
    u.reg_write(E.UC_X86_REG_BX, bx)
    u.reg_write(E.UC_X86_REG_DS, E.SEG)
    u.reg_write(E.UC_X86_REG_ES, E.SEG)
    m._run()


for ah in range(0, 13):
    m = E.MDRV()
    m.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    m.install()
    m.uc.mem_write(E.lin(E.SEG, DATA_OFF), data)
    m.midi.clear()
    m.io_log.clear()
    call(m, ax=ah << 8, dx=DATA_OFF)
    outs = [p for d, p, _ in m.io_log if d == 'out']
    print('AH=%2d → MIDI %3d 字节  out 端口 %s'
          % (ah, len(m.midi),
             sorted(set(hex(p) for p in outs))[:5]))
