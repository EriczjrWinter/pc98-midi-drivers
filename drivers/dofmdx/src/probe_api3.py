# -*- coding: utf-8 -*-
"""功能 1 是「打开曲子」，参数：BX = 数据段，DX = 偏移。

之前把 BX 传成 0，导致 mov es,0 读到了中断向量表。
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdrv_emu as E

HERE = os.path.dirname(os.path.abspath(__file__))
H = r'D:\GamedataUnpack\hoot20251231\pc98'
API_OFF = 0xCE
DATA_SEG = 0x4000          # 数据放到独立的段
DATA_OFF = 0

data = zipfile.ZipFile(os.path.join(H, 'cl_98.zip')).read('CR001G.FMD')


def call(m, off, ax=0, dx=0, bx=0):
    u = m.uc
    m._push(u, E.SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, E.SEG)
    u.reg_write(E.UC_X86_REG_IP, off)
    u.reg_write(E.UC_X86_REG_AX, ax)
    u.reg_write(E.UC_X86_REG_DX, dx)
    u.reg_write(E.UC_X86_REG_BX, bx)
    u.reg_write(E.UC_X86_REG_DS, E.SEG)
    u.reg_write(E.UC_X86_REG_ES, DATA_SEG)
    m._run()


def fire_irq(m):
    v = m.vectors.get(E.IVT_API)
    if not v:
        return False
    ip, cs = v
    u = m.uc
    m._push(u, 0x0202)
    m._push(u, E.STUB_SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, cs)
    u.reg_write(E.UC_X86_REG_IP, ip)
    m._run()
    return True


for off in (0, 4):
    m = E.MDRV()
    m.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    m.install()
    m.uc.mem_write(E.lin(DATA_SEG, 0), data)
    m.midi.clear()
    # 先用功能 0 做硬件检测，再用功能 1 打开曲子
    call(m, API_OFF, ax=0x0000, dx=0, bx=DATA_SEG)
    call(m, API_OFF, ax=0x0100, dx=DATA_OFF + off, bx=DATA_SEG)
    for i in range(2000):
        m.tick += 1
        if not fire_irq(m):
            break
    print('data off=%d → MIDI %4d 字节  前 16: %s'
          % (off, len(m.midi), ' '.join('%02X' % b for _, b in m.midi[:16])))
