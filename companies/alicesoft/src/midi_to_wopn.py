#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""midi_to_wopn.py —— 把 MIDI 的 program change 改写成 WOPN bank 的槽号。

为什么需要：WOPN 的「program」不是 GM 音色号，而是 bank 里的槽位（0-127）。
一首用 GM 音色号写的 MIDI，直接配 WOPN 会全部指错槽；这个脚本只重写 program change
的数据字节，**音符、时值、CC、文件长度一律不动**。

三种映射来源，任选其一：
  --map-csv  midi2fm_mapping.csv --song N   # 本项目的 MDA 表（song,program,patch）
  --map-json mapping.json                   # {"programs": {"19": 13, ...}}
                                            # 或 {"songs": {"1": {"19": 13}}}

典型用法：
  # 1) 先看看这首用了哪些音色、会映射到哪
  python midi_to_wopn.py --map-csv midi2fm_mapping.csv --song 1 --bank ambi_fm.wopn --list "01.mid"

  # 2) 真正改写
  python midi_to_wopn.py --map-csv midi2fm_mapping.csv --song 1 --bank ambi_fm.wopn \
        --ssg-channels 3,4,5 --ssg-slot 26 -o "01_fm.mid" "01.mid"
"""
from __future__ import annotations

import argparse
import csv
import json
import struct
import sys
from pathlib import Path

N_DEFAULT_DRUMS = 9


# ---------------------------------------------------------------- WOPN
def read_wopn(path: str):
    """返回 (槽位名列表, chip_type, 打击乐非空槽数)。只读 melodic 库。"""
    d = Path(path).read_bytes()
    if d[:11] not in (b'WOPN2-B2NK\x00', b'WOPN2-BANK\x00'):
        raise ValueError('不是 WOPN 文件: %s' % path)
    ver = struct.unpack_from('<H', d, 11)[0] if d[:11] == b'WOPN2-B2NK\x00' else 1
    mel = struct.unpack_from('>H', d, 13)[0]
    perc = struct.unpack_from('>H', d, 15)[0]
    flags = d[17]
    p = 18
    names = []
    if ver >= 2:
        for _ in range(mel + perc):
            names.append(d[p:p + 32].rstrip(b'\x00').decode('ascii', 'replace'))
            p += 34
    inst_size = 69 if ver >= 2 else 65
    p0 = p
    slots = []
    for i in range(128):
        q = p0 + i * inst_size
        nm = d[q:q + 32].rstrip(b'\x00').decode('ascii', 'replace')
        if inst_size == 69:
            don, doff = struct.unpack_from('>H', d, q + 65)[0], struct.unpack_from('>H', d, q + 67)[0]
            blank = (don == 0 and doff == 0 and not nm)
        else:
            blank = not nm
        slots.append(None if blank else nm)
    pp = p0 + 128 * inst_size * mel
    nperc = 0
    for i in range(128):
        q = pp + i * inst_size
        if inst_size == 69:
            don, doff = struct.unpack_from('>H', d, q + 65)[0], struct.unpack_from('>H', d, q + 67)[0]
            if not (don == 0 and doff == 0):
                nperc += 1
        elif d[q:q + 32].strip(b'\x00'):
            nperc += 1
    return slots, (flags >> 4) & 1, nperc


# ---------------------------------------------------------------- 映射
def load_map(args) -> dict:
    """返回 {program: slot}（单曲）或 {song: {program: slot}}。"""
    if args.map_json:
        j = json.loads(Path(args.map_json).read_text(encoding='utf-8'))
        if 'programs' in j:
            return {int(k): int(v) for k, v in j['programs'].items()}
        if 'songs' in j:
            return {int(s): {int(k): int(v) for k, v in m.items()} for s, m in j['songs'].items()}
        raise ValueError('JSON 里既没有 programs 也没有 songs')
    if args.map_csv:
        table = {}
        with open(args.map_csv, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if r.get('app', 'melodic') != 'melodic':
                    continue
                song = int(r['song'])
                prog = int(r['program'])
                if r.get('slot') not in (None, ''):
                    slot = int(r['slot'])
                else:                                   # patch = "P07"
                    slot = int(r['patch'].lstrip('Pp')) - 1
                table.setdefault(song, {})[prog] = slot
        if args.song:
            return table.get(int(args.song), {})
        return table
    raise SystemExit('需要 --map-csv 或 --map-json')


# ---------------------------------------------------------------- SMF
def iter_events(data: bytes):
    """线性遍历，yield (偏移, tick, 状态, 数据...)；只 yield 需要的事件。"""
    hlen = struct.unpack_from('>I', data, 4)[0]
    ntrk = struct.unpack_from('>H', data, 10)[0]
    pos = 8 + hlen
    for _ in range(ntrk):
        tlen = struct.unpack_from('>I', data, pos + 4)[0]
        i, end, rs, tick = pos + 8, pos + 8 + tlen, 0, 0
        while i < end:
            v = 0
            while True:
                b = data[i]; i += 1
                v = (v << 7) | (b & 0x7F)
                if not b & 0x80:
                    break
            tick += v
            b = data[i]
            if b & 0x80:
                if b < 0xF0:
                    rs = b
                st = b; i += 1
            else:
                st = rs
            if st == 0xFF:
                mt = data[i]; i += 1
                ln = 0
                while True:
                    c = data[i]; i += 1
                    ln = (ln << 7) | (c & 0x7F)
                    if not c & 0x80:
                        break
                i += ln
            elif st in (0xF0, 0xF7):
                ln = 0
                while True:
                    c = data[i]; i += 1
                    ln = (ln << 7) | (c & 0x7F)
                    if not c & 0x80:
                        break
                i += ln
            elif (st & 0xF0) == 0xC0:
                yield (i, tick, st & 0x0F, data[i])
                i += 1
            elif (st & 0xF0) == 0xD0:
                i += 1
            else:
                yield (i, tick, st & 0x0F, data[i], data[i + 1])
                i += 2
        pos = pos + 8 + tlen


def rewrite(data: bytearray, mapping: dict, ssg_channels, ssg_slot, drums, strict=False):
    stats = {'total': 0, 'changed': 0, 'skipped_drums': 0, 'ssg': 0, 'unmatched': []}
    for ev in iter_events(bytes(data)):
        off = ev[0]
        if len(ev) == 4:                          # 只有一个数据字节 -> program change
            _, tick, ch, prog = ev
            stats['total'] += 1
            if ch == drums:
                stats['skipped_drums'] += 1
                continue
            if ch in ssg_channels:
                data[off] = ssg_slot
                stats['changed'] += 1
                stats['ssg'] += 1
                continue
            if prog in mapping:
                data[off] = mapping[prog]
                stats['changed'] += 1
            else:
                stats['unmatched'].append((ch, prog))
                if strict:
                    raise SystemExit('通道 %d 的 program %d 没有映射' % (ch, prog))
    return stats


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description='把 MIDI 的 program change 改成 WOPN 槽号')
    ap.add_argument('midi', help='输入 .mid')
    ap.add_argument('-o', '--out', help='输出 .mid（不给则只做 dry-run）')
    ap.add_argument('--bank', help='WOPN 文件，用于校验槽位和显示音色名')
    ap.add_argument('--map-csv', help='如 midi2fm_mapping.csv')
    ap.add_argument('--map-json', help='{"programs":{"19":13}} 或 {"songs":{...}}')
    ap.add_argument('--song', type=int, help='CSV 模式下取哪一首')
    ap.add_argument('--ssg-channels', default='', help='这些通道改指向 SSG 槽，如 3,4,5')
    ap.add_argument('--ssg-slot', type=int, default=26, help='SSG 替身音色的槽号（默认 26）')
    ap.add_argument('--drums', type=int, default=N_DEFAULT_DRUMS, help='鼓通道，默认 9，不改')
    ap.add_argument('--list', action='store_true', help='只列出每通道的 program 序列')
    ap.add_argument('--strict', action='store_true', help='有未匹配的 program 就报错')
    a = ap.parse_args(argv)

    data = Path(a.midi).read_bytes()
    ssg = {int(x) for x in a.ssg_channels.split(',') if x.strip()}

    slots = None
    if a.bank:
        slots, chip, nperc = read_wopn(a.bank)
        used = sum(1 for s in slots if s)
        print('bank: %s  melodic 非空槽 %d  percussive 非空槽 %d  chip=%s'
              % (Path(a.bank).name, used, nperc, 'OPNA' if chip else 'OPN2'))

    if a.list:
        per = {}
        for ev in iter_events(data):
            if len(ev) == 4:
                _, tick, ch, prog = ev
                per.setdefault(ch, []).append(prog)
        mapping = load_map(a) if (a.map_csv or a.map_json) else {}
        for ch in sorted(per):
            seq = per[ch]
            tag = ' [SSG→%d]' % a.ssg_slot if ch in ssg else ''
            if ch == a.drums:
                print('  ch%-2d 鼓（不改）%d 条 PC' % (ch, len(seq)))
                continue
            m = ' '.join('%s→%s' % (p, (a.ssg_slot if ch in ssg else mapping.get(p, '?'))) for p in seq)
            print('  ch%-2d%s  %s' % (ch, tag, m))
        return 0

    mapping = load_map(a)
    buf = bytearray(data)
    stats = rewrite(buf, mapping, ssg, a.ssg_slot, a.drums, a.strict)

    print('program change 共 %d：改写 %d（其中 SSG %d），鼓通道跳过 %d，未匹配 %d'
          % (stats['total'], stats['changed'], stats['ssg'], stats['skipped_drums'],
             len(stats['unmatched'])))
    if stats['unmatched']:
        print('  未匹配:', sorted(set(stats['unmatched'])))
    if slots:
        empty = [s for s in sorted(set(mapping.values())) if s < 128 and slots[s] is None]
        if empty:
            print('  警告：这些槽在 bank 里是空的 ->', empty)

    if not a.out:
        print('（dry-run，没写文件；加 -o 输出）')
        return 0

    # 只有 0xC0 的数据字节被改过，长度不变；但这里仍按原样写回
    Path(a.out).write_bytes(bytes(buf))
    print('->', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
