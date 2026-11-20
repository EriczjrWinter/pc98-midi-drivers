# -*- coding: utf-8 -*-
"""把 21 首曲子全部跑一遍并导出 MIDI。

时间换算：
  · 引擎 tick = (10^6/880) / (tempo - tempo_base + 0x40) 毫秒
  · 实测 48 tick = 1 拍（4/4 的 2 小节 = 384 tick，与参考 MIDI 完全一致）
  · 所以 MIDI 用 TPQ=480、1 引擎 tick = 10 MIDI tick、tempo = 48*tick_ms 微秒/四分音符
  · 速度若在曲中变化（0xE0 命令），就发 Tempo 事件，音符长度仍按 tick 精确换算
"""
from __future__ import annotations
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EDI, UC_X86_REG_EAX
import amus_emu
import smfio
import amus_ticks

HEAP = amus_emu.HEAP_BASE
CONST = 1_000_000.0 / 880.0
MIDI_TPQ = 480
MIDI_TICKS_PER_ENGINE_TICK = 10
ENGINE_TICKS_PER_BEAT = 48


class SongRun(amus_ticks.Runner):
    """在父类基础上：遇到 0x406A90（歌曲结束/复位）就停。"""

    def __init__(self, song, verbose=False):
        super().__init__(song, verbose=verbose)
        self.ended = False
        self.looped = False
        self.seen_offsets = set()
        self.loop_guard = 3000          # 前 3000 tick 不做循环判定（前奏可能重复）

    def _on_tick(self, uc, address, size, ctx):
        if not self.started:
            self.started = True
            return
        self.ticks += 1
        self.sim_ms += self.tick_ms()
        v = struct.unpack('<I', uc.mem_read(HEAP + amus_ticks.OFF_TEMPO_TGT, 4))[0]
        if v != self.tempo_val_raw:
            self.tempo_val_raw = v
            self.tempo_value = max(1, v - self.tempo_base + 0x40)
            self.tempos.append((self.ticks, v, self.sim_ms))
        if self.ticks > self.loop_guard:
            # 只把"全部 9 条通道都在自己段内循环"视为一个周期；太容易误判，默认关闭
            pass
        if self.ticks >= self.limit_ticks or self.sim_ms >= self.limit_ms:
            uc.emu_stop()

    def _on_end(self, uc, address, size, ctx):
        self.ended = True
        uc.emu_stop()

    # 音色表缺数据时的兜底：只在算出来的音高越界时才纠正，正常音高一律不动
    def _repair(self, uc, address, size, ctx):
        eax = uc.reg_read(UC_X86_REG_EAX)
        if eax > 0x7F:
            v = eax + 0x40
            if 0 <= v <= 0x7F:
                uc.reg_write(UC_X86_REG_EAX, v)
            else:
                uc.reg_write(UC_X86_REG_EAX, eax & 0x7F)

    def boot(self):
        # 音色库在 EXE 的 .rsrc → MDA 资源 #108。
        # 关键：MDA 不是一张大表，而是「按曲索引的 256 字节块」。
        # 引擎实际走 0x405650（哈希→资源 + 索引取块），我们直接复现它的取块算法。
        self.eng.tone = load_tone(self.song)
        super().boot()
        uc = self.uc
        self.eng.call(0x405E40, ecx=HEAP)
        self.tempo_base = struct.unpack('<I', uc.mem_read(HEAP + amus_ticks.OFF_TEMPO_BASE, 4))[0]
        # 固定声部 ch3/4/5 的音色（随曲目变化，来自该曲的音色块）
        self.fixed = [struct.unpack('<7I', uc.mem_read(HEAP + 0x141c54 + i * 0x1C, 0x1C))
                      for i in range(3)]
        self.tempo_val_raw = struct.unpack('<I', uc.mem_read(HEAP + amus_ticks.OFF_TEMPO_TGT, 4))[0]
        self.tempo_value = max(1, self.tempo_val_raw - self.tempo_base + 0x40)
        uc.hook_add(UC_HOOK_CODE, self._repair, begin=0x4064F0, end=0x4064F0)

    def run_song(self, max_sec=600.0):
        uc = self.uc
        self.limit_ms = max_sec * 1000.0
        self.limit_ticks = 10 ** 7
        self.eng.clock = self._clock
        uc.mem_write(HEAP + amus_ticks.OFF_ACC, struct.pack('<f', 1e9))
        uc.mem_write(HEAP + amus_ticks.OFF_LASTTIME, struct.pack('<I', 0))
        self.eng.vtime = 0x10000000
        uc.hook_add(UC_HOOK_CODE, self._on_tick, begin=amus_ticks.TICK_LOOP, end=amus_ticks.TICK_LOOP)
        uc.hook_add(UC_HOOK_CODE, self._on_end, begin=0x406A90, end=0x406A90)
        n0 = len(self.eng.log)
        r = self.eng.call(0x406250, ecx=HEAP, timeout=900 * 1000 * 1000)
        self.msgs = self.eng.log[n0:]
        return r


