# -*- coding: utf-8 -*-
"""MS.COM（LEAF / 雀鬼・Filsnown 的 MIDI 驱动）的假时钟运行器。

思路与 MMDR 那条一致：不解析数据，把驱动跑起来，抓它写往
MIDI 接口的字节。INT 08h 由我们主动触发，所以一首曲子秒级跑完。

与 MMDR 的差别：
  - 功能调用走 INT 7Fh（MMDR 是 7Eh）
  - 数据文件名是 .MD / .MID，头部有 "RM" 魔数（驱动自己解）

用法：
    python mscom_emu.py --list            # 看有哪些数据文件
    python mscom_emu.py FR_GS00           # 导出一首
    python mscom_emu.py --all             # 全导
"""
import argparse
import os
import struct
import sys
import time

from unicorn import (
    Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN,
    UC_PROT_ALL, UcError,
)
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
    UC_X86_REG_SP, UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI,
    UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
    UC_X86_REG_IP, UC_X86_INS_IN, UC_X86_INS_OUT,
)

PSP_SEG = 0x1000
DATA_SEG = 0x2000
STUB_SEG = 0xE000
MAGIC_IP = 0x0FF0
MEM_SIZE = 0x110000
IVT_08 = 0x08
IVT_API = 0x7F              # MS.COM 用 7Fh

DEFAULT_MS = 8.13


def lin(seg, off):
    return ((seg & 0xFFFF) << 4) + (off & 0xFFFF)


