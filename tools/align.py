# -*- coding: utf-8 -*-
"""全曲对齐：把参考和我们各自换算成真实秒，做容差匹配，算召回/多余。"""
import collections
import sys

from timer import note_seconds


def key(notes, tol):
    """把音符按 (通道, 音高, 时间/容差) 归桶，用于容差匹配。"""
    d = collections.defaultdict(list)
    for t, c, v in notes:
        d[(c, v)].append(t)
    for k in d:
        d[k].sort()
    return d


def match(ref, our, tol=0.06):
    r = key(ref, tol)
    o = key(our, tol)
    hit = 0
    missing = []
    for k, ts in r.items():
        cand = list(o.get(k, []))
        for t in ts:
            j = None
            for i, v in enumerate(cand):
                if abs(v - t) <= tol:
                    j = i
                    break
            if j is None:
                missing.append((t, k[0], k[1]))
            else:
                hit += 1
                cand.pop(j)
    total_ref = len(ref)
    total_our = len(our)
    extra = total_our - hit
    return hit, total_ref, total_our, extra, missing


if __name__ == '__main__':
    a, b = sys.argv[1], sys.argv[2]
    tmax = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
    ref = [x for x in note_seconds(a) if x[0] < tmax]
    our = [x for x in note_seconds(b) if x[0] < tmax]
    hit, tr, to, extra, missing = match(ref, our)
    print('参考 %d 音，我们 %d 音' % (tr, to))
    print('匹配上 %d 音（容差 60ms）→ 召回 %.2f%%' % (hit, 100.0 * hit / tr))
    print('我们多出 %d 音（%.2f%%）' % (extra, 100.0 * extra / to))
    print('参考中被漏掉 %d 音' % len(missing))
    if missing:
        print('  漏掉的前 10 个:', [(round(t, 2), c, v) for t, c, v in missing[:10]])
