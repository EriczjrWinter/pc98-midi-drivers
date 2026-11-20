# -*- coding: utf-8 -*-
"""按 VGMRips 记录的长度截断导出结果。

VGMRips 的 data-duration 是 VGM 实际播放长度（含循环），
和 CD 专辑的长度不一定相同——专辑那边有自己的剪辑。
这里统一以 VGM 长度为准，至少是个客观标准。
"""
import glob
import os
import sys

sys.path.insert(0, r'D:\gf\pc98-midi-drivers\drivers\mscom\src')
sys.path.insert(0, r'D:\gf\pc98-midi-drivers\companies\leaf\src')
import mscom_emu as E
import smf_build

HERE = r'D:\gf\pc98-midi-drivers\drivers\mscom\src'
DATA = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, 'out')

# VGMRips 的 data-duration（秒）
JANKI = {
    1: 5.798, 2: 69.673, 3: 199.591, 4: 151.818, 5: 135.912,
    6: 337.372, 7: 341.941, 8: 361.763, 9: 214.146, 10: 134.287,
    11: 304.525, 12: 208.350, 13: 326.524, 14: 295.386,
    15: 8.751, 16: 2.796, 17: 2.242, 18: 2.835,
}
FILSNOWN = {
    1: 5.621, 2: 145.379, 3: 104.649, 4: 135.666, 5: 166.660,
    6: 160.045, 7: 77.284, 8: 139.896, 9: 103.924, 10: 110.218,
    11: 122.798, 12: 149.213, 13: 91.585, 14: 147.382, 15: 125.399,
    16: 157.879, 17: 222.751, 18: 77.548, 19: 111.788, 20: 163.085,
    21: 179.413, 22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0,
    26: 0.0, 27: 101.559, 28: 66.619, 29: 111.783, 30: 108.645,
    31: 149.538, 32: 146.006, 33: 167.764, 34: 180.074, 35: 247.906,
    36: 200.867, 37: 275.798, 38: 6.217, 39: 6.096, 40: 6.133,
    41: 3.753, 42: 2.914, 43: 2.270,
}


def trim(ms, target_s):
    """把 (毫秒, 字节) 流截到 target_s。"""
    if not target_s:
        return ms
    lim = target_s * 1000.0
    return [x for x in ms if x[0] <= lim]


def run(path, out_path, target_s):
    data = open(path, 'rb').read()
    m = E.MSCom(driver=os.path.join(HERE, 'ms.com'))
    stream = m.export(data, max_ticks=45000, silence_ticks=10 ** 9)
    period = E.scan_timer_writes(m.timer_writes, m.tick)
    acc = [0.0] * (m.tick + 2)
    for i in range(1, m.tick + 2):
        acc[i] = acc[i - 1] + period[i - 1]
    ms = [(acc[t], b) for t, b in stream]
    before = ms[-1][0] / 1000.0 if ms else 0
    ms = trim(ms, target_s)
    smf, tempo, p = smf_build.build_ms(ms)
    open(out_path, 'wb').write(smf)
    after = ms[-1][0] / 1000.0 if ms else 0
    print('%-14s %6.1f → %6.1f 秒（目标 %5.1f）' %
          (os.path.basename(path), before, after, target_s or 0))


def main():
    os.makedirs(OUT, exist_ok=True)
    for sub, pat, table in (('dr2', '*.MID', JANKI),
                            ('filsnown', '*.MD', FILSNOWN)):
        files = sorted(glob.glob(os.path.join(DATA, sub, pat)))
        for i, f in enumerate(files, 1):
            try:
                run(f, os.path.join(OUT, '%s_%s.mid' % (sub, os.path.splitext(os.path.basename(f))[0])),
                    table.get(i))
            except Exception as e:
                print('%-14s 失败 %s' % (os.path.basename(f), e))


if __name__ == '__main__':
    main()
