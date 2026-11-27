# 风雅（FUGA）FMD / FMD5 MIDI 驱动

## 曲尾怎么切（现行做法，2026-11-27）

风雅的曲子既有几秒的 logo，也有三分钟以上的 ending，而**多数 BGM 是无限循环**。
现在统一用**静态音序器**：直接按记录流算出长度，不再等运行时循环重复。

- 有限曲：曲终 = `max(各轨总长)`，文件切到「最后一个 note-on + 2 s」；
- 无限曲：切在 `A（前奏终点）+ P`，其中 **P = 全轨状态向量 `(seg,cur,anchor,depth,en)`
  连续三段一致的最小周期**；循环接缝与开头无缝；
- 判据：`|runtime − static| ≤ 1`（差 1 是驱动第一拍在 tick 1 处理首记录，是常数）；
- **禁止**：固定 `max_ticks`、「第一次回跳」当终点、按 depth/层号挑周期、按曲目关闭判据。

语义与坑详见 [`docs/FMD-LOOP-F8F9.md`](docs/FMD-LOOP-F8F9.md)；
每个 build 的轨道表地址见 [`docs/EXPORTER-PROFILES.md`](docs/EXPORTER-PROFILES.md)。

富士通系 PC-98 的 MIDI 驱动族。按代次分 **A 代**（`FMD9.EXE` / `FMD13.EXE`）与
**B 代**（`FMD.EXE` 1.5x–1.72），另有独立的 `FMD5.EXE`（风雅セレクション用，`/e` 参数）。

- 逆向细节与全部实测数据：`docs/FMD-BUILDS.md`、`docs/FMD.md`
- 方法论（观测纪律、机制优先于拟合）：仓库 `lessons/HANDBOOK.md`
- MMD 侧对 `0xFD` 的口径差异：`../mmd/docs/MMD.md`

---

## 状态：已完成（2026-11-27）

**8 个分支 / 12 个 build / 420 首**，全部按静态音序器计算长度并通过 `|runtime − static| ≤ 1`。

| build | 轨道表 | 包 | 曲数 |
|---|---|---|---:|
| `FMD9.EXE` 4774 | `0x0E64` | ama2_98 / ama2s_98 | 72 |
| `FMD.EXE` 4969 / 4857 | `0x0EBC` | ama4 / amakh / deadfc / farce / hiragi / momoko / papa / reno / tlove12 / yumecol | 142 |
| `FMD.EXE` 4773 | `0x0C9E` | ama3_98 / ama3s_98 | 48 |
| `FMD13.EXE` 5301 | `0x0F0F` | ama2m_98 | 34 |
| `FMD5.EXE` 4485 | `0x0D1A` | fgsel1c / fgsel1m | 32 |
| `FMD.EXE` 5248 | `0x0E70` | image1_98 / image2_98 / p_club_98 | 24 |
| `FMD.EXE` 5365 / 4601 / 4341 | `0xD18` / `0xCB8` / `0xCD0` | mug-r / venus / oerstd | 47 |
| `FMD14.EXE` 4341 | `0x0CD2` | sanina_98 | 12 |
| `FMD7.EXE` 4998 | `0x0E09` | marple98 | 9 |

逐 build 的完整档案（含 `df` / `tempo` / `end` / 源变体规则）见
[`docs/EXPORTER-PROFILES.md`](docs/EXPORTER-PROFILES.md)。

**不属本驱动、另行处理的两个包**：`ayayo2_98`（`.EMI` + `EMD_98.COM` 壳）、
`sematte_98`（`.MUS/.ONS` + `ABIKO_98.COM` 壳）——它们的记录流不是 FMD 格式。

## 走过的弯路（值得记住的三条）

1. **播放期 code hook 会让 `cmp` 丢 CF**：一度造出"查表不命中 / F8 计数永远完成 /
   锚点只 +4"三个假象，拆掉后全部消失（复盘见仓库 `lessons/heisenberg/`）。
2. **"自相似找周期"会把半周期当整周期**：旧动态产物的 `loop` 元数据不可当基准，
   真值只有驱动内部状态与静态走数据两个来源。
3. **A/B 是 profile preset，不是驱动代际**：同一 build 可能同时出现在两个预设里
   （`image2_98`/`venus_98` 曾因此重复交付，已去重）。

完整证据链见 `docs/FMD-BUILDS.md` §31–§37、`docs/FMD-LOOP-F8F9.md` §35，
方法论见仓库 `lessons/HANDBOOK.md`。


## 关键：先读 docs/BOARD-SPEC.md

**FMD 期望的硬件环境 = PC-98 MIDI 卡的公共交集（MPU-401 intelligent mode）。**
板卡模型已落地（`build/mpu401.py`）：端口/状态位/命令表/FIFO/`$DF`/TX/IRQ 与 JSONL 四层日志。
**conductor 假设已被日志证伪**：A/B 两代 17,242 条命令里 `$8C/$8D/$F8/$F9` 0 次；
`$F9/$F8/$8C/$8D` 没有进入模型。B 代真正的坑是 **播放期 code hook 污染 `cmp` 的 CF**，
不是板子、不是 conductor。结论与证据见 `docs/BOARD-SPEC.md` §三、§十一。
