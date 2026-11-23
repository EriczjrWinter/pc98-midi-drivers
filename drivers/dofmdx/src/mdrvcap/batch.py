# -*- coding: utf-8 -*-
"""批量导出某一部作品的全部 MIDI 变体曲目，并与参考 MIDI 逐首对比。"""
import os
import sys
import zipfile

import mido

from . import export as export2

HOOT = os.environ.get('HOOT_PC98', r'D:\GamedataUnpack\hoot20251231\pc98')


def tracks(pack, suffix='C.FMD'):
    path = os.path.join(HOOT, pack + '.zip')
    if not os.path.exists(path):
        print('找不到 %s —— 检查 HOOT_PC98 环境变量（当前 %s）' % (path, HOOT))
        return []
    z = zipfile.ZipFile(path)
    names = [n for n in z.namelist() if n.upper().endswith(suffix.upper())]
    z.close()
    return sorted(names)


def ref_path(pack, name):
    base = os.path.splitext(os.path.basename(name))[0]   # CR001C
    num = base[:-1] if base and base[-1] in 'CFG' else base
    rd = export2.ref_dir_for(pack)
    return os.path.join(rd, num + '.MID') if rd else None


def stats(path):
    m = mido.MidiFile(path)
    msgs = [x for tr in m.tracks for x in tr]
    return (m.length,
            sum(1 for x in msgs if x.type == 'note_on' and x.velocity > 0),
            sum(1 for x in msgs if x.type == 'program_change'))


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    use_loop = '--loop' in sys.argv[1:]
    pack = argv[0] if len(argv) > 0 else 'cl_98'
    suffix = argv[1] if len(argv) > 1 else 'C.FMD'
    outdir = argv[2] if len(argv) > 2 else os.path.join(os.getcwd(), 'midi_' + pack + '_' + suffix[0])
    os.makedirs(outdir, exist_ok=True)
    names = tracks(pack, suffix)
    print('%s: %d tracks' % (pack, len(names)))
    if not names:
        print('（没有匹配 %s 的文件；检查包名和扩展名）' % suffix)
        return
    rows = []
    for name in names:
        rp = ref_path(pack, name)
        out = os.path.join(outdir, os.path.splitext(name)[0] + '.mid')
        has_ref = bool(rp and os.path.exists(rp))
        if has_ref:
            info = export2.export_track(pack, name, out, rp)
        elif use_loop:
            info = export2.export_loop(pack, name, out)
        else:
            info = export2.export_track(pack, name, out, None)
        if has_ref:
            rd, rn, rpc = stats(rp)
            od, on, opc = stats(out)
            rows.append((name, od, rd, on, rn, opc, rpc))
            print('%-14s  %7.2fs/%-7.2fs  notes %4d/%-4d  pc %2d/%2d'
                  % (name, od, rd, on, rn, opc, rpc))
        else:
            rows.append((name, info['seconds'], None, 0, None, 0, None))
            print('%-14s  %7.2fs  %s' % (name, info['seconds'],
                                         '(--loop 循环估长)' if use_loop else '(无参考，按 430s)'))
    # 汇总
    ok = sum(1 for r in rows if r[2] and abs(r[1] - r[2]) < 2.0)
    print('时长吻合(<2s): %d / %d' % (ok, len(rows)))


if __name__ == '__main__':
    main()