class MSCom:
    def __init__(self, verbose=False, driver=None):
        self.verbose = verbose
        self.driver = driver
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, MEM_SIZE, UC_PROT_ALL)
        self.uc.mem_write(0, b'\x00' * MEM_SIZE)
        self.midi = []           # [(tick, byte)]
        self.tick = 0
        self.timer_writes = []
        self.dos_calls = []
        self.io_log = []
        self.installed = False
        self.vectors = {}        # 我们替 DOS 管的 IVT
        self.mpu_ack = None
        self.mpu_ack_all = True
        self._io_hooks()
        self.uc.mem_write(lin(STUB_SEG, MAGIC_IP), b'\xCF')
        self.uc.hook_add(UC_HOOK_CODE, self._on_magic,
                         begin=lin(STUB_SEG, MAGIC_IP),
                         end=lin(STUB_SEG, MAGIC_IP))

    # ---------- I/O ----------
    def _io_hooks(self):
        u = self.uc
        u.hook_add(UC_HOOK_INSN, self._on_in, None, 1, 0, UC_X86_INS_IN)
        u.hook_add(UC_HOOK_INSN, self._on_out, None, 1, 0, UC_X86_INS_OUT)

    def _on_in(self, uc, port, size, user):
        port &= 0xFFFF
        if port == 0xE0D2:
            val = 0x40 if self.mpu_ack is not None else 0x00
        elif port == 0xE0D0:
            if self.mpu_ack is not None:
                val = self.mpu_ack
                self.mpu_ack = None
            else:
                val = 0
        else:
            val = 0
        self.io_log.append(('in', port, val))
        return val

    def _on_out(self, uc, port, size, value, user):
        port &= 0xFFFF
        val = value & 0xFF
        self.io_log.append(('out', port, val))
        if port in (0x77, 0x71):
            self.timer_writes.append((self.tick, port, val))
        elif port == 0xE0D2:
            if val == 0xFF:
                self.mpu_ack = 0xFE
            elif self.mpu_ack_all:
                self.mpu_ack = 0xFE
        elif port == 0xE0D0:
            self.midi.append((self.tick, val))

    # ---------- INT ----------
    def hook_ints(self, base, length):
        u = self.uc
        img = bytes(u.mem_read(base, length))
        n = 0
        for i in range(len(img) - 1):
            if img[i] == 0xCD and img[i + 1] in (0x21, 0x08, 0x7F, 0x20):
                a = base + i
                u.hook_add(UC_HOOK_CODE, self._on_int, begin=a, end=a)
                n += 1
        return n

    def _on_int(self, uc, address, size, user):
        vec = bytes(uc.mem_read(address + 1, 1))[0]
        if vec == 0x21:
            self._dos(uc)
        uc.reg_write(UC_X86_REG_IP, (uc.reg_read(UC_X86_REG_IP) + 2) & 0xFFFF)

    def _dos(self, uc):
        ax = uc.reg_read(UC_X86_REG_AX)
        ah = (ax >> 8) & 0xFF
        self.dos_calls.append(ah)
        if ah == 0x31:                       # TSR
            self.installed = True
            uc.emu_stop()
        elif ah == 0x4C:                     # 退出
            self.installed = False
            uc.emu_stop()
        elif ah == 0x35:                     # 取中断向量 → ES:BX
            vec = ax & 0xFF
            ip, cs = self.vectors.get(vec, (0, 0))
            uc.reg_write(UC_X86_REG_BX, ip)
            uc.reg_write(UC_X86_REG_ES, cs)
            uc.reg_write(UC_X86_REG_AX, ip)
        elif ah == 0x25:                     # 设中断向量 ← DS:DX
            vec = ax & 0xFF
            dx = uc.reg_read(UC_X86_REG_DX)
            ds = uc.reg_read(UC_X86_REG_DS)
            self.vectors[vec] = (dx, ds)
            uc.mem_write(lin(0, vec * 4), struct.pack('<HH', dx, ds))
            self.uc.mem_write(lin(0, vec * 4), struct.pack('<HH', dx, ds))
        elif ah == 0x30:                     # DOS 版本
            uc.reg_write(UC_X86_REG_AX, 0x0005)
            uc.reg_write(UC_X86_REG_BX, 0x0000)
            uc.reg_write(UC_X86_REG_CX, 0x0000)
        elif ah == 0x4A or ah == 0x49:       # 分配/释放内存
            uc.reg_write(UC_X86_REG_AX, 0x0000)
        elif ah == 0x09:
            if self.verbose:
                dx = uc.reg_read(UC_X86_REG_DX)
                ds = uc.reg_read(UC_X86_REG_DS)
                s = b''
                for i in range(512):
                    ch = bytes(uc.mem_read(lin(ds, dx + i), 1))
                    if ch == b'$':
                        break
                    s += ch
                print('     >>', s)

    # ---------- 运行 ----------
    def _on_magic(self, uc, address, size, user):
        uc.emu_stop()

    def _push(self, uc, val):
        ss = uc.reg_read(UC_X86_REG_SS)
        sp = (uc.reg_read(UC_X86_REG_SP) - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', val & 0xFFFF))
        uc.reg_write(UC_X86_REG_SP, sp)

    def _run(self, timeout=4_000_000):
        u = self.uc
        begin = lin(u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP))
        try:
            u.emu_start(begin, lin(STUB_SEG, MAGIC_IP + 1), 0, timeout)
        except UcError as e:
            if self.verbose:
                print('!! 异常:', e)

    def fire_timer(self):
        v = self.vectors.get(IVT_08)
        if not v:
            return False
        ip, cs = v
        u = self.uc
        self._push(u, 0x0202)
        self._push(u, STUB_SEG)
        self._push(u, MAGIC_IP)
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        self._run()
        return True

    def call_api(self, ax=0, dx=0, bx=None, es=None):
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
        if bx is not None:
            u.reg_write(UC_X86_REG_BX, bx)
        if es is not None:
            u.reg_write(UC_X86_REG_ES, es)
        self._run()
        return True

    # ---------- 装载 ----------
    def load_driver(self):
        d = open(self.driver, 'rb').read()
        u = self.uc
        u.mem_write(lin(PSP_SEG, 0), struct.pack('<H', 0x20CD))
        u.mem_write(lin(PSP_SEG, 2), struct.pack('<H', 0x9FFF))
        u.mem_write(lin(PSP_SEG, 0x80), b'\x00\x0d')
        u.mem_write(lin(PSP_SEG, 0x100), d)
        for r in (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS):
            u.reg_write(r, PSP_SEG)
        u.reg_write(UC_X86_REG_SP, 0xFF00)
        u.reg_write(UC_X86_REG_IP, 0x100)
        self.code_base = lin(PSP_SEG, 0x100)
        self.code_len = len(d)

    def install(self):
        self.hook_ints(self.code_base, self.code_len)
        self._run(20_000_000)
        return self.installed

    def load_music(self, data):
        self.uc.mem_write(lin(DATA_SEG, 0), data)
        return len(data)

    # ---------- 导出 ----------
    def export(self, data, max_ticks=45000, silence_ticks=10 ** 9):
        self.load_driver()
        if not self.install():
            raise RuntimeError('驱动安装失败')
        self.load_music(data)
        self.midi.clear()
        # AH=1：播放；数据指针走 ES:BX
        self.call_api(ax=0x0100, bx=0, es=DATA_SEG)

        quiet = 0
        last = 0
        for _ in range(max_ticks):
            self.tick += 1
            if not self.fire_timer():
                raise RuntimeError('INT 08h 未安装')
            if len(self.midi) != last:
                last = len(self.midi)
                quiet = 0
            else:
                quiet += 1
                if quiet > silence_ticks:
                    break
        return self.midi


