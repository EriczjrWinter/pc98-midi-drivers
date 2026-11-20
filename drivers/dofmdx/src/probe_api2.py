# -*- coding: utf-8 -*-
"""MDRV98 是中断驱动的：调用 API 起播后，要靠 INT 7Fh 推进音乐。"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdrv_emu as E

HERE = os.path.dirname(os.path.abspath(__file__))
H = r'D:\GamedataUnpack\hoot20251231\pc98'
API_OFF = 0xCE
DATA_OFF = 0x8000

data = zipfile.ZipFile(os.path.join(H, 'cl_98.zip')).read('CR001G.FMD')


def call_code(m, off, ax=0, dx=0, bx=0, si=0, di=0):
    u = m.uc
    m._push(u, E.SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, E.SEG)
    u.reg_write(E.UC_X86_REG_IP, off)
    u.reg_write(E.UC_X86_REG_AX, ax)
    u.reg_write(E.UC_X86_REG_DX, dx)
    u.reg_write(E.UC_X86_REG_BX, bx)
    u.reg_write(E.UC_X86_REG_SI, si)
    u.reg_write(E.UC_X86_REG_DI, di)
    u.reg_write(E.UC_X86_REG_DS, E.SEG)
    u.reg_write(E.UC_X86_REG_ES, E.SEG)
    m._run()


def fire_irq(m):
    """触发 INT 7Fh（硬件中断）。"""
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


for ah in range(0, 13):
    m = E.MDRV()
    m.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    m.install()
    m.uc.mem_write(E.lin(E.SEG, DATA_OFF), data)
    m.midi.clear()
    call_code(m, API_OFF, ax=ah << 8, dx=DATA_OFF)
    for i in range(3000):
        m.tick += 1
        if not fire_irq(m):
            break
    print('AH=%2d → MIDI %4d 字节  前 12: %s'
          % (ah, len(m.midi),
             ' '.join('%02X' % b for _, b in m.midi[:12])))
