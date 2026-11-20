# -*- coding: utf-8 -*-
"""用 Unicorn 运行 system3.exe 的音乐引擎，抓 midiOutShortMsg。

接管点：
  0x40d311  calloc            → 自己的 bump 分配器
  0x40d2ff  malloc            → 同上
  0x40d216  free              → 空操作
  0x40d439  CreateThread 包装 → 返回 0（不真开线程）
  0x4053e0  load(path, song, &size) → 直接返回 AMUS.DAT 里对应歌曲表指针
  0x405650  备用 load（4 参）  → 同上
"""
from __future__ import annotations
import os
import struct
import sys

from unicorn import (Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_PROT_ALL, UC_PROT_READ, UC_PROT_WRITE)
from unicorn.x86_const import *

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Galgame\PC98-DOS-WIN95\GAME\AMBIVALENZ\system3.exe"
AMUS = r"D:\GamedataUnpack\alice-tools-0.13.0\AMUS.DAT"

IMAGE_BASE = 0x400000
STUB_BASE = 0x30000000
HEAP_BASE = 0x20000000
HEAP_SIZE = 0x800000
STACK_BASE = 0x10000000
STACK_SIZE = 0x200000
TEB_BASE = 0x7FFD0000
FILEDATA_BASE = 0x60000000

RET_MAGIC = 0xFFFFFFF0

NARGS = {'midiOutShortMsg': 2, 'midiOutOpen': 4, 'midiOutClose': 1,
         # chip 初始化（0x405E40）会走这几个，缺了会导致栈不平衡 → ret 到 0
         'midiOutLongMsg': 3, 'midiOutPrepareHeader': 3,
         'midiOutUnprepareHeader': 3, 'midiInAddBuffer': 3,
         'FindResourceA': 3, 'LoadResource': 1, 'LockResource': 1,
         'SizeofResource': 2, 'GetModuleHandleA': 1, 'GetModuleHandleW': 1,
         'timeGetTime': 0, 'Sleep': 1, 'CreateThread': 6, 'CloseHandle': 1,
         'VirtualAlloc': 4, 'VirtualFree': 3, 'HeapAlloc': 3, 'HeapCreate': 3,
         'HeapFree': 3, 'HeapReAlloc': 4, 'GetProcessHeap': 0,
         'EnterCriticalSection': 1, 'LeaveCriticalSection': 1,
         'InitializeCriticalSection': 1, 'DeleteCriticalSection': 1,
         'GetTickCount': 0, 'TlsAlloc': 0, 'TlsGetValue': 1, 'TlsSetValue': 2,
         'TlsFree': 1, 'GetCurrentThreadId': 0}


def load_pe():
    d = open(EXE, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    imgsz = struct.unpack_from('<I', d, pe + 24 + 56)[0]
    sh = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = sh + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('latin1')
        vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8)
        secs.append((nm, va, vs, ra, rs))
    return d, secs, imgsz, pe + 24


def parse_imports(d, secs, opt):
    def va2off(va):
        for nm, sva, vs, ra, rs in secs:
            if sva <= va < sva + max(vs, rs):
                return ra + (va - sva)
        return None
    imp_rva, _ = struct.unpack_from('<II', d, opt + 96 + 8)
    o = va2off(imp_rva)
    out = []
    k = 0
    while True:
        ilt, ts, fc, nm, iat = struct.unpack_from('<IIIII', d, o + k * 20)
        if (ilt, ts, fc, nm, iat) == (0, 0, 0, 0, 0):
            break
        no = va2off(nm)
        dll = d[no:d.index(b'\x00', no)].decode('latin1')
        j = 0
        while True:
            v = struct.unpack_from('<I', d, va2off(ilt) + j * 4)[0]
            if v == 0:
                break
            if v & 0x80000000:
                fn = '#%d' % (v & 0xFFFF)
            else:
                h = va2off(v) + 2
                fn = d[h:d.index(b'\x00', h)].decode('latin1')
            out.append((dll, fn, iat + j * 4))
            j += 1
        k += 1
    return out


