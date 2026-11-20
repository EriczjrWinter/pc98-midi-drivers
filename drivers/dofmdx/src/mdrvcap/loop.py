# -*- coding: utf-8 -*-
"""没有参考 MIDI 时，用自相似估一首曲子的循环长度。

用法：
    python -m mdrvcap.loop <pack> <file>     # 打印估算的循环长度
    from mdrvcap.loop import note_seq, estimate_ticks
"""
import sys

from . import capture, smf
from .export import TICK_MS


def note_seq(pack, name, ticks=45000):
    """抓一段，返回去掉重复音的 (tick, note) 序列。"""
    sim, _ = capture.capture(capture.load_track(pack, name), ticks=ticks)
    msgs = smf.parse(sim.midi)
    out = []
    for t, m in msgs:
        if 0x90 <= m[0] < 0xA0 and len(m) > 2 and m[2] > 0 and m[1] > 0:
            if out and out[-1] == (t, m[1]):
                continue
            out.append((t, m[1]))
    return out


def estimate_ticks(seq, k=300):
    """取 300 音窗口重复跨度的中位数，换算成一次循环的 tick 数。

    注意：段落重复也会命中，所以这是「一个循环」的近似，不是精确曲长。
    """
    if len(seq) < k * 2:
        return None
    p = bytes(x[1] for x in seq)
    spans = []
    for a in range(0, len(p) - k, 40):
        j = p.find(p[a:a + k], a + k // 2)
        if j > a:
            spans.append((seq[j][0] - seq[a][0], a, j))
    if not spans:
        return None
    spans.sort()
    L = spans[len(spans) // 2][0]
    for span, _a, j in sorted(spans, key=lambda x: x[1]):
        if abs(span - L) <= 80:
            return seq[j][0] + 2
    return None


if __name__ == '__main__':
    pack = sys.argv[1] if len(sys.argv) > 1 else 'zatuon_98'
    name = sys.argv[2] if len(sys.argv) > 2 else 'ZR02G.FMD'
    seq = note_seq(pack, name)
    t = estimate_ticks(seq)
    print('%s/%s notes=%d loop=%s (%.1f s)'
          % (pack, name, len(seq), t, (t or 0) * TICK_MS / 1000.0))
