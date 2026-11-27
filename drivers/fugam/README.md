# 风雅（FUGA）FMD / FMD5 MIDI 驱动

## 曲尾怎么切（现行做法，2026-11-27）

风雅的曲子既有几秒的 logo，也有三分钟以上的 ending，而**多数 BGM 是无限循环**。
现在统一用**静态音序器**：直接按记录流算出长度，不再等运行时循环重复。

- 有限曲：曲终 = `max(各轨总长)`，文件切到「最后一个 note-on + 2 s」；
- 无限曲：切在 `A（前奏终点）+ P（最外层无限循环的周期）`，循环接缝与开头无缝；
- 判据：`|runtime − static| ≤ 1`（差 1 是驱动第一拍在 tick 1 处理首记录，是常数）；
- **禁止**：固定 `max_ticks`、「第一次回跳」当终点、按曲目关闭判据。

语义与坑详见 [`docs/FMD-LOOP-F8F9.md`](docs/FMD-LOOP-F8F9.md)；
每个 build 的轨道表地址见 [`docs/EXPORTER-PROFILES.md`](docs/EXPORTER-PROFILES.md)。

富士通系 PC-98 的 MIDI 驱动族。按代次分 **A 代**（`FMD9.EXE` / `FMD13.EXE`）与
**B 代**（`FMD.EXE` 1.5x–1.72），另有独立的 `FMD5.EXE`（风雅セレクション用，`/e` 参数）。

- 逆向细节与全部实测数据：`docs/FMD-BUILDS.md`、`docs/FMD.md`
- 方法论（观测纪律、机制优先于拟合）：仓库 `lessons/HANDBOOK.md`
- MMD 侧对 `0xFD` 的口径差异：`../mmd/docs/MMD.md`

---

## 状态（2026-11-25 更新）

| 线 | 状态 | 说明 |
|---|---|---|
| **A 代（FMD9 / FMD13）** | ✅ **可交付**（Amaranth II GS 36 + MT-32 34，斜率 1.000） | — |
| 1.71 / 1.72（B 代） | ✅ **`AMA4_015` 已对齐 HOOT**（斜率 1.00024、鼓 9/9、密度 0.88；1.71=1.72 输出相同） | **批量 237/255 ok；11 首 `end=cap` 待修**；TLOVE_02/08 未收口；根因是播放期 code hook 让 `cmp` 丢 CF，见 `docs/FMD-BUILDS.md` §37 |
| FMD5（fgsel） | ⚠ 未过 | MAZE00 1716→2085、MAZE01 1842→1658 音（HOOT 3224/2363）；ch3–ch7 198 条/通道（HOOT 339），非单调改善 |

**原「共同缺口」判断作废**：B 代不是「音源槽/通道分配」未复刻，而是观测工具污染了
`0x0CFC` FD 扫描的 `cmp` 分支（`si` 每次只 +4）。FMD5 仍有通道铺开缺口，是下一条线。

**交付口径**：只认 A 代 70 个文件；B 代已批量导出 237/255，但仍标 **unverified**，
待审计（台账 `build/audit/fuga_ledger.csv`：11 cap / TLOVE_02/08 / FMD5 未收口）。
`no-ref`（382 首）按「修完已知问题后新旧导出无差别」回归验收，不逐首找 HOOT。
`build/hootcap/fmd/` 其余 99 个文件、`fmd_synth/` 41 首、旧的
`AMA4_015_1.71_fixed.mid`/`fgsel_MAZE0{0,1}.mid` 仍标 **unverified**。

完整依据见 `docs/FMD-BUILDS.md` §31–§37，方法论见 内部审查清单（不随库发布）。
后续执行清单见 [`docs/ROUTE-v1-2026-11-26.md`](docs/ROUTE-v1-2026-11-26.md)。


## 关键：先读 docs/BOARD-SPEC.md

**FMD 期望的硬件环境 = PC-98 MIDI 卡的公共交集（MPU-401 intelligent mode）。**
板卡模型已落地（`build/mpu401.py`）：端口/状态位/命令表/FIFO/`$DF`/TX/IRQ 与 JSONL 四层日志。
**conductor 假设已被日志证伪**：A/B 两代 17,242 条命令里 `$8C/$8D/$F8/$F9` 0 次；
`$F9/$F8/$8C/$8D` 没有进入模型。B 代真正的坑是 **播放期 code hook 污染 `cmp` 的 CF**，
不是板子、不是 conductor。结论与证据见 `docs/BOARD-SPEC.md` §三、§十一。
