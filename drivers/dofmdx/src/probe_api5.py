# -*- coding: utf-8 -*-
"""MDRV98 单独装载在偏移 0（跳转表才在正确位置）。

流程：AH=0 硬件检测 → AH=1 打开曲子（BX=数据段, DX=偏移）→ AH=2 播放
      → 反复触发 INT 7Fh 推进音乐。
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdrv_emu as E

HERE = os.path.dirname(os.path.abspath(__file__))
DSEG = 0x4000
data = zipfile.ZipFile(r'D:\GamedataUnpack\hoot20251231\pc98\cl_98.zip').read('CR001G.FMD')


def boot(m):
    d = open(os.path.join(HERE, 'MDRV98'), 'rb').read()
    m.uc.mem_write(E.lin(E.SEG, 0), d)
    m.code_base = E.lin(E.SEG, 0)
    m.code_len = len(d)
    u = m.uc
    for r in (E.UC_X86_REG_CS, E.UC_X86_REG_DS, E.UC_X86_REG_ES,
              E.UC_X86_REG_SS):
        u.reg_write(r, E.SEG)
    u.reg_write(E.UC_X86_REG_SP, 0x4CE)
    # 预置 IVT 0x7F 指向 MDRV98 的 IRQ 处理（用 BIN 里的 0x39？先留空）
    m.hook_ints(m.code_base, m.code_len)


def api(m, ah=0, al=0, bx=0, dx=0):
    u = m.uc
    m._push(u, 0x0202)
    m._push(u, E.SEG)
    m._push(u, E.MAGIC_IP)
    u.reg_write(E.UC_X86_REG_CS, E.SEG)
    u.reg_write(E.UC_X86_REG_IP, 0)
    u.reg_write(E.UC_X86_REG_AX, (ah << 8) | al)
    u.reg_write(E.UC_X86_REG_BX, bx)
    u.reg_write(E.UC_X86_REG_DX, dx)
    u.reg_write(E.UC_X86_REG_DS, E.SEG)
    u.reg_write(E.UC_X86_REG_ES, E.SEG)
    m._run()


def fire(m, vec):
    v = m.vectors.get(vec)
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


def w(m, off):
    return int.from_bytes(m.uc.mem_read(E.lin(E.SEG, off), 2), 'little')


for ah in (1, 2):
    m = E.MDRV()
    boot(m)
    api(m, ah=0)                                  # 硬件检测
    m.uc.mem_write(E.lin(DSEG, 0), data)
    m.midi.clear()
    api(m, ah=1, bx=DSEG, dx=4)                   # 跳过 68V2 魔数
    print('AH=1 后 [0x120A]=%04X [0x1210]=%04X [0x1216]=%04X'
          % (w(m, 0x120A), w(m, 0x1210), w(m, 0x1216)))
    api(m, ah=2, bx=DSEG)                         # 播放？
    print('AH=2 后 MIDI=%d' % len(m.midi))
    for i in range(600):
        m.tick += 1
        fire(m, E.IVT_API)
    print('过 600 次中断 MIDI=%d  前 16: %s\n'
          % (len(m.midi), ' '.join('%02X' % b for _, b in m.midi[:16])))
    break
