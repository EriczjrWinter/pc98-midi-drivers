# -*- coding: utf-8 -*-
"""批量导出某一部作品的全部 MIDI 变体曲目，并与参考 MIDI 逐首对比。"""
import os
import sys
import zipfile

import mido

from . import export as export2

HOOT = os.environ.get('HOOT_PC98', r'D:\GamedataUnpack\hoot20251231\pc98')


def tracks(pack, suffix='C.FMD'):
    z = zipfile.ZipFile(os.path.join(HOOT, pack + '.zip'))
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
    pack = sys.argv[1] if len(sys.argv) > 1 else 'cl_98'
    suffix = sys.argv[2] if len(sys.argv) > 2 else 'C.FMD'
    outdir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.getcwd(), 'midi_' + pack + '_' + suffix[0])
    os.makedirs(outdir, exist_ok=True)
    names = tracks(pack, suffix)
    print('%s: %d tracks' % (pack, len(names)))
    rows = []
    for name in names:
        rp = ref_path(pack, name)
        out = os.path.join(outdir, os.path.splitext(name)[0] + '.mid')
        info = export2.export_track(pack, name, out, rp if rp and os.path.exists(rp) else None)
        if rp and os.path.exists(rp):
            rd, rn, rpc = stats(rp)
            od, on, opc = stats(out)
            rows.append((name, od, rd, on, rn, opc, rpc))
            print('%-14s  %7.2fs/%-7.2fs  notes %4d/%-4d  pc %2d/%2d'
                  % (name, od, rd, on, rn, opc, rpc))
        else:
            rows.append((name, info['seconds'], None, 0, None, 0, None))
            print('%-14s  %7.2fs  (无参考)' % (name, info['seconds']))
    # 汇总
    ok = sum(1 for r in rows if r[2] and abs(r[1] - r[2]) < 2.0)
    print('时长吻合(<2s): %d / %d' % (ok, len(rows)))


if __name__ == '__main__':
    main()