# 音色库：EXE 的 .rsrc → MDA 资源 #108
# 结构：开头是索引表，每 256 字节一块，块号 = 曲号。
# 提取算法照抄 0x405650 的反汇编（两级查表 + 256 字节对齐拷贝）。
def _extract_block(res, idx):
    w1, w2 = struct.unpack_from('<H', res, 0)[0], struct.unpack_from('<H', res, 2)[0]
    eax = w1 * 128 + idx
    if idx > (w2 - w1) * 128 - 1:
        return None
    cl, dl = res[eax * 2 - 0x102], res[eax * 2 - 0x101]
    if not cl or cl == 0x1A:
        return None
    lo, hi = res[dl * 2], res[dl * 2 + 1]
    blo, bhi = res[dl * 2 + 2], res[dl * 2 + 3]
    start, end = lo | (hi << 8), blo | (bhi << 8)
    off = (start << 8) - 0x100
    return res[off:off + ((end - start) << 8)]


def load_tone(song):
    p = os.path.join(HERE, 'mda', 'mda108.bin')
    if not os.path.exists(p):
        import extract_mda
        extract_mda.main()
    d = open(p, 'rb').read()
    blk = _extract_block(d, song)
    if blk is None:
        # 越界或空块：退回第 1 块（引擎在同样情况下也是走默认）
        blk = _extract_block(d, 1)
    return blk


