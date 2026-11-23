# -*- coding: utf-8 -*-
"""命令行：导出一个包（或单个 .MDT）为 MIDI。

    python -m mdt ee_98                 # 整包，默认输出到 ./mdt_out/<pack>
    python -m mdt ee_98 D:\\out\\ee      # 指定输出目录
    python -m mdt --file X.MDT          # 单文件，输出同目录同名 .mid
"""
import os
import sys
import zipfile

from . import writer

ROOT = os.environ.get('HOOT_PC98', r'D:\GamedataUnpack\hoot20251231\pc98')


def export_pack(pack, outdir=None, max_seconds=420.0):
    zpath = os.path.join(ROOT, pack + '.zip')
    if not os.path.exists(zpath):
        print('找不到 %s' % zpath)
        return 1
    outdir = outdir or os.path.join('mdt_out', pack)
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        songs = sorted(n for n in z.namelist() if n.upper().endswith('.MDT'))
        ok = zero = 0
        for song in songs:
            smf, st = writer.convert(bytearray(z.read(song)),
                                     max_ticks=int(max_seconds * 48))
            out = os.path.join(outdir, os.path.splitext(song)[0] + '.mid')
            with open(out, 'wb') as f:
                f.write(smf)
            if st['notes']:
                ok += 1
            else:
                zero += 1
            print('  %-22s notes %4d  ticks %6d' % (song, st['notes'], st['ticks']))
        print('%s: %d 首（有音符 %d，0 音符 %d）-> %s'
              % (pack, len(songs), ok, zero, outdir))
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    if args[0] == '--file':
        out, st = writer.convert_file(args[1])
        print('%s -> %s  音符 %d tick %d' % (args[1], out, st['notes'], st['ticks']))
        return 0
    pack = args[0]
    outdir = args[1] if len(args) > 1 else None
    return export_pack(pack, outdir)


if __name__ == '__main__':
    sys.exit(main())
