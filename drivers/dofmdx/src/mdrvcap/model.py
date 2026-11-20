# -*- coding: utf-8 -*-
"""正确布局下的 MDRV98 装载与调用实验。

布局（来自 DOFMD_98.BIN 的代码）：
    BIN  线性 0x0600 = 段 0x0060:0000    （bootcs=0x0060, bootip=0）
    DRV  线性 0x0FA0 = 段 0x00FA:0000    （XML 里 offset=0xfa0）
BIN 自己把 IVT[0x45] 指向 0x00FA:0000，把 IVT[0x7F] 指向 BIN:0x39。
"""
import os
import struct
import sys

from unicorn import (Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE,
                     UC_HOOK_INSN, UC_HOOK_INTR, UC_PROT_ALL, UcError)
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_BP, UC_X86_REG_SP,
    UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
    UC_X86_REG_IP, UC_X86_REG_FLAGS, UC_X86_INS_IN, UC_X86_INS_OUT,
    UC_X86_INS_HLT)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BASE = 0x600
DRV_BASE = 0xFA0
DRV_SEG = DRV_BASE >> 4          # 0x00FA
BIN_SEG = BIN_BASE >> 4          # 0x0060
MAGIC_SEG = 0xE000
MAGIC_IP = 0x0FFF
DATA_SEG = 0x4000


def lin(s, o):
    return ((s & 0xFFFF) << 4) + (o & 0xFFFF)