class Engine:
    def __init__(self, song=1, verbose=False):
        self.d, self.secs, self.imgsz, self.opt = load_pe()
        self.imports = parse_imports(self.d, self.secs, self.opt)
        self.verbose = verbose
        self.song = song
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vtime = 1000
        self.log = []
        self.alloc_ptr = HEAP_BASE + 0x400000
        self.bp = set()
        self.hit = None
        self.tg_count = 0
        self.tone = None
        self.clock = None            # 若设置，日志时间戳用它（用于按 tick 精确驱动）
        self._map()
        self._stubs()
        self._hooks()
        # 文件数据
        f = open(AMUS, 'rb').read()
        self.amus = f
        self.uc.mem_map(FILEDATA_BASE, (len(f) + 0xFFF) & ~0xFFF, UC_PROT_ALL)
        self.uc.mem_write(FILEDATA_BASE, f)
        self.song_offsets = self._find_songs()

    def _find_songs(self):
        """AMUS.DAT 是 21 个独立 MUS 文件按 0x100 对齐拼接的，歌曲表就落在对齐边界上。"""
        out = []
        i = 0
        while i < len(self.amus) - 8:
            n = self.amus[i]
            if (i % 0x100 == 0 and n in (52, 68)
                    and i + n + 1 < len(self.amus) and self.amus[i + n + 1] == 0x0F):
                out.append(i)
                i += n
            else:
                i += 1
        return out

    def _map(self):
        u = self.uc
        size = (self.imgsz + 0xFFF) & ~0xFFF
        u.mem_map(IMAGE_BASE, size, UC_PROT_ALL)
        for nm, va, vs, ra, rs in self.secs:
            if rs:
                u.mem_write(IMAGE_BASE + va, self.d[ra:ra + rs])
        u.mem_map(HEAP_BASE, HEAP_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        u.mem_map(STUB_BASE, 0x1000, UC_PROT_ALL)
        u.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
        u.mem_map(RET_MAGIC & ~0xFFF, 0x1000, UC_PROT_ALL)
        u.mem_write(RET_MAGIC, b'\xC3')
        u.mem_map(TEB_BASE, 0x2000, UC_PROT_ALL)
        u.mem_write(TEB_BASE, struct.pack('<I', 0xFFFFFFFF))
        # FS base 在 unicorn 里不可设（默认 0），所以把 0 页映射出来当 TEB 用
        try:
            u.mem_map(0, 0x10000, UC_PROT_ALL)
        except UcError:
            pass
        u.mem_write(0, struct.pack('<I', 0xFFFFFFFF))
        u.mem_write(STUB_BASE, b'\xC3' * 0x1000)

    def _stubs(self):
        self.api_at = {}
        for i, (dll, fn, iat) in enumerate(self.imports):
            a = STUB_BASE + i * 4
            self.uc.mem_write(IMAGE_BASE + iat, struct.pack('<I', a))
            self.api_at[a] = fn

    def _hooks(self):
        u = self.uc
        u.hook_add(UC_HOOK_CODE, self._on_api, begin=STUB_BASE, end=STUB_BASE + 0xFFF)
        for a in (0x40CE11, 0x40D311, 0x40D2FF, 0x40D216, 0x4053E0, 0x405650, 0x405FC8):
            u.hook_add(UC_HOOK_CODE, self._on_bp, begin=a, end=a)
            self.bp.add(a)
        u.hook_add(UC_HOOK_CODE, self._on_ret, begin=RET_MAGIC, end=RET_MAGIC)

    # ---------- 分配器 ----------
    def _alloc(self, n):
        n = (n + 15) & ~15
        p = self.alloc_ptr
        self.alloc_ptr += n
        if self.alloc_ptr > HEAP_BASE + HEAP_SIZE:
            raise RuntimeError('heap exhaust')
        return p

    # ---------- hooks ----------
    def _ret(self, uc, nargs, eax):
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack('<I', uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + nargs * 4)
        uc.reg_write(UC_X86_REG_EAX, eax & 0xFFFFFFFF)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def _on_api(self, uc, address, size, ctx):
        fn = self.api_at.get(address)
        esp = uc.reg_read(UC_X86_REG_ESP)
        n = NARGS.get(fn, 0)
        args = [struct.unpack('<I', uc.mem_read(esp + 4 + i * 4, 4))[0] for i in range(n)]
        eax = 0
        if fn == 'timeGetTime':
            self.tg_count += 1
            eax = (self.vtime + self.tg_count) & 0xFFFFFFFF
        elif fn == 'midiOutShortMsg':
            self.log.append((self.clock() if self.clock else self.vtime, 'msg', args[1]))
        elif fn == 'midiOutOpen':
            ptr = args[0]
            uc.mem_write(ptr, struct.pack('<I', 0x1234))
            eax = 0
        elif fn in ('Sleep',):
            pass
        elif fn in ('VirtualAlloc', 'HeapAlloc'):
            eax = self._alloc(args[2] if fn == 'VirtualAlloc' else args[2])
        elif fn in ('HeapCreate', 'GetProcessHeap'):
            eax = 0x1000
        elif fn in ('VirtualFree', 'HeapFree', 'HeapReAlloc'):
            eax = 1
        elif fn == 'CreateThread':
            eax = 0
        else:
            eax = 0
        self._ret(uc, n, eax)

    def _on_bp(self, uc, address, size, ctx):
        self._handle(address, uc)

    def _on_ret(self, uc, address, size, ctx):
        uc.emu_stop()

    def _handle(self, address, uc):
        esp = uc.reg_read(UC_X86_REG_ESP)
        if address == 0x405FC8:
            # 等 MIDI 回调标志的忙等循环：把被轮询的字节置 1，放行
            uc.mem_write(esp + 0x30, b'\x01')
            return
        if address == 0x40CE11:            # operator new(n)
            n = struct.unpack('<I', uc.mem_read(esp + 4, 4))[0]
            p = self._alloc(max(n, 4))
            uc.mem_write(p, b'\x00' * 16)
            self._ret(uc, 0, p)
            return
        if address == 0x40D311:            # calloc(n, size)
            a, b = struct.unpack('<II', uc.mem_read(esp + 4, 8))
            p = self._alloc(max(a * b, 4))
            uc.mem_write(p, b'\x00' * (a * b if a * b <= 4096 else 16))
            self._ret(uc, 0, p)
            return
        if address == 0x40D2FF:            # malloc(size)
            n = struct.unpack('<I', uc.mem_read(esp + 4, 4))[0]
            p = self._alloc(max(n, 4))
            self._ret(uc, 0, p)
            return
        if address == 0x40D216:            # free(p)
            self._ret(uc, 0, 0)
            return
        if address == 0x40D439:            # CreateThread wrapper
            self._ret(uc, 3, 0)
            return
        if address in (0x4053E0, 0x405650):
            nargs = 3 if address == 0x4053E0 else 4
            if address == 0x405650:
                args = [struct.unpack('<I', uc.mem_read(esp + 4 * i, 4))[0]
                        for i in (1, 2, 3, 4)]
                self.load_args = getattr(self, 'load_args', [])
                self.load_args.append(args)
                if self.verbose:
                    print('   0x405650 args: ' + ' '.join('%08X' % x for x in args))
            path = struct.unpack('<I', uc.mem_read(esp + 4, 4))[0]
            name = b''
            try:
                name = uc.mem_read(path, 32).split(b'\x00')[0]
            except UcError:
                pass
            if self.verbose:
                print('   load(%r) via 0x%X' % (name, address))
            if name.endswith(b'MDA') or name.endswith(b'MSE'):
                self._ret(uc, nargs, 0)
                return
            if address == 0x405650:
                # 音色库：把我们抽出来的 MDA 资源原样交回去，让引擎自己解析
                if self.tone is not None:
                    p = self._alloc(len(self.tone) + 16)
                    uc.mem_write(p, self.tone)
                    uc.mem_write(p + len(self.tone), b'\x00' * 16)
                    self._ret(uc, nargs, p)
                    return
                p = self._alloc(0x4000)
                uc.mem_write(p, b'\x00' * 0x4000)
                uc.mem_write(p + 7, b'\x40')
                self._ret(uc, nargs, p)
                return
            off = self.song_offsets[self.song - 1] if self.song - 1 < len(self.song_offsets) else 0
            self._ret(uc, nargs, FILEDATA_BASE + off)
            return
        uc.emu_stop()

    # ---------- 调用 ----------
    def call(self, fn, ecx=None, args=(), timeout=20 * 1000 * 1000, stop=None):
        u = self.uc
        esp = STACK_BASE + STACK_SIZE - 0x1000
        u.reg_write(UC_X86_REG_ESP, esp)
        for a in reversed(args):
            esp -= 4
            u.mem_write(esp, struct.pack('<I', a))
        esp -= 4
        u.mem_write(esp, struct.pack('<I', RET_MAGIC))
        u.reg_write(UC_X86_REG_ESP, esp)
        if ecx is not None:
            u.reg_write(UC_X86_REG_ECX, ecx)
        self.stop_set = set(stop or ())
        try:
            u.emu_start(fn, 0xFFFFFFFF, timeout=timeout)
        except UcError as e:
            return 'ERR %s eip=0x%X' % (e, u.reg_read(UC_X86_REG_EIP))
        return 'ok'

    def memb(self, addr, n):
        return bytes(self.uc.mem_read(addr, n))


def main():
    song = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    eng = Engine(song=song, verbose=True)
    print('songs found:', len(eng.song_offsets), [hex(x) for x in eng.song_offsets][:6])
    scratch = HEAP_BASE + 0x380000
    eng.uc.mem_write(scratch, b'\x00' * 0x100)
    print('== ctor', eng.call(0x405830, ecx=HEAP_BASE, args=(scratch,)))
    print('   AMUS.DAT slot:', eng.memb(HEAP_BASE + 0x142e90, 12))
    print('== parse', eng.call(0x406AC0, ecx=HEAP_BASE, args=(song,)))
    for i in range(9):
        off = struct.unpack('<I', eng.memb(HEAP_BASE + 0x40030 + i * 0x20004, 4))[0]
        base = HEAP_BASE + 0x20030 + i * 0x20004
        print('ch%d readoff=0x%X  head=%s' % (i, off, eng.memb(base, 24).hex(' ')))
    print('== init tone', eng.call(0x407090, ecx=HEAP_BASE, args=(song,)))
    print('== init chip', eng.call(0x405E40, ecx=HEAP_BASE))
    for nm, off in (('tempotgt', 0x142ca8), ('tempobase', 0x142cac), ('acc', 0x142e88)):
        v = eng.memb(HEAP_BASE + off, 4)
        print('   %s = %s' % (nm, v.hex(' ')))
    # 时钟基准：让引擎认为"上次 tick 就是现在"，避免第一帧吃掉一大段时间
    eng.uc.mem_write(HEAP_BASE + 0x142e8c, struct.pack('<I', eng.vtime))
    eng.uc.mem_write(HEAP_BASE + 0x142e88, struct.pack('<f', 0.0))
    ntick = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    for k in range(ntick):
        eng.vtime += step
        r = eng.call(0x406250, ecx=HEAP_BASE)
        if r != 'ok':
            print('tick', k, r)
            break
    print('midi msgs', len(eng.log), 'end vtime', eng.vtime)
    for t, kind, v in eng.log[:12]:
        print('  %6d  %s %06X' % (t, kind, v))
    print('  ...')
    for t, kind, v in eng.log[-6:]:
        print('  %6d  %s %06X' % (t, kind, v))


if __name__ == '__main__':
    main()
