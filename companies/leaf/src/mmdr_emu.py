# -*- coding: utf-8 -*-
"""MMDR (LEAF / H.Ninomae MIDI Music Driver) 的假时钟运行器。

思路与 AMUS 那条一致：不解析数据，把驱动跑起来，抓它写往 MIDI 接口
(0xE0D0 数据 / 0xE0D2 状态) 的字节。定时器 INT 08h 由我们主动触发，
所以一首曲子可以在秒级跑完，不用像 HOOT 那样实时等着。

用法：
    python mmdr_emu.py 18                  # 导出 SZ_GS18 到 SZ_GS18.mid
    python mmdr_emu.py 18 out.mid
    python mmdr_emu.py --all               # 25 首全导
"""
import os
import struct
import sys
import time

from unicorn import (
    Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN,
    UC_PROT_ALL, UcError,
)
from unicorn.x86_const import (
    UC_X86_REG_AX, UC_X86_REG_DX, UC_X86_REG_SP,
    UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
    UC_X86_REG_IP, UC_X86_INS_IN, UC_X86_INS_OUT,
)

import smf_build

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, '..', 'MIDI-RE', 'mmdr.com')
MUSIC_DIR = os.path.join(HERE, '..', 'MIDI-RE')

PSP_SEG = 0x1000
DATA_SEG = 0x2000
STUB_SEG = 0xE000
MAGIC_IP = 0x0FF0
MEM_SIZE = 0x110000
IVT_08 = 8
IVT_7E = 0x7E
TICK_MS = 10.0              # 8253 计数 0x4E00 @1.9968MHz => 100Hz


def lin(seg, off):
    return ((seg & 0xFFFF) << 4) + (off & 0xFFFF)


