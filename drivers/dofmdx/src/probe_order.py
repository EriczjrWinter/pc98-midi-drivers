# -*- coding: utf-8 -*-
"""试不同的初始化顺序 + 周期推进函数组合。"""
import itertools
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


def run(tick, order):
    m = E.MDRV()
    boot(m)
    api(m, ah=0)
    m.uc.mem_write(E.lin(DSEG, 0), data)
    m.midi.clear()
    for ah in order:
        if ah == 1:
            api(m, ah=1, bx=DSEG, dx=4)
        else:
            api(m, ah=ah)
    for i in range(500):
        m.tick += 1
        api(m, ah=tick)
    return len(m.midi), m


best = []
for order in ([2, 1, 3], [1, 2, 3], [2, 1], [1, 3]):
    for tick in (6, 8, 9, 10, 11):
        n, m = run(tick, order)
        if n:
            best.append((n, order, tick))
        print('顺序 %-12s 推进 AH=%2d → %4d 字节' % (order, tick, n))

if best:
    best.sort(reverse=True)
    print('\n有输出的组合:', best[:5])
