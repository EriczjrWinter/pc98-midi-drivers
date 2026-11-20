# -*- coding: utf-8 -*-
"""MSDRV4.EXE 的装载试探：按 MZ 头装进内存，跑起来看它想干什么。"""
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

H = r'D:\GamedataUnpack\hoot20251231\pc98'
EXE = os.path.join(r'D:\gf\pc98-midi-drivers\drivers\msdrv\src', 'MSDRV4.EXE')

MEM = 0x110000
PSP_SEG = 0x1000
LOAD_SEG = PSP_SEG + 0x10   # EXE 的 load module 在 PSP 之后 0x10 段处


def lin(seg, off):
    return ((seg & 0xFFFF) << 4) + (off & 0xFFFF)


def parse_mz(d):
    (last, pages, relocs, hdr, minalloc, maxalloc, ss, sp, csum,
     ip, cs, reloc_off, ovl) = struct.unpack_from('<HHHHHHHHHHHHH', d, 2)
    size = pages * 512 - (512 - last if last else 0)
    return dict(size=size, hdr=hdr * 16, ss=ss, sp=sp, ip=ip, cs=cs,
                relocs=relocs, reloc_off=reloc_off)


class Loader:
    def __init__(self, path, verbose=True):
        self.d = open(path, 'rb').read()
        self.mz = parse_mz(self.d)
        self.verbose = verbose
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, MEM, UC_PROT_ALL)
        self.uc.mem_write(0, b'\x00' * MEM)
        self.dos = []
        self.ints = []
        self.outs = []
        self.installed = False
        self.vectors = {}
        self.strings = []
        # 预置常用中断向量：指向一块只有 IRET 的假存根
        stub = 0xE000
        self.uc.mem_write(lin(stub, 0), b'\\xCF')
        for v in (0x08, 0x09, 0x1B, 0x1C, 0x23, 0x24, 0x2F):
            self.vectors[v] = (0x0000, stub)
        self.uc.hook_add(UC_HOOK_INSN, self._on_in, None, 1, 0, UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INSN, self._on_out, None, 1, 0, UC_X86_INS_OUT)
        self._load()

    def _load(self):
        d, mz = self.d, self.mz
        body = d[mz['hdr']:mz['size']]
        base = lin(LOAD_SEG, 0)
        self.uc.mem_write(base, body)
        # 重定位表：每项 4 字节 (偏移, 段)
        n = 0
        for i in range(mz['relocs']):
            off = mz['reloc_off'] + i * 4
            if off + 4 > len(d):
                break
            o, s = struct.unpack_from('<HH', d, off)
            addr = base + (s << 4) + o
            v = struct.unpack('<H', bytes(self.uc.mem_read(addr, 2)))[0]
            self.uc.mem_write(addr, struct.pack('<H', (v + LOAD_SEG) & 0xFFFF))
            n += 1
        self.reloc_n = n
        u = self.uc
        u.mem_write(lin(PSP_SEG, 0), struct.pack('<H', 0x20CD))
        u.mem_write(lin(PSP_SEG, 2), struct.pack('<H', 0x9FFF))
        u.mem_write(lin(PSP_SEG, 0x80), b'\x00\x0d')
        for r in (UC_X86_REG_DS, UC_X86_REG_ES):
            u.reg_write(r, PSP_SEG)
        u.reg_write(UC_X86_REG_SS, (LOAD_SEG + mz['ss']) & 0xFFFF)
        u.reg_write(UC_X86_REG_SP, mz['sp'] or 0xFFFE)
        u.reg_write(UC_X86_REG_CS, (LOAD_SEG + mz['cs']) & 0xFFFF)
        u.reg_write(UC_X86_REG_IP, mz['ip'])
        self.code_base = lin((LOAD_SEG + mz['cs']) & 0xFFFF, mz['ip'])

    def _on_in(self, uc, port, size, user):
        self.ints.append(('in', port & 0xFFFF, 0))
        return 0xFF

    def _on_out(self, uc, port, size, value, user):
        self.outs.append((port & 0xFFFF, value & 0xFF))

    def _on_int(self, uc, address, size, user):
        vec = bytes(uc.mem_read(address + 1, 1))[0]
        ax = uc.reg_read(UC_X86_REG_AX)
        ah = (ax >> 8) & 0xFF
        self.dos.append((vec, ah))
        if vec == 0x21:
            self._dos(uc, ah, ax)
        uc.reg_write(UC_X86_REG_IP,
                     (uc.reg_read(UC_X86_REG_IP) + 2) & 0xFFFF)

    def _dos(self, uc, ah, ax):
        if ah == 0x35:                       # 取向量 → ES:BX
            v = self.vectors.get(ax & 0xFF, (0, 0))
            uc.reg_write(UC_X86_REG_BX, v[0])
            uc.reg_write(UC_X86_REG_ES, v[1])
        elif ah == 0x25:                     # 设向量 ← DS:DX
            vx = ax & 0xFF
            dx = uc.reg_read(UC_X86_REG_DX)
            ds = uc.reg_read(UC_X86_REG_DS)
            self.vectors[vx] = (dx, ds)
            uc.mem_write(lin(0, vx * 4), struct.pack('<HH', dx, ds))
        elif ah == 0x30:
            uc.reg_write(UC_X86_REG_AX, 0x0005)
        elif ah == 0x09:
            if self.verbose:
                dx = uc.reg_read(UC_X86_REG_DX)
                ds = uc.reg_read(UC_X86_REG_DS)
                s = b''
                for i in range(256):
                    ch = bytes(uc.mem_read(lin(ds, dx + i), 1))
                    if ch == b'$':
                        break
                    s += ch
                self.strings.append(s)
        elif ah in (0x48, 0x49, 0x4A):
            uc.reg_write(UC_X86_REG_AX, 0)
        elif ah in (0x4C, 0x31):
            self.installed = (ah == 0x31)
            uc.emu_stop()

    def hook_ints(self):
        u = self.uc
        # 扫整块内存找 CD xx
        n = 0
        for seg_off in range(0, len(self.d) - self.mz['hdr'] - 1):
            pass
        body = self.d[self.mz['hdr']:self.mz['size']]
        base = lin(LOAD_SEG, 0)
        for i in range(len(body) - 1):
            if body[i] == 0xCD and body[i + 1] in (0x21, 0x08, 0x7F, 0x20, 0x16):
                a = base + i
                u.hook_add(UC_HOOK_CODE, self._on_int, begin=a, end=a)
                n += 1
        return n

    def run(self, timeout=5_000_000):
        u = self.uc
        try:
            u.emu_start(self.code_base, 0, 0, timeout)
        except UcError as e:
            if self.verbose:
                print('  !! 停止:', e)
        return (u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP))


if __name__ == '__main__':
    L = Loader(EXE)
    print('MZ:', L.mz)
    print('重定位项:', L.reloc_n)
    print('入口 CS:IP = %04X:%04X' % (L.uc.reg_read(UC_X86_REG_CS),
                                     L.uc.reg_read(UC_X86_REG_IP)))
    n = L.hook_ints()
    print('挂钩 CD xx:', n, '处')
    cs, ip = L.run(2_000_000)
    print('停在 %04X:%04X' % (cs, ip))
    print('DOS 调用:', [('INT%02X' % v, 'AH=%02X' % a) for v, a in L.dos[:20]])
    print('out 端口:', sorted(set(p for p, _ in L.outs))[:10])