class Sim:
    def __init__(self, verbose=False, tracing=False):
        self.verbose = verbose
        self.tracing = tracing
        self.io = []
        self.midi = []
        self.out_log = []
        self.in_log = []
        self.ints = []
        self.int_log = []
        self.last_out = {}
        self.trace = []
        self.probed_0xe0d2 = False
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x120000, UC_PROT_ALL)
        self.uc.mem_write(0, b'\x00' * 0x120000)
        self.uc.mem_write(lin(MAGIC_SEG, MAGIC_IP), b'\xf4')  # hlt
        u = self.uc
        u.hook_add(UC_HOOK_INSN, self._on_in, None, 1, 0, UC_X86_INS_IN)
        u.hook_add(UC_HOOK_INSN, self._on_out, None, 1, 0, UC_X86_INS_OUT)
        u.hook_add(UC_HOOK_INTR, self._on_intr)

    def _on_intr(self, uc, intno, user):
        """unicorn 16 位模式不自动派发 INT，这里手动做真实模式派发。"""
        self.ints.append(intno)
        self.int_log.append((intno, uc.reg_read(UC_X86_REG_CS),
                             uc.reg_read(UC_X86_REG_IP),
                             uc.reg_read(UC_X86_REG_SP)))
        ip, cs = struct.unpack('<HH', bytes(uc.mem_read(intno * 4, 4)))
        if ip == 0 and cs == 0:
            return
        # 当前 IP 已经越过 int 指令
        ret_ip = uc.reg_read(UC_X86_REG_IP)
        ret_cs = uc.reg_read(UC_X86_REG_CS)
        fl = uc.reg_read(UC_X86_REG_FLAGS)
        ss = uc.reg_read(UC_X86_REG_SS)
        sp = uc.reg_read(UC_X86_REG_SP)
        sp = (sp - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', fl))
        sp = (sp - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', ret_cs))
        sp = (sp - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', ret_ip))
        uc.reg_write(UC_X86_REG_SP, sp)
        uc.reg_write(UC_X86_REG_CS, cs)
        uc.reg_write(UC_X86_REG_IP, ip)

    # ---------- I/O ----------
    def _on_in(self, uc, port, size, user):
        port &= 0xFFFF
        if port == 0xE0D2:
            # 状态口：bit7=有数据，bit6=忙。第一次读回 0xFF 让驱动认出 MIDI 板。
            if not self.probed_0xe0d2:
                self.probed_0xe0d2 = True
                val = 0xFF
            else:
                val = 0x00
        elif port == 0xE0D0:
            val = 0xFE        # 数据口：回 ACK
        else:
            val = self.last_out.get(port, 0x00)
        self.in_log.append((port, val))
        return val

    def _on_out(self, uc, port, size, value, user):
        port &= 0xFFFF
        v = value & 0xFF
        self.last_out[port] = v
        self.out_log.append((port, v))
        if port in (0xE0D0, 0xE0D2):
            self.midi.append(v)

    def _on_hlt(self, uc, user):
        uc.emu_stop()

    # ---------- 执行 ----------
    def run(self, timeout=20_000_000):
        u = self.uc
        begin = lin(u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP))
        hid = None
        if self.tracing:
            self.trace = []
            hid = u.hook_add(UC_HOOK_CODE, self._trace_code)
        try:
            u.emu_start(begin, lin(MAGIC_SEG, MAGIC_IP), 0, timeout)
        except UcError as e:
            print('  !! UcError:', e)
            print('     at %04X:%04X AX=%04X BX=%04X CX=%04X DX=%04X DS=%04X ES=%04X' % (
                u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP),
                u.reg_read(UC_X86_REG_AX), u.reg_read(UC_X86_REG_BX),
                u.reg_read(UC_X86_REG_CX), u.reg_read(UC_X86_REG_DX),
                u.reg_read(UC_X86_REG_DS), u.reg_read(UC_X86_REG_ES)))
            if self.trace:
                print('     trace:', ' '.join('%04X:%04X' % t for t in self.trace[-25:]))
        finally:
            if hid is not None:
                u.hook_del(hid)

    def _trace_code(self, uc, address, size, user):
        self.trace.append((uc.reg_read(UC_X86_REG_CS), address & 0xFFFF))
        if len(self.trace) > 4000:
            del self.trace[:2000]

    def push(self, val):
        u = self.uc
        ss = u.reg_read(UC_X86_REG_SS)
        sp = (u.reg_read(UC_X86_REG_SP) - 2) & 0xFFFF
        u.mem_write(lin(ss, sp), struct.pack('<H', val & 0xFFFF))
        u.reg_write(UC_X86_REG_SP, sp)

    def load(self, bin_path, drv_path):
        b = open(bin_path, 'rb').read()
        d = open(drv_path, 'rb').read()
        self.bin_len, self.drv_len = len(b), len(d)
        u = self.uc
        u.mem_write(BIN_BASE, b)
        u.mem_write(DRV_BASE, d)
        u.reg_write(UC_X86_REG_CS, BIN_SEG)
        u.reg_write(UC_X86_REG_IP, 0)
        u.reg_write(UC_X86_REG_SS, BIN_SEG)
        u.reg_write(UC_X86_REG_SP, 0x4CE)
        u.reg_write(UC_X86_REG_DS, BIN_SEG)
        u.reg_write(UC_X86_REG_ES, BIN_SEG)

    def call_driver(self, ax=0, bx=0, cx=0, dx=0, ds=0, es=0, di=0, si=0,
                    timeout=20_000_000):
        u = self.uc
        self.push(u.reg_read(UC_X86_REG_FLAGS))
        self.push(MAGIC_SEG)
        self.push(MAGIC_IP)
        u.reg_write(UC_X86_REG_CS, DRV_SEG)
        u.reg_write(UC_X86_REG_IP, 0)
        u.reg_write(UC_X86_REG_AX, ax)
        u.reg_write(UC_X86_REG_BX, bx)
        u.reg_write(UC_X86_REG_CX, cx)
        u.reg_write(UC_X86_REG_DX, dx)
        u.reg_write(UC_X86_REG_DS, ds)
        u.reg_write(UC_X86_REG_ES, es)
        u.reg_write(UC_X86_REG_DI, di)
        u.reg_write(UC_X86_REG_SI, si)
        self.run(timeout)

    def fire_irq(self, vec, timeout=20_000_000):
        u = self.uc
        ip, cs = struct.unpack('<HH', bytes(u.mem_read(vec * 4, 4)))
        if ip == 0 and cs == 0:
            return False
        self.push(u.reg_read(UC_X86_REG_FLAGS))
        self.push(u.reg_read(UC_X86_REG_CS))
        self.push(u.reg_read(UC_X86_REG_IP))
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        self.run(timeout)
        return True


def ivt_dump(sim):
    u = sim.uc
    for vec in range(0x100):
        ip, cs = struct.unpack('<HH', bytes(u.mem_read(vec * 4, 4)))
        if ip or cs:
            print('  INT %02X -> %04X:%04X' % (vec, cs, ip))


if __name__ == '__main__':
    sim = Sim(verbose=True)
    sim.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    print('装载 BIN@%04X DRV@%04X (seg %04X)' % (BIN_BASE, DRV_BASE, DRV_SEG))
    sim.run()
    print('BIN 装完。IVT:')
    ivt_dump(sim)
    print('端口访问:', sorted(set(p for p, _ in sim.out_log)))
    print('INT 21 调用?（BIN 不该有）')


