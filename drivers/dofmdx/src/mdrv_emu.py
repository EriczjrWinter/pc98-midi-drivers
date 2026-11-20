# -*- coding: utf-8 -*-
"""DOFMDX98 / MDRV98（D.O. 的 MIDI 驱动）的假时钟运行器。

装载模型（从 DOFMD_98.BIN 的代码反推出来的）：
    CS:0000        DOFMD_98.BIN   206 字节，入口就是 0
    CS:00CE        MDRV98         11519 字节，紧接在后面
    SP = 0x4CE

BIN 干的事：
    out 0x7E8, 0x80       声卡控制
    int 45h / int 14h     BIOS 调用
    IVT[0x7F] = CS:0x39   挂功能调用
    out 0x7E8, 0x81
    sti / hlt

功能调用走 INT 7Fh，AH = 功能号（代码里 cmp ah, 0Ch）。
"""
import os
import struct
import sys

from unicorn import (Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE,
                     UC_HOOK_INSN, UC_PROT_ALL, UcError)
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
                               UC_X86_REG_DX, UC_X86_REG_SP, UC_X86_REG_BP,
                               UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_CS,
                               UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
                               UC_X86_REG_IP, UC_X86_INS_IN, UC_X86_INS_OUT)

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = 0x2000
MEM = 0x110000
STUB_SEG = 0xE000
MAGIC_IP = 0x0FF0
IVT_API = 0x7F
IVT_TIMER = 0x08

PORTS_DATA = (0x7D0, 0x7D2)     # 数据口
PORTS_STAT = (0x7E0, 0x7E2)     # 状态口
PORTS_CTRL = (0x7E8,)           # 控制口


def lin(seg, off):
    return ((seg & 0xFFFF) << 4) + (off & 0xFFFF)


class MDRV:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, MEM, UC_PROT_ALL)
        self.uc.mem_write(0, b'\x00' * MEM)
        self.midi = []
        self.tick = 0
        self.io_log = []
        self.installed = False
        self.vectors = {}
        self.api_ip = None
        self.uc.mem_write(lin(STUB_SEG, MAGIC_IP), b'\xCF')
        self.uc.hook_add(UC_HOOK_CODE, self._on_magic,
                         begin=lin(STUB_SEG, MAGIC_IP),
                         end=lin(STUB_SEG, MAGIC_IP))
        u = self.uc
        u.hook_add(UC_HOOK_INSN, self._on_in, None, 1, 0, UC_X86_INS_IN)
        u.hook_add(UC_HOOK_INSN, self._on_out, None, 1, 0, UC_X86_INS_OUT)

    # ---------- I/O ----------
    def _on_in(self, uc, port, size, user):
        port &= 0xFFFF
        val = 0
        self.io_log.append(('in', port, val))
        return val

    def _on_out(self, uc, port, size, value, user):
        port &= 0xFFFF
        val = value & 0xFF
        self.io_log.append(('out', port, val))
        if port in PORTS_DATA:
            self.midi.append((self.tick, val))

    # ---------- 中断 ----------
    def _on_int(self, uc, address, size, user):
        vec = bytes(uc.mem_read(address + 1, 1))[0]
        ax = uc.reg_read(UC_X86_REG_AX)
        ah = (ax >> 8) & 0xFF
        self.events.append((vec, ah))
        if vec == 0x21:
            self._dos(uc, ah, ax)
        uc.reg_write(UC_X86_REG_IP,
                     (uc.reg_read(UC_X86_REG_IP) + 2) & 0xFFFF)

    def _dos(self, uc, ah, ax):
        if ah == 0x25:
            v = ax & 0xFF
            dx = uc.reg_read(UC_X86_REG_DX)
            ds = uc.reg_read(UC_X86_REG_DS)
            self.vectors[v] = (dx, ds)
            uc.mem_write(lin(0, v * 4), struct.pack('<HH', dx, ds))
        elif ah == 0x35:
            v = ax & 0xFF
            ip, cs = self.vectors.get(v, (0, 0))
            uc.reg_write(UC_X86_REG_BX, ip)
            uc.reg_write(UC_X86_REG_ES, cs)
        elif ah in (0x4C, 0x31):
            self.installed = (ah == 0x31)
            uc.emu_stop()

    def hook_ints(self, base, length):
        u = self.uc
        img = bytes(u.mem_read(base, length))
        n = 0
        for i in range(len(img) - 1):
            if img[i] == 0xCD and img[i + 1] in (0x21, 0x45, 0x14, 0x7F, 0x08):
                a = base + i
                u.hook_add(UC_HOOK_CODE, self._on_int, begin=a, end=a)
                n += 1
        return n

    def _on_magic(self, uc, address, size, user):
        uc.emu_stop()

    def _push(self, uc, val):
        ss = uc.reg_read(UC_X86_REG_SS)
        sp = (uc.reg_read(UC_X86_REG_SP) - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', val & 0xFFFF))
        uc.reg_write(UC_X86_REG_SP, sp)

    def _run(self, timeout=5_000_000):
        u = self.uc
        begin = lin(u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP))
        try:
            u.emu_start(begin, lin(STUB_SEG, MAGIC_IP + 1), 0, timeout)
        except UcError as e:
            if self.verbose:
                print('  !! 停止:', e)

    # ---------- 装载 ----------
    def load(self, bin_path, drv_path):
        b = open(bin_path, 'rb').read()
        d = open(drv_path, 'rb').read()
        self.uc.mem_write(lin(SEG, 0), b + d)
        self.bin_len = len(b)
        self.drv_len = len(d)
        self.code_base = lin(SEG, 0)
        self.code_len = len(b) + len(d)
        u = self.uc
        for r in (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES):
            u.reg_write(r, SEG)
        u.reg_write(UC_X86_REG_SS, SEG)
        u.reg_write(UC_X86_REG_SP, 0x4CE)
        u.reg_write(UC_X86_REG_IP, 0)

    def install(self, timeout=3_000_000):
        self.events = []
        self.hook_ints(self.code_base, self.code_len)
        self._run(timeout)
        v = self.vectors.get(IVT_API) or self._read_ivt(IVT_API)
        return v

    def _read_ivt(self, vec):
        ip, cs = struct.unpack('<HH',
                               bytes(self.uc.mem_read(lin(0, vec * 4), 4)))
        if ip or cs:
            self.vectors[vec] = (ip, cs)
        return self.vectors.get(vec)

    def fire_api(self, ax=0, dx=0, bx=0):
        v = self.vectors.get(IVT_API)
        if not v:
            return False
        ip, cs = v
        u = self.uc
        self._push(u, cs)
        self._push(u, MAGIC_IP)
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        u.reg_write(UC_X86_REG_AX, ax)
        u.reg_write(UC_X86_REG_DX, dx)
        u.reg_write(UC_X86_REG_BX, bx)
        self._run()
        return True


if __name__ == '__main__':
    m = MDRV(verbose=True)
    m.load(os.path.join(HERE, 'DOFMD_98.BIN'), os.path.join(HERE, 'MDRV98'))
    print('装载 %d + %d 字节' % (m.bin_len, m.drv_len))
    v = m.install()
    print('安装:', v)
    print('INT 7Fh 向量:', v)
    print('中断调用:', [(hex(a), hex(b)) for a, b in m.events[:12]])
    print('I/O 端口:', sorted(set(p for _, p, _ in m.io_log)))
    print('MIDI 字节:', len(m.midi))
