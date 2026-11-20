# LEAF（リーフ）

LEAF 的 PC-98 作品里，音乐是**两套并存**的：

| 音源 | 驱动 | 数据 | 我们的状态 |
|---|---|---|---|
| **FM** | `PMD.COM`（KAJA 的通用 PMD） | `.FM` | 不用做——标准 PMD，工具生态现成 |
| **MIDI** | **`MMDR.COM`**（LEAF 私有，H.Ninomae） | `.MD` | ✅ **已解，雫 / 痕全导出（51 首）** |
| **MIDI** | **`MS.COM`**（6531 B，与 MMDR 同源框架） | `.MD` / `.MID` | ✅ **已解，雀鬼 / Filsnown 全导出（61 首）** |

> 所以真正属于 LEAF 私有的，**只有 MIDI 那条线**。FM 侧是通用的。

**两个 MIDI 驱动的关系**：`MS.COM` 不是 MMDR 的前身，而是**同一套 TSR 框架的另一个分支**——
加载器都叫 `*_98.com`（400 B）、都挂 `INT 08h`、都用 `out 0x77/0x71` 改 8253。
区别只有功能调用中断号（`INT 7Eh` vs `INT 7Fh`）。
详见 [drivers/mscom](../../drivers/mscom/)。

## 已收录作品

| 作品 | 年份 | 驱动 | 曲目 | 状态 |
|---|---|---|---|---|
| [雫 -しずく-](games/shizuku.md) | 1996 | `mmdr.com`（3218 B） | 25 | ✅ 5 份实机录音验证，逐音符吻合 |
| [痕 -きずあと-](games/kizuato.md) | 1997 | `MMDR.COM`（3954 B） | 26 | ✅ 与 OPMIDI 版本对照一致 |
| DR²ナイト雀鬼 | — | `MS.COM` | ? | ⬜ 待验证 |
| Filsnown ～光と刻～ | — | `MS.COM` | 43 | ⬜ 待验证 |

## 已验证

| 作品 | 验证方式 | 结果 |
|---|---|---|
| 雫 -しずく- | 5 份 HOOT 实机录音，逐音符对照 | 前 300 音零差异，时间比值 0.998–0.999 |
| 痕 -きずあと- | 与前辈制作的 OPMIDI 版本对照 | 一致 |

## 两个构建的差异

| | 雫 | 痕 |
|---|---|---|
| 大小 | 3218 B | 3954 B |
| 入口 | `jmp 0x0BF2` | `jmp 0x0E5A` |
| `INT 08h` | `0x0103` | `0x0103` |
| `INT 7Eh` | `0x0479` | `0x0555` |
| MIDI 端口 | `0xE0D0` | `0xE0D0` |

**接口完全兼容**，运行器只换路径。

## 目录

```
src/
  mmdr_emu.py   MMDR 运行器（Unicorn 16 位实模式 + 假时钟）
  smf_build.py  MIDI 字节流 → SMF
docs/
  MMDR.md       驱动结构 + .MD 格式 + 三个必踩的坑
games/
  shizuku.md    雫：曲目表、GS15/GS18 对调的发现
  kizuato.md    痕：曲目表、与雫的差异
```

## 用法

```bash
pip install unicorn

python src/mmdr_emu.py --dir <雫的目录> --all --count 25
python src/mmdr_emu.py --dir <痕的目录> --prefix KZ_GS --all --count 26
```

数据目录里要有 `MMDR.COM` 和 `sz_gsNN.md` / `GSNN.MD`（两种命名自动识别）。

## 待办

- [ ] 验证 `MS.COM`（雀鬼 / Filsnown）
- [ ] 确认 LEAF 哪些作品有 MIDI 音源（不是所有都有）
- [ ] 用实机录音验证痕的 26 首
