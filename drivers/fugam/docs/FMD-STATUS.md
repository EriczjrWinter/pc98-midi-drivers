# FMD 正式结档总表（2026-11-26）

> ✅ **已结档**：FMD 线完成并冻结。最终汇总 `build/hootcap/fmd-collection/`（445 个 MIDI）。

## 已导出/验收

| 驱动/build | 包 | 产物 | 状态 |
|---|---|---|---|
| FMD9 4774 | ama2s_98 / ama2_98 | `fuga-a` | A：OPENING 335/9461；95+99 identical 回归 |
| FMD.EXE 4969 | ama4/amakh/deadfc | `fuga-b` | B：TLOVE_08 197/19006 |
| FMD.EXE 4857 | farce/hiragi/momoko/papa/reno/tlove12/yumecol | `fuga-b` | B 批量 |
| FMD.EXE 4773 | ama3_98 | `fuga-b/ama3_98` + `ama3s_98` | MT + GS 各 24 |
| FMD.EXE 5365 a/b | bonnou3 / mug-r | `fuga-b` | 两 hash 分开 |
| FMD.EXE 4601 | venus_98 | `fuga-a`/`fuga-b` | A/B 都通过 |
| FMD.EXE 4341 | oerstd98 | `fuga-b` | cycle |
| FMD.EXE 5248 | image2_98 | `fuga-a`/`fuga-b` | A/B 都通过 |
| FMD.EXE 5248 | image1_98 / p_club_98 | `fmd5248` | 全轨向量周期；TITLE 195/3264/3459；DORA 784/8832/9616 |
| FMD13 5301 | ama2m_98 | `fmd13/ama2m_98` | P1 legacy-A，34 首 loop29/pass5 |
| FMD14 4341 | sanina_98 | `fuga-b` | max40000 + cycle off |
| FMD5 4485 | fgsel1m/fgsel1c | `fmd5/maze`,`calc` | 32 首（含 FGTTL/MAZE03） |
| FMD7 4998 | marple98 | `fmd7/marple98` | 9 首 loop5/fe4 |

## 已移出风雅（独立驱动，不是 FMD 未完成）

| 包 | 新归属 | 原因 |
|---|---|---|
| ayayo2_98 | [`drivers/emd98`](../../emd98/README.md) | `.EMI` + `EMD_98.COM`，FMD7051 不是实际入口 |
| sematte_98 | [`drivers/abiko98`](../../abiko98/README.md) | `.MUS/.ONS` + `ABIKO_98.COM` |

这两个包不再出现在风雅的“待处理驱动”里；它们各自是独立逆向项目。

## 关键规则

```text
1. 导出前先看源结构 + shells/tail，不取 cand[0]。
2. loop 只认 depth=1 外层；pass 不依赖末尾 FF/32。
3. pass 尾部 = 最后 note + 2 s；cycle 需记录匹配键。
4. A/B 是 profile preset，不是驱动代际。
5. 同一 build 可同时出现在 A/B（4601/5248）。
```

## 文档索引

- `drivers/fugam/docs/FMD.md` §九/§十
- `drivers/fugam/docs/DRIVER-VARIANTS.md` §五–§八
- `build/audit/fmd_build_diff.md`
- `build/audit/A_end_table.csv` / `B_end_table.csv`
- `build/audit/fmd13_end_table.csv`
- `build/audit/fmd5_end_table.csv`
- `build/audit/fmd7_end_table.csv`
- `build/audit/fmd5248_end_table.csv`

## 最终可转移汇总（2026-11-27）

```text
build/hootcap/fmd-collection/
build/audit/fmd-collection-2026-11-27.zip
```

内容：**448 个 MIDI**

| 组 | 数量 |
|---|---:|
| A | 100 |
| B | 263 |
| FMD5 | 32 |
| FMD13 | 34 |
| FMD7 | 9 |
| FMD5248 | 10 |

排除：

```text
VENUS_00.GS.mid     0 音占位
fuga-b/marple98/*   旧坏产物；FMD7 新产物已替换
```

每包报告在 `_reports/`，完整哈希/时长在 `MANIFEST.csv`。

## 结档后短曲复核（2026-11-26）— 待 P0–P4 重判

生成的 `build/audit/fmd_new_vs_old.csv` 共 23 行（含 marple 旧产物 7 行）。
A 代 `static`/depth≥2 误停已临时改取自然长度，但**尚未完成静态判定链**：

```text
DHILTHY / AMA2_006   6.495 s -> 55.73 s（tentative）
AMA2_012            39.484 s -> 108.11 s（tentative）
AMA2_013            16.649 s -> 93.54 s（tentative）
AMA2_020            10.570 s -> 60.64 s（tentative）
```

**重要**：静态音序器显示 `AMA2_006` 是无限曲：

```text
L=1200  P_out=10752  →  C=11952 ticks
```

所以 55.73 s 仍是预算截断，不是终点；最终以 P0–P4 静态切点为准。
详细清单：`build/audit/fmd_new_vs_old.csv`。

## 短曲复核（2026-11-27，人工听感确认）

静态导出后有 24 个"时长 < 20s"的文件，按命名与跨作品重复排除标题曲后，
以下 5 首经人工试听确认**无问题**，不再标记为可疑：

| 文件 | 时长 | 音符 | 判定 |
|---|---|---|---|
| `VENUS_09.mid` | 9.9 s | 298 | 短曲，正常 |
| `AMA3_019.mid` | 5.5 s | 70 | 短曲，正常 |
| `DFRC_014.mid` | 8.7 s | 118 | 短促循环曲，循环两次、无截断尾 |
| `DFRC_012.mid` | 19.8 s | 525 | 前段正常 + 尾部循环回跳，尾部完整 |
| `MAG-R_00.mid` | 18.4 s | 457 | 短循环曲，结构 1-2-1 |

排除规则（供以后复用）：
1. 文件名含 `000` / `TTL`（如 `FGTTL`）→ 标题曲，短是正常；
2. 不同作品出现**完全相同的 (时长, 音符数)** → 同一份标题资源复用（如 `AMA3_000` 与 `DFRC_000`、
   `AMA4_000` 与 `AMKH_000`）；
3. 剩余短曲逐个试听，开循环听接缝：自然衔接 = 真短；停顿/吃音 = 切点错。