def scan_timer_writes(writes, max_tick, default_ms=DEFAULT_MS):
    period = [default_ms] * (max_tick + 2)
    buf = []
    marks = []
    for t, p, v in writes:
        if p == 0x77:
            buf = []
        elif p == 0x71:
            buf.append(v & 0xFF)
            if len(buf) == 2:
                cnt = buf[0] | (buf[1] << 8)
                if cnt > 0:
                    marks.append((t, cnt / 2457.6))
    for i, (t, ms) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else max_tick + 1
        for k in range(max(0, t), min(end, max_tick + 2)):
            period[k] = ms
    return period


def cut_loop(stream, window=1024, min_gap=20000, verify=8192):
    """循环曲目在字节流上会原样重复。两级判定：先用 512 字节找候选，
    再要求后续 4096 字节也完全一致，避免误判内部的短重复（比如鼓点）。"""
    b = [x for _, x in stream]
    first = {}
    for i in range(len(b) - window):
        k = bytes(b[i:i + window])
        if k in first and i - first[k] > min_gap:
            j = first[k]
            n = min(verify, len(b) - i, len(b) - j)
            if n > 0 and bytes(b[j:j + n]) == bytes(b[i:i + n]):
                return stream[:i]
        if k not in first:
            first[k] = i
    return stream


def run_one(path, out_path, verbose=False):
    data = open(path, 'rb').read()
    here = os.path.dirname(os.path.abspath(__file__))
    m = MSCom(verbose=verbose, driver=os.path.join(here, 'ms.com'))
    stream = m.export(data)
    period = scan_timer_writes(m.timer_writes, m.tick)
    acc = [0.0] * (m.tick + 2)
    for i in range(1, m.tick + 2):
        acc[i] = acc[i - 1] + period[i - 1]
    ms = [(acc[t], b) for t, b in stream]
    # 不做循环裁剪：让驱动跑到自己停，长度才准
    sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')
    import smf_build
    smf, tempo, p = smf_build.build_ms(ms)
    open(out_path, 'wb').write(smf)
    dur = ms[-1][0] / 1000.0 if ms else 0
    print('%-14s %4d 事件 %6.1f 秒 → %s'
          % (os.path.basename(path), len(p.events), dur,
             os.path.basename(out_path)))
    return out_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('music', nargs='?', help='数据文件名（与本脚本同目录）')
    ap.add_argument('--out', default='out')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, a.out)
    os.makedirs(outdir, exist_ok=True)
    if a.all:
        import glob
        n = 0
        for f in sorted(glob.glob(os.path.join(here, '*.MD')) +
                        glob.glob(os.path.join(here, '*.MID'))):
            try:
                run_one(f, os.path.join(outdir,
                                        os.path.splitext(os.path.basename(f))[0] + '.mid'),
                        a.verbose)
                n += 1
            except Exception as e:
                print('%-14s 失败: %s' % (os.path.basename(f), e))
        print('完成', n, '首')
    elif a.music:
        run_one(os.path.join(here, a.music),
                os.path.join(outdir, os.path.splitext(os.path.basename(a.music))[0] + '.mid'),
                a.verbose)
    else:
        ap.print_help()
