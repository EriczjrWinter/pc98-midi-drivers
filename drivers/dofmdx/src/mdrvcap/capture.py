# -*- coding: utf-8 -*-
"""MDRV98 MIDI 变体抓包器（最小实现）。

只跑「MIDI 那条腿」：
    BIN 启动 → INT 7F AL=1（BIN 从 0x7D4/0x7D6 取指针、校验 68V2、调表 B 功能 1）
    → INT 7F AL=0（表 B 功能 2）→ 反复触发 INT 12h（Timer B）→ 抓 0xE0D0 的字节

表 A 的 FM 音乐推进完全不跑。
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from .model import Sim, lin, BIN_SEG, DRV_SEG, MAGIC_IP, MAGIC_SEG
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
                               UC_X86_REG_DX, UC_X86_REG_DS, UC_X86_REG_ES,
                               UC_X86_REG_DI, UC_X86_REG_SI, UC_X86_REG_CS,
                               UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_SS)

DATA_SEG = 0x4000
IVT_IRQ = 0x12


class CapSim(Sim):
    def __init__(self, verbose=False):
        super().__init__(verbose=verbose)
        self.data_off = 0
        self.data_seg = DATA_SEG
        self.tick = 0
        self.midi = []            # (tick, byte)
        self.reg_sel = 0
        self.regs = {}
        self.tb_enabled = False
        self.status = 0
        self.board_cmd = 0

    # ---------- 端口 ----------
    def _on_in(self, uc, port, size, user):
        port &= 0xFFFF
        if port == 0x7D4:
            return self.data_off
        if port == 0x7D6:
            return self.data_seg
        if port == 0x7E0:
            return self.board_cmd
        if port == 0x7E4:
            return 0
        if port == 0x188:
            return self.status      # 状态寄存器：读不清（由写 0x27 清除）
        if port == 0x18A:
            return self.last_out.get(0x18A, 0x00)
        if port == 0xE0D2:
            return 0x00          # 板子在、就绪、无数据
        if port == 0xE0D0:
            return 0xFE          # ACK
        return self.last_out.get(port, 0x00)

    def _on_out(self, uc, port, size, value, user):
        port &= 0xFFFF
        v = value & 0xFF
        self.last_out[port] = v
        self.out_log.append((port, v))
        if port == 0x188:
            self.reg_sel = v
        elif port == 0x18A:
            self._write_reg(self.reg_sel, v)
        elif port in (0xE0D0, 0xE0D2):
            self.midi.append((self.tick, v))

    def _write_reg(self, reg, v):
        self.regs[reg] = v
        if reg == 0x27:
            self.status = 0                  # 写 0x27 = 确认/复位定时器标志
            if v & 0x10:                     # bit4 = 复位
                self.tb_enabled = False
            else:
                self.tb_enabled = bool(v & 0x08)   # bit3 = Timer B 允许中断
        # 其它寄存器（0x24/0x25/0x26）只记录

    # ---------- 调用 ----------
    def call_int(self, vec, ax=0, bx=0, cx=0, dx=0, ds=0, es=0, di=0, si=0):
        u = self.uc
        self.push(0x0202)   # FLAGS
        self.push(MAGIC_SEG)
        self.push(MAGIC_IP)
        ip, cs = struct.unpack('<HH', bytes(u.mem_read(vec * 4, 4)))
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        u.reg_write(UC_X86_REG_AX, ax)
        u.reg_write(UC_X86_REG_BX, bx)
        u.reg_write(UC_X86_REG_CX, cx)
        u.reg_write(UC_X86_REG_DX, dx)
        u.reg_write(UC_X86_REG_DS, ds)
        u.reg_write(UC_X86_REG_ES, es)
        u.reg_write(UC_X86_REG_DI, di)
        u.reg_write(UC_X86_REG_SI, si)
        self.run()


def load_track(pack, name):
    import zipfile
    root = os.environ.get('HOOT_PC98', r'D:\GamedataUnpack\hoot20251231\pc98')
    z = zipfile.ZipFile(os.path.join(root, pack + '.zip'))
    return z.read(name)


def capture(data, ticks=4000, verbose=False):
    sim = CapSim(verbose=verbose)
    sim.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    sim.run()                                  # BIN 启动
    sim.uc.mem_write(lin(DATA_SEG, 0), data)   # 曲子数据
    sim.data_off, sim.data_seg = 0, DATA_SEG
    sim.board_cmd = 1
    sim.call_int(0x7F, ax=0x0001)              # 板命令 1：加载 + 播放
    got = 0
    while got < ticks and sim.tb_enabled:
        sim.tick += 1
        sim.status = 0x02                      # Timer B 到点
        sim.fire_irq(IVT_IRQ)
        got += 1
    return sim, got


if __name__ == '__main__':
    pack = sys.argv[1] if len(sys.argv) > 1 else 'cl_98'
    name = sys.argv[2] if len(sys.argv) > 2 else 'CR001C.FMD'
    ticks = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    data = load_track(pack, name)
    print('%s/%s %d 字节 head=%s' % (pack, name, len(data), data[:8].hex()))
    sim, n = capture(data, ticks=ticks)
    print('ticks=%d  bytes=%d' % (n, len(sim.midi)))
    print(' '.join('%02X' % b for _, b in sim.midi[:160]))