class MMDR:
    def __init__(self, verbose=False, driver=None, cmdline=None):
        self.verbose = verbose
        self.driver = driver or DRIVER
        self.cmdline = cmdline
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, MEM_SIZE, UC_PROT_ALL)
        self.uc.mem_write(0, b'\x00' * MEM_SIZE)
        self.midi = []
        self.tick = 0
        self.ports_in = {}
        self.outports = {}
        self.timer_writes = []
        self.dos_calls = []
        self.io_log = []
        self.mpu_ack = None
        self.installed = False
        self._io_hooks()
        self.uc.mem_write(lin(STUB_SEG, MAGIC_IP), b'\xCF')
        self.uc.hook_add(UC_HOOK_CODE, self._on_magic,
                         begin=lin(STUB_SEG, MAGIC_IP), end=lin(STUB_SEG, MAGIC_IP))

    # ---------- I/O ----------
    def _io_hooks(self):
        u = self.uc
        u.hook_add(UC_HOOK_INSN, self._on_in, None, 1, 0, UC_X86_INS_IN)
        u.hook_add(UC_HOOK_INSN, self._on_out, None, 1, 0, UC_X86_INS_OUT)

    def _on_in(self, uc, port, size, user):
        port &= 0xFFFF
        if port == 0xE0D2:                      # MPU 状态口
            val = 0x40 if self.mpu_ack is not None else 0x00
        elif port == 0xE0D0:                    # MPU 数据口
            if self.mpu_ack is not None:
                val = self.mpu_ack
                self.mpu_ack = None
            else:
                val = 0
        else:
            val = self.ports_in.get(port, 0)
        self.io_log.append(('in', port, val))
        return val

    def _on_out(self, uc, port, size, value, user):
        port &= 0xFFFF
        val = value & 0xFF
        self.io_log.append(('out', port, val))
        self.outports[port] = self.outports.get(port, 0) + 1
        if port == 0xE0D2:
            if val == 0xFF:                     # MPU 复位命令 → 回 ACK 0xFE
                self.mpu_ack = 0xFE
            elif getattr(self, 'mpu_ack_all', False):
                self.mpu_ack = 0xFE
        elif port == 0xE0D0:
            self.midi.append((self.tick, val))

    # ---------- INT 拦截 ----------
    def hook_ints(self, base, length):
        u = self.uc
        img = bytes(u.mem_read(base, length))
        n = 0
        for i in range(len(img) - 1):
            if img[i] == 0xCD and img[i + 1] in (0x21, 0x08, 0x7E, 0x20):
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
        ah = (uc.reg_read(UC_X86_REG_AX) >> 8) & 0xFF
        self.dos_calls.append(ah)
        if ah == 0x31:
            self.installed = True
            uc.emu_stop()
        elif ah == 0x4C:
            self.installed = False
            uc.emu_stop()
        elif ah == 0x09:
            dx = uc.reg_read(UC_X86_REG_DX)
            ds = uc.reg_read(UC_X86_REG_DS)
            s = b''
            for i in range(512):
                ch = bytes(uc.mem_read(lin(ds, dx + i), 1))
                if ch == b'$':
                    break
                s += ch
            if self.verbose:
                try:
                    print('    ', s.decode('cp932').strip())
                except Exception:
                    print('    ', s)

    # ---------- 调用 ----------
    def _on_magic(self, uc, address, size, user):
        uc.emu_stop()

    def _push(self, uc, val):
        ss = uc.reg_read(UC_X86_REG_SS)
        sp = (uc.reg_read(UC_X86_REG_SP) - 2) & 0xFFFF
        uc.mem_write(lin(ss, sp), struct.pack('<H', val & 0xFFFF))
        uc.reg_write(UC_X86_REG_SP, sp)

    def call_int(self, vec, ax=0, dx=0, timeout=3_000_000):
        u = self.uc
        ip, cs = struct.unpack('<HH', u.mem_read(lin(0, (vec & 0xFF) * 4), 4))
        if ip == 0 and cs == 0:
            return False
        self._push(u, cs)
        self._push(u, MAGIC_IP)
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        u.reg_write(UC_X86_REG_AX, ax)
        u.reg_write(UC_X86_REG_DX, dx)
        self._run(timeout)
        return True

    def fire_timer(self, timeout=3_000_000):
        u = self.uc
        ip, cs = struct.unpack('<HH', u.mem_read(lin(0, IVT_08 * 4), 4))
        if ip == 0 and cs == 0:
            return False
        self._push(u, 0x0202)
        self._push(u, STUB_SEG)
        self._push(u, MAGIC_IP)
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        self._run(timeout)
        return True

    def _run(self, timeout):
        u = self.uc
        begin = lin(u.reg_read(UC_X86_REG_CS), u.reg_read(UC_X86_REG_IP))
        try:
            u.emu_start(begin, lin(STUB_SEG, MAGIC_IP + 1), 0, timeout)
        except UcError as e:
            if self.verbose:
                print('!! 异常:', e)

    # ---------- 装载 ----------
    def load_driver(self):
        d = open(self.driver, 'rb').read()
        u = self.uc
        u.mem_write(lin(PSP_SEG, 0), struct.pack('<H', 0x20CD))
        u.mem_write(lin(PSP_SEG, 2), struct.pack('<H', 0x9FFF))
        # PSP:0x80 = 命令行长度，随后是内容，以 0x0D 结尾
        if self.cmdline:
            text = b' ' + self.cmdline.encode('ascii') + b'\r'
            u.mem_write(lin(PSP_SEG, 0x80), bytes([len(text) - 1]) + text)
        else:
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

    def load_music(self, path):
        d = open(path, 'rb').read()
        self.uc.mem_write(lin(DATA_SEG, 0), d)
        return len(d)

    # ---------- 导出 ----------
    def export(self, md_path, max_ticks=60000, silence_ticks=600):
        self.load_driver()
        if not self.install():
            raise RuntimeError('驱动安装失败')
        self.load_music(md_path)

        self.call_int(IVT_7E, ax=0x0001)                     # MIDI 复位
        self.call_int(IVT_7E, ax=0x0002, dx=DATA_SEG)        # 播放

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