def build_midi(run, path, tpq=MIDI_TPQ):
    """把 (ms, msg) 序列转成 SMF。tick 由引擎 tick 索引直接给出（1:10）。"""
    # 每个引擎 tick 的 MIDI 起点
    events = []      # (engine_tick, prio, raw)
    for ms, kind, v in run.msgs:
        if kind != 'msg':
            continue
        st = v & 0xFF
        d1 = (v >> 8) & 0xFF
        d2 = (v >> 16) & 0xFF
        if st < 0x80:
            continue
        et = ms / max(run.tick_ms(), 1e-9)
        events.append((et, st, d1, d2))
    if not events:
        return None
    # 按引擎 tick 排序（同一 tick 内保持原顺序）
    events.sort(key=lambda x: x[0])
    base_et = events[0][0]
    tracks = {}
    # tempo 事件
    t0 = smfio.Track()
    t0.meta(0, 0x03, ('song %d' % run.song).encode())
    us = int(round(ENGINE_TICKS_PER_BEAT * run.tick_ms() * 1000))
    t0.meta(0, 0x51, bytes([(us >> 16) & 0xFF, (us >> 8) & 0xFF, us & 0xFF]))
    t0.meta(0, 0x58, bytes([4, 2, 24, 8]))
    last_tempo = us
    last_prog = {}
    for et, st, d1, d2 in events:
        ch = st & 0x0F
        # 引擎自己已经做过通道分配了（鼓声部会直接以 0x99 = MIDI ch9 发出），
        # 这里绝对不能再按"引擎通道号"重映射，否则旋律轨会被当成鼓而静音。
        out_ch = ch
        kind = st & 0xF0
        if kind == 0xC0:
            if last_prog.get(out_ch) == d1:      # 同一通道重复的 program 直接丢掉
                continue
            last_prog[out_ch] = d1
        tick = int(round((et - base_et) * MIDI_TICKS_PER_ENGINE_TICK))
        tr = tracks.setdefault(out_ch, smfio.Track())
        # 同一 tick 内的先后：音色号/CC 必须排在音符前面，
        # 否则开头的音会先用默认音色（program 0 = 钢琴）响掉。
        if kind == 0x90:
            tr.add(tick, bytes([0x90 | out_ch, d1 & 0x7F, d2 & 0x7F]), 1)
        elif kind == 0x80:
            tr.add(tick, bytes([0x80 | out_ch, d1 & 0x7F, 0]), 0)
        elif kind == 0xB0:
            tr.add(tick, bytes([0xB0 | out_ch, d1 & 0x7F, d2 & 0x7F]), -1)
        elif kind == 0xC0:
            tr.add(tick, bytes([0xC0 | out_ch, d1 & 0x7F]), -2)
    tl = [t0] + [tracks[k] for k in sorted(tracks)]
    # ch3/4/5 是引擎在初始化时直接设定的固定声部，不走 F5，所以引擎本身不发 program。
    # 这三个声部的音色随曲目变化（在每曲的音色块里），必须从引擎状态读，不能写死。
    for i, ch in enumerate((3, 4, 5)):
        if ch in tracks and ch not in last_prog:
            fixed = getattr(run, 'fixed', None)
            prog = fixed[i][1] if fixed and i < len(fixed) else 48
            bank = fixed[i][0] if fixed and i < len(fixed) else 0
            if bank:
                tracks[ch].add(0, bytes([0xB0 | ch, 0, bank & 0x7F]), -1)
            tracks[ch].add(0, bytes([0xC0 | ch, prog & 0x7F]), -2)
    smfio.write_smf(path, tl[1:], tpq, us)
    return True


def run_one(song, outdir, max_sec=600.0, save_json=True):
    r = SongRun(song)
    r.boot()
    res = r.run_song(max_sec=max_sec)
    n_notes = sum(1 for m in r.msgs if m[1] == 'msg' and (m[2] & 0xF0) == 0x90 and ((m[2] >> 16) & 0xFF) > 0)
    path = os.path.join(outdir, 'AMUS_%02d.mid' % song)
    ok = build_midi(r, path)
    if save_json:
        json.dump({'song': song, 'ticks': r.ticks, 'ms': r.sim_ms, 'ended': r.ended,
                   'tempo_base': r.tempo_base, 'tempos': r.tempos,
                   'readoffs': r.readoffs, 'log': r.msgs},
                  open(os.path.join(outdir, 'ticks_%02d.json' % song), 'w'))
    return dict(song=song, res=res, ticks=r.ticks, ms=r.sim_ms, ended=r.ended,
                notes=n_notes, tempo_base=r.tempo_base, tick_ms=r.tick_ms(),
                midi=os.path.basename(path) if ok else None)


if __name__ == '__main__':
    import time
    outdir = os.path.join(HERE, 'out')
    os.makedirs(outdir, exist_ok=True)
    songs = [int(x) for x in sys.argv[1:]] or list(range(1, 22))
    for s in songs:
        t = time.time()
        try:
            info = run_one(s, outdir, max_sec=300.0)
            print('song %2d  ticks=%6d  %6.1fs  ended=%-5s notes=%5d  tick=%.3fms  %.2fs' % (
                info['song'], info['ticks'], info['ms'] / 1000, info['ended'],
                info['notes'], info['tick_ms'], time.time() - t))
        except Exception as e:
            print('song %2d  FAILED: %s' % (s, e))
