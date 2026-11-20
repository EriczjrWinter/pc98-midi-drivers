# -*- coding: utf-8 -*-
"""把抓到的字节流整理成「tick + MIDI 消息」的时间线，方便看节奏。"""


def parse(stream):
    """stream: [(tick, byte)] -> [(tick, msg_bytes)]，处理 running status。"""
    out = []
    status = None
    i = 0
    n = len(stream)
    while i < n:
        tick, b = stream[i]
        if b >= 0xF8:                      # realtime
            out.append((tick, bytes([b])))
            i += 1
            continue
        if b >= 0x80:
            status = b
            if b in (0xF0, 0xF7):          # sysex：吃到 0xF7
                msg = [b]
                i += 1
                while i < n:
                    t2, b2 = stream[i]
                    msg.append(b2)
                    i += 1
                    if b2 == 0xF7:
                        break
                out.append((tick, bytes(msg)))
                continue
            if b >= 0xF0:                  # 其它系统消息，先按 1 字节
                out.append((tick, bytes([b])))
                i += 1
                continue
            need = 1 if 0xC0 <= b < 0xE0 else 2
            data = []
            i += 1
            while i < n and len(data) < need:
                t2, b2 = stream[i]
                if b2 >= 0x80:
                    break
                data.append(b2)
                i += 1
            out.append((tick, bytes([b] + data)))
        else:
            # running status
            if status is None:
                i += 1
                continue
            need = 1 if 0xC0 <= status < 0xE0 else 2
            data = [b]
            i += 1
            while i < n and len(data) < need:
                t2, b2 = stream[i]
                if b2 >= 0x80:
                    break
                data.append(b2)
                i += 1
            out.append((tick, bytes([status] + data)))
    return out


