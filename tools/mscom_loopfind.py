# -*- coding: utf-8 -*-
"""从驱动吐出的字节流里找出真实的循环周期。

驱动播放循环曲目时，输出会严格周期性重复：
    data[L:] 以 P 为周期
于是「一遍」就是 data[:L+P]。
"""
import glob
import os
import sys

HERE = r'D:\gf\pc98-midi-drivers\drivers\mscom\src'
sys.path.insert(0, HERE)
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')
import mscom_emu as E
import smf_build


def find_loop(stream, probe=20000, min_period=2000):
    """返回 (L, P)：L 是循环起点（字节下标），P 是周期。找不到返回 None。"""
    data = bytes(x for _, x in stream)
    n = len(data)
    if n < probe * 2 + min_period:
        return None
    tail = n - probe
    head = data[tail:tail + 64]
    # 找 tail 处这段在文件里出现过的位置
    pos = data.find(head, 0)
    cands = []
    while 0 <= pos < tail:
        P = tail - pos
        if P >= min_period and data[tail:] == data[tail - P:tail - P + probe]:
            cands.append((pos, P))
        pos = data.find(head, pos + 1)
    if not cands:
        return None
    # 取最小的周期（最紧凑的循环）
    pos, P = min(cands, key=lambda x: x[1])
    L = tail
    while L > 0 and data[L - 1] == data[L - 1 + P]:
        L -= 1
    return L, P


def analyse(path):
    data = open(path, 'rb').read()
    m = E.MSCom(driver=os.path.join(HERE, 'ms.com'))
    stream = m.export(data, max_ticks=45000, silence_ticks=10 ** 9)
    period = E.scan_timer_writes(m.timer_writes, m.tick)
    acc = [0.0] * (m.tick + 2)
    for i in range(1, m.tick + 2):
        acc[i] = acc[i - 1] + period[i - 1]
    ms = [(acc[t], b) for t, b in stream]
    full = ms[-1][0] / 1000.0 if ms else 0
    r = find_loop(stream)
    if r:
        L, P = r
        cut = ms[:L + P]
        one = cut[-1][0] / 1000.0 if cut else 0
        return full, one, P, True
    return full, full, 0, False


if __name__ == '__main__':
    for pat in ('data/dr2/*.MID', 'data/filsnown/*.MD'):
        for f in sorted(glob.glob(os.path.join(HERE, pat))):
            full, one, P, ok = analyse(f)
            print('%-14s 全长 %6.1f 秒  一遍 %6.1f 秒  周期 %6d 字节 %s'
                  % (os.path.basename(f), full, one, P, '' if ok else '(未检出循环)'))
