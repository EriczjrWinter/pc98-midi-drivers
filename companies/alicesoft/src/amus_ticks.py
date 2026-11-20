# -*- coding: utf-8 -*-
"""一次 emu_start 跑完整首歌：在 tick 边界（0x406294）挂钩，自己推进虚拟时间。

引擎 0x406250 的结构：
    0x406294  循环头：检查 9 个通道就绪标志
    0x4062F2  检查累积器 acc > 0 ？
    0x406309..0x406996  对 9 个通道各推进一个 tick
    0x40699C  jmp 0x406294
所以 0x406294 每次命中就代表"一个 tick 开始"。
把 acc 先设成一个很大的值，循环就永不因时间耗尽而退出；
由钩子在跑了 N 个 tick 后 emu_stop，同时按当前速度累积精确毫秒。
"""
from __future__ import annotations
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP
import amus_emu

HEAP = amus_emu.HEAP_BASE
OFF_TEMPO_TGT = 0x142ca8
OFF_TEMPO_BASE = 0x142cac
OFF_ACC = 0x142e88
OFF_LASTTIME = 0x142e8c
CONST = 1_000_000.0 / 880.0
TICK_LOOP = 0x406294


class Runner:
    def __init__(self, song, verbose=False):
        self.eng = amus_emu.Engine(song=song, verbose=verbose)
        self.uc = self.eng.uc
        self.song = song
        self.msgs = []
        self.sim_ms = 0.0
        self.ticks = 0
        self.tempos = []
        self.limit_ticks = 0
        self.limit_ms = 0.0
        self.started = False

    # ---------- 时间 ----------
    def tick_ms(self):
        return CONST / max(1, self.tempo_value)

    def _clock(self):
        return self.sim_ms

    def _on_tick(self, uc, address, size, ctx):
        if not self.started:
            self.started = True
            return
        self.ticks += 1
        self.sim_ms += self.tick_ms()
        # 读速度（可能被 E0/E1 改变）
        v = struct.unpack('<I', uc.mem_read(HEAP + OFF_TEMPO_TGT, 4))[0]
        if v != self.tempo_val_raw:
            self.tempo_val_raw = v
            self.tempo_value = max(1, v - self.tempo_base + 0x40)
            self.tempos.append((self.ticks, v, self.sim_ms))
        if self.ticks >= self.limit_ticks or self.sim_ms >= self.limit_ms:
            uc.emu_stop()

    def boot(self):
        eng, uc = self.eng, self.uc
        scratch = HEAP + 0x380000
        uc.mem_write(scratch, b'\x00' * 0x100)
        eng.call(0x405830, ecx=HEAP, args=(scratch,))
        eng.call(0x406AC0, ecx=HEAP, args=(self.song,))
        eng.call(0x407090, ecx=HEAP, args=(self.song,))
        eng.call(0x405E40, ecx=HEAP)
        self.tempo_base = struct.unpack('<I', uc.mem_read(HEAP + OFF_TEMPO_BASE, 4))[0]
        self.tempo_val_raw = struct.unpack('<I', uc.mem_read(HEAP + OFF_TEMPO_TGT, 4))[0]
        self.tempo_value = max(1, self.tempo_val_raw - self.tempo_base + 0x40)
        self.tempos = [(0, self.tempo_val_raw, 0.0)]
        # 缓存解析后的 9 条内部字节流（调试/校验用）
        self.streams = [bytes(uc.mem_read(HEAP + 0x20030 + i * 0x20004, 0x4000)) for i in range(9)]
        self.readoffs = [struct.unpack('<I', uc.mem_read(HEAP + 0x40030 + i * 0x20004, 4))[0]
                         for i in range(9)]

    def run(self, max_sec=400.0, max_ticks=400000):
        eng, uc = self.eng, self.uc
        self.limit_ms = max_sec * 1000.0
        self.limit_ticks = max_ticks
        eng.clock = self._clock
        # acc 设成一个巨大的值，让 tick 循环不会因为时间用尽而退出
        uc.mem_write(HEAP + OFF_ACC, struct.pack('<f', 1e9))
        uc.mem_write(HEAP + OFF_LASTTIME, struct.pack('<I', 0))
        eng.vtime = 0x10000000
        uc.hook_add(UC_HOOK_CODE, self._on_tick, begin=TICK_LOOP, end=TICK_LOOP)
        n0 = len(eng.log)
        r = eng.call(0x406250, ecx=HEAP, timeout=600 * 1000 * 1000)
        self.msgs = eng.log[n0:]
        return r


def main():
    import time
    song = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    t0 = time.time()
    r = Runner(song)
    r.boot()
    res = r.run(max_sec=secs)
    dt = time.time() - t0
    print('song %d: %s  ticks=%d  %.2fs  real %.1fs  msgs=%d  tempo_base=%d tempo=%d tick=%.4fms' % (
        song, res, r.ticks, r.sim_ms / 1000.0, dt, len(r.msgs),
        r.tempo_base, r.tempo_val_raw, r.tick_ms()))
    print('tempo changes:', r.tempos[:8])
    json.dump({'song': song, 'ticks': r.ticks, 'ms': r.sim_ms,
               'tempo_base': r.tempo_base, 'tempos': r.tempos,
               'readoffs': r.readoffs, 'log': r.msgs},
              open(os.path.join(HERE, 'ticks_%02d.json' % song), 'w'))


if __name__ == '__main__':
    main()
