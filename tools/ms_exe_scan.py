# -*- coding: utf-8 -*-
"""在 MSDRV4.EXE 里找处理 0xE7 命令的代码。"""
import struct
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'


def load():
    z = zipfile.ZipFile(H + r'\karanon_98.zip')
    return z.read('MSDRV4.EXE')


def mz_info(d):
    if d[:2] != b'MZ':
        return None
    last, pages, relocs, hdr, _, _, _, ss, sp, _, ip, cs, reloc_off = \
        struct.unpack_from('<HHHHHHHHHHHHH', d, 2)
    size = pages * 512 - (512 - last if last else 0)
    return {'size': size, 'hdr': hdr * 16, 'cs': cs, 'ip': ip,
            'ss': ss, 'sp': sp, 'relocs': relocs, 'reloc_off': reloc_off}


def main():
    d = load()
    info = mz_info(d)
    print('MSDRV4.EXE %d 字节' % len(d))
    for k, v in (info or {}).items():
        print('  %-9s %s' % (k, hex(v) if k != 'size' else v))
    if not info:
        return
    print('\n代码段线性起点 = 0x%X' % info['hdr'])
    body = d[info['hdr']:]
    cs = info['cs']

    # 常见比较形式：3C E7 (cmp al,0E7h) / 80 F8 E7 / 3D E7 00
    pats = {
        '3C E7 (cmp al,E7)': b'\x3c\xe7',
        '80 F8 E7 (cmp al,E7)': b'\x80\xf8\xe7',
        '3D E7 00 (cmp ax,00E7h)': b'\x3d\xe7\x00',
        'E7 (单字节)': b'\xe7',
    }
    for label, pat in pats.items():
        hits = []
        i = 0
        while True:
            j = d.find(pat, i)
            if j < 0:
                break
            hits.append(j)
            i = j + 1
        print('\n%s → %d 处' % (label, len(hits)))
        for h in hits[:6]:
            if h < info['hdr']:
                continue
            off_in_code = h - info['hdr']
            seg = cs + off_in_code // 16
            ip = off_in_code % 16
            print('  文件 0x%05X  → %04X:%04X   %s'
                  % (h, seg, ip, d[h - 6:h + 10].hex(' ')))


if __name__ == '__main__':
    main()
