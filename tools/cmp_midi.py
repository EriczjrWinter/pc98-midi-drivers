# -*- coding: utf-8 -*-
import collections
import sys

import mido


def load(path):
    m = mido.MidiFile(path)
    notes = []
    progs = collections.defaultdict(list)
    for ti, tr in enumerate(m.tracks):
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append((t, msg.channel, msg.note, msg.velocity))
            elif msg.type == 'program_change':
                progs[msg.channel].append((t, msg.program))
    return m, notes, progs


def main():
    a, b = sys.argv[1], sys.argv[2]
    ma, na, pa = load(a)
    mb, nb, pb = load(b)
    print('参考: %s' % a)
    print('   %.1f 秒  %d 音符  %d 轨  TPQ=%d' % (ma.length, len(na), len(ma.tracks), ma.ticks_per_beat))
    print('我们: %s' % b)
    print('   %.1f 秒  %d 音符  %d 轨  TPQ=%d' % (mb.length, len(nb), len(mb.tracks), mb.ticks_per_beat))
    print()
    ca = collections.Counter(c for _, c, _, _ in na)
    cb = collections.Counter(c for _, c, _, _ in nb)
    print('%-6s %8s %8s' % ('通道', '参考', '我们'))
    for c in sorted(set(ca) | set(cb)):
        print('%-6d %8d %8d' % (c, ca.get(c, 0), cb.get(c, 0)))
    print()
    print('参考音高范围: %d..%d' % (min(n for _, _, n, _ in na), max(n for _, _, n, _ in na)))
    print('我们音高范围: %d..%d' % (min(n for _, _, n, _ in nb), max(n for _, _, n, _ in nb)))
    print()
    na.sort()
    nb.sort()
    print('参考前 12 音:', [(c, n) for _, c, n, _ in na[:12]])
    print('我们前 12 音:', [(c, n) for _, c, n, _ in nb[:12]])
    print()
    print('参考音色:', {c: sorted(set(p for _, p in v)) for c, v in sorted(pa.items())})
    print('我们音色:', {c: sorted(set(p for _, p in v)) for c, v in sorted(pb.items())})


if __name__ == '__main__':
    main()
