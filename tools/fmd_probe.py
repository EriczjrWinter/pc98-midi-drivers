# -*- coding: utf-8 -*-
"""分析 .FMD（D.O. 社的音乐数据，签名 "68V2"）的结构。"""
import os
import struct
import sys
import zipfile

H = r'D:\GamedataUnpack\hoot20251231\pc98'


def load(pack, name):
    z = zipfile.ZipFile(os.path.join(H, pack + '.zip'))
    return z.read(name)


def main():
    pack = sys.argv[1] if len(sys.argv) > 1 else 'cl_98'
    name = sys.argv[2] if len(sys.argv) > 2 else 'CR001G.FMD'
    d = load(pack, name)
    print('%s / %s   %d 字节' % (pack, name, len(d)))
    print('签名:', d[:4])
    print()
    # 头部看起来是 4 字节一组
    print('前 64 字节:')
    for i in range(0, min(64, len(d)), 16):
        print('  %04X  %s' % (i, d[i:i + 16].hex(' ')))
    print()
    print('按 4 字节一组解读前 20 组:')
    for i in range(0, min(80, len(d) - 3), 4):
        v = struct.unpack_from('<I', d, i)[0]
        print('  %04X  u32=%-10d  字节=%s' % (i, v, d[i:i + 4].hex(' ')))
    print()
    # 找数据区起点
    print('从 0x40 起的内容:')
    for i in range(0x40, min(0x40 + 96, len(d)), 16):
        print('  %04X  %s' % (i, d[i:i + 16].hex(' ')))


if __name__ == '__main__':
    main()