def scan_timer_writes(writes, max_tick, default_ms=8.13):
    """把 0x77/0x71 的写入还原成「每个 tick 的时长（毫秒）」。

    PC-98 的 8253 时钟是 2.4576 MHz，所以 周期(ms) = count / 2457.6。
    驱动靠改写计数来设定每首曲子的 tempo，必须跟随。
    """
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


def cut_loop(stream, window=512, min_gap=5000, verify=4096):
    """循环曲目在字节流上会原样重复。

    两级判定：先用 512 字节找到候选，再要求后续 4096 字节也完全一致，
    避免把内部的短重复（比如鼓点）误当成整曲循环。
    """
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


def find_music(dirpath, no):
    """不同作品的数据文件名不一样，挨个试。"""
    for pat in ('sz_gs%02d.md', 'GS%02d.MD', 'GS%02d.md', 'gs%02d.md'):
        pit = os.path.join(dirpath, pat % no)
        if os.path.exists(pit):
            return pit
    return None


def run_one(no, out_dir=None, verbose=False, music_dir=None, prefix='SZ_GS'):
    music_dir = music_dir or MUSIC_DIR
    md = find_music(music_dir, no)
    if not md:
        print('缺少 %s%02d 的数据文件' % (prefix, no))
        return None
    t0 = time.time()
    m = MMDR(verbose=verbose, driver=os.path.join(music_dir, 'MMDR.COM'))
    stream = m.export(md)
    full_ticks = m.tick

    # 按驱动设定的定时器把 tick 换算成毫秒
    period = scan_timer_writes(m.timer_writes, full_ticks)
    acc = [0.0] * (full_ticks + 2)
    for i in range(1, full_ticks + 2):
        acc[i] = acc[i - 1] + period[i - 1]
    stream = [(acc[t], b) for t, b in stream]

    stream = cut_loop(stream)
    data, tempo, p = smf_build.build_ms(stream)
    out_dir = out_dir or HERE
    out = os.path.join(out_dir, '%s%02d.mid' % (prefix, no))
    open(out, 'wb').write(data)
    dt = time.time() - t0
    dur = stream[-1][0] / 1000.0 if stream else 0
    tag = '循环' if stream and stream[-1][0] < acc[full_ticks] else '单遍'
    print('%s%02d  %5d 事件  %6.1f 秒  %s  %5.2f 秒算完'
          % (prefix, no, len(p.events), dur, tag, dt))
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description='用假时钟跑 LEAF 的 MMDR 驱动，导出 MIDI')
    ap.add_argument('track', nargs='?', type=int, help='曲号（0 起）')
    ap.add_argument('--dir', help='数据目录（默认取脚本旁的 MIDI-RE）')
    ap.add_argument('--prefix', default=None, help='输出前缀（默认按目录猜）')
    ap.add_argument('--count', type=int, default=26, help='--all 时最多导出几首')
    ap.add_argument('--all', action='store_true', help='批量导出')
    ap.add_argument('--out', help='输出目录')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()

    music_dir = a.dir or MUSIC_DIR
    if a.prefix:
        prefix = a.prefix
    else:
        prefix = 'KZ_GS' if os.path.basename(os.path.normpath(music_dir)).lower() == 'kz' else 'SZ_GS'

    if a.all:
        ok = 0
        for no in range(a.count):
            try:
                if run_one(no, out_dir=a.out, music_dir=music_dir,
                           prefix=prefix, verbose=a.verbose):
                    ok += 1
            except Exception as e:
                print('%s%02d 失败: %s' % (prefix, no, e))
        print('完成 %d 首' % ok)
        return
    if a.track is None:
        ap.print_help()
        return
    run_one(a.track, out_dir=a.out, music_dir=music_dir,
            prefix=prefix, verbose=a.verbose)


if __name__ == '__main__':
    main()
