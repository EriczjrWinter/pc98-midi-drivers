# -*- coding: utf-8 -*-
"""统计 .MMD 的「特征」——用来区分不同构建 / 不同游戏用了哪些能力。

不做循环展开，只走一遍命令流，所以再离谱的数据也不会炸。

用法：
  python mmd_features.py <目录或zip> [更多...]
  python mmd_features.py --dir D:\\path\\to\\mmd
  python mmd_features.py --zip pack.zip
"""
import collections
import glob
import io
import os
import struct
import sys
import zipfile

KNOWN_NOTE = '音符'
MASK = 0x80


def walk(data):
    """返回 (统计字典, 警告列表)。不展开循环。"""
    st = {
        'bpm': data[0],
        'transpose': struct.unpack('b', data[1:2])[0],
        'tracks': 0,
        'notes': 0,
        'cmds': collections.Counter(),
        'unknown': collections.Counter(),
        'loop_start': 0,
        'loop_end': 0,
        'loop_counts': collections.Counter(),
        'max_depth': 0,
        'unbalanced': 0,
        'tempo_cmds': 0,
        'tempo_ramp': 0,
        'msg_kinds': collections.Counter(),
    }
    n = len(data)
    warns = []
    for i in range(16):
        off, key, ch = struct.unpack_from('<HBB', data, 2 + 4 * i)
        if ch >= 16:
            continue
        st['tracks'] += 1
        pos = off
        buf = [0, 0, 0, 0]
        depth = 0
        steps = 0
        while 0 <= pos < n and steps < 200000:
            steps += 1
            cmd = data[pos]; pos += 1
            if (cmd & 0xF0) == MASK:
                if cmd & 0x08:
                    buf[0] = data[pos] if pos < n else 0; pos += 1
                if cmd & 0x04:
                    buf[1] = data[pos] if pos < n else 0; pos += 1
                if cmd & 0x02:
                    buf[2] = data[pos] if pos < n else 0; pos += 1
                if cmd & 0x01:
                    buf[3] = data[pos] if pos < n else 0; pos += 1
            else:
                buf[0] = cmd
                for k in (1, 2, 3):
                    buf[k] = data[pos] if pos < n else 0
                    pos += 1
            c0 = buf[0]
            if c0 == 0xFE:
                break
            if c0 == 0x00:
                st['cmds']['00 休止'] += 1
                continue
            if c0 < 0x80:
                st['notes'] += 1
                st['cmds'][KNOWN_NOTE] += 1
            elif c0 == 0xE7:
                st['tempo_cmds'] += 1
                if buf[3]:
                    st['tempo_ramp'] += 1
                st['cmds']['E7 变速'] += 1
            elif (c0 & 0xF8) in (0xE8, 0xD8):
                k = c0 & 0x0F
                if k <= 0xE:
                    st['msg_kinds'][k] += 1
                    st['cmds']['%02X 消息' % (k << 4)] += 1
                else:
                    st['unknown']['%02X' % c0] += 1
            elif c0 == 0xF9:
                depth += 1
                st['loop_start'] += 1
                st['max_depth'] = max(st['max_depth'], depth)
                st['cmds']['F9 循环开始'] += 1
            elif c0 == 0xF8:
                st['loop_end'] += 1
                st['cmds']['F8 循环结束'] += 1
                st['loop_counts'][buf[1]] += 1
                if depth == 0:
                    st['unbalanced'] += 1
                else:
                    depth -= 1
            else:
                st['unknown']['%02X' % c0] += 1
        if depth:
            st['unbalanced'] += depth
    return st, warns


def summarize(name, files):
    """files: [(文件名, bytes)]"""
    agg = None
    for fn, data in files:
        st, _ = walk(data)
        if agg is None:
            agg = st
            agg['files'] = 0
        agg['files'] += 1
        for k in ('tracks', 'notes', 'loop_start', 'loop_end', 'unbalanced',
                  'tempo_cmds', 'tempo_ramp'):
            agg[k] += st[k]
        agg['max_depth'] = max(agg['max_depth'], st['max_depth'])
        agg['cmds'].update(st['cmds'])
        agg['unknown'].update(st['unknown'])
        agg['loop_counts'].update(st['loop_counts'])
        agg['msg_kinds'].update(st['msg_kinds'])
    return agg


def load(path):
    """返回 {包名: [(文件名, bytes)]}"""
    out = {}
    if os.path.isdir(path):
        files = []
        for f in sorted(glob.glob(os.path.join(path, '*.MMD')) +
                        glob.glob(os.path.join(path, '*.mmd'))):
            files.append((os.path.basename(f), open(f, 'rb').read()))
        if files:
            out[os.path.basename(os.path.abspath(path))] = files
    else:
        z = zipfile.ZipFile(path)
        files = [(n, z.read(n)) for n in z.namelist() if n.upper().endswith('.MMD')]
        if files:
            out[os.path.splitext(os.path.basename(path))[0]] = files
    return out


def verdict(a):
    """根据特征给出「能不能放心转」的判断。

    阈值是按实测调的：eime_98（已验证 99.95%）会被判为可放心转换，
    TH02（时长放大 7 倍）和 ukiukiis（E2 未知命令）会被标出来。
    """
    total_cmd = sum(a['cmds'].values()) + sum(a['unknown'].values())
    issues = []

    unk = sum(a['unknown'].values())
    if unk > 100 or (total_cmd and unk / total_cmd > 0.01):
        issues.append('未知命令 %d 个（%s）'
                      % (unk, ', '.join(a['unknown'].keys())))
    if a['max_depth'] > 2:
        issues.append('循环嵌套 %d 层，时长可能被放大' % a['max_depth'])
    if a['unbalanced'] > 5:
        issues.append('循环标记不配对 %d 处' % a['unbalanced'])
    if a['tempo_ramp']:
        issues.append('tempo 渐变 %d 处（未支持）' % a['tempo_ramp'])

    if not issues:
        return '✅ 可放心转换'
    return '⚠ ' + '；'.join(issues)


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not paths:
        print(__doc__)
        return
    packs = {}
    for p in paths:
        if os.path.isdir(p):
            for f in glob.glob(os.path.join(p, '*.zip')):
                packs.update(load(f))
            packs.update(load(p))
        else:
            packs.update(load(p))

    for name, files in sorted(packs.items()):
        a = summarize(name, files)
        print('=' * 72)
        print('%s   %d 个文件，%d 条有效轨' % (name, a['files'], a['tracks']))
        print('  bpm 首曲=%d  音符合计=%d' % (a['bpm'], a['notes']))
        print('  循环: 开始 %d / 结束 %d  最大嵌套 %d  不配对 %d'
              % (a['loop_start'], a['loop_end'], a['max_depth'], a['unbalanced']))
        print('  循环次数分布:', dict(sorted(a['loop_counts'].items())) or '无')
        print('  变速 %d 次（其中渐变 %d）' % (a['tempo_cmds'], a['tempo_ramp']))
        kinds = ', '.join('%02X' % (k << 4) for k in sorted(a['msg_kinds']))
        print('  MIDI 消息类型:', kinds or '无')
        print('  用到的命令:', ', '.join('%s×%d' % (k, v)
                                    for k, v in a['cmds'].most_common(10)))
        if a['unknown']:
            print('  ！未知命令:', dict(a['unknown'].most_common(8)))
        print('  判定:', verdict(a))
        print()


if __name__ == '__main__':
    main()
