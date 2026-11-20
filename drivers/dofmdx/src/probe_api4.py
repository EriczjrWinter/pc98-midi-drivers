# -*- coding: utf-8 -*-
"""以中断方式调用 API（入口以 iret 结尾，必须压 FLAGS+CS+IP）。"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdrv_emu as E

DSEG = 0x4000
API_OFF = 0xCE
data = zipfile.ZipFile(r'D:\GamedataUnpack\hoot20251231\pc98\cl_98.zip').read('CR001G.FMD')


def api(m, ah=0, al=0, bx=0, dx=0):
    u = m.uc
    # iret 需要 FLAGS / CS / IP 三个
    m._push(u, 0x0202)
    m._push(u, E.SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, E.SEG)
    u.reg_write(E.UC_X86_REG_IP, API_OFF)
    u.reg_write(E.UC_X86_REG_AX, (ah << 8) | al)
    u.reg_write(E.UC_X86_REG_BX, bx)
    u.reg_write(E.UC_X86_REG_DX, dx)
    u.reg_write(E.UC_X86_REG_DS, E.SEG)
    u.reg_write(E.UC_X86_REG_ES, E.SEG)
    m._run()


def w(m, off):
    return int.from_bytes(m.uc.mem_read(E.lin(E.SEG, off), 2), 'little')


m = E.MDRV()
m.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DOFMD_98.BIN'),
       os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MDRV98'))
m.install()
m.uc.mem_write(E.lin(DSEG, 0), data)

api(m, ah=0)                       # 硬件检测
print('AH=0 后 [0x181]=%04X' % w(m, 0x181))
api(m, ah=1, bx=DSEG, dx=0)        # 打开曲子
print('AH=1 后 [0x120A]=%04X [0x1210]=%04X [0x1216]=%04X [0x121A]=%04X'
      % (w(m, 0x120A), w(m, 0x1210), w(m, 0x1216), w(m, 0x121A)))

m.midi.clear()
api(m, ah=2, bx=DSEG)              # 播放？
print('AH=2 后 MIDI=%d' % len(m.midi))
for i in range(800):
    m.tick += 1
    v = m.vectors.get(E.IVT_API)
    if not v:
        break
    ip, cs = v
    u = m.uc
    m._push(u, 0x0202)
    m._push(u, E.STUB_SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, cs)
    u.reg_write(E.UC_X86_REG_IP, ip)
    m._run()
print('过 800 次中断 MIDI=%d  前 16: %s'
      % (len(m.midi), ' '.join('%02X' % b for _, b in m.midi[:16])))
