# FUGAM / FMD —— 正式结档（2026-11-26）

> ## 📌 当前状态（2026-11-27）
>
> **风雅已全部解出并交付：8 个分支 / 448 首**，曲尾截断改用**静态音序器**
> （按记录流算长度，不等运行时循环）。本文以下内容是**过程记录**，
> 其中"结案/无法复现/只交付 A 代"等表述为**当时结论，已被推翻**。
>
> 现行权威来源：
> - 交付清单与最终状态：仓库根 `README.md` 的「风雅（FUGA / FMD）完成清单」
> - 记录流与循环语义（F9/F8、FD/FC 锚点同步）：[`FMD-LOOP-F8F9.md`](FMD-LOOP-F8F9.md)
> - 每个 build 的轨道表地址与能力：[`EXPORTER-PROFILES.md`](EXPORTER-PROFILES.md)
> - 曲尾方案的演进：[`FMD-END-PLAN.md`](FMD-END-PLAN.md)
> - 方法论（观测纪律、机制优先于拟合）：仓库 `lessons/HANDBOOK.md`

PC-98 上由 **FMD.EXE / FMD5/7/9/13/14.EXE + FUGAM_98.COM** 驱动的 MIDI 音乐，
HOOT 里共 **34 个包**（GS 19 / MT-32 13 + 13 个 Emulation 重复条目 / SC-55 4 / 无标签 5，
**没有 SC-88 / CM-64**）。

> ## ✅ 正式结档
>
> FMD 线已完成并冻结：
>
> - A：100 首成品（VENUS_00 占位除外），`fuga-a`
> - B：263 首成品，`fuga-b`
> - FMD5：32 首，`fmd5`
> - FMD13：34 首，`fmd13`
> - FMD7：9 首，`fmd7`
> - FMD5248：10 首，`fmd5248`
> - 最终可转移汇总：`build/hootcap/fmd-collection/`（448 个 MIDI）
>
> 当前总表以 [`FMD-STATUS.md`](FMD-STATUS.md) 为准；
> 最终技术细节见 [`FMD-FINAL-NOTES.md`](FMD-FINAL-NOTES.md)。
>
> **已移出风雅**（不是 FMD 未完成）：
> `ayayo2_98 → drivers/emd98`（`EMD_98.COM + .EMI`），
> `sematte_98 → drivers/abiko98`（`ABIKO_98.COM + .MUS/.ONS`）。
>
> 下面是开发过程记录；其中“B 代 237/255 / 11 cap / FMD5 未过 / FMD7 坏”
> 都是历史状态，已被本次结档取代。

## ✅ 2026-11-25 更新：B 代已通并批量导出，原「结案」撤销

B 代（1.71 / 1.72）在 `AMA4_015` 上已对齐 HOOT：**斜率 1.00024、窗内 2691 vs 2696 音、
音高相似度 0.999、鼓 9 种（含 42）、事件密度 0.88**；1.71 与 1.72 输出 SHA256 完全相同。
A 代两个哈希不变（`A5AB…` / `99ED…`，42.4 s / 51.7 s）。

根因不是「音源槽/通道分配」，也不是板子，而是**播放期 code hook 让 Unicorn 的 `cmp` 丢了 CF**：
`0x0CFC` 的 FD 扫描 `cmp al,0xFC / jb` 永远不跳，锚点每次只 +4，播放被反复拉回。
拆掉播放期 hook（安装期范围 hook 用完即拆、不再装 `hook_all_ints`）后即恢复。
详见 [`FMD-BUILDS.md`](FMD-BUILDS.md) §37 与 [`BOARD-SPEC.md`](BOARD-SPEC.md) §11.6。
**B 代批量：237/255 首 ok，11 首 `end=cap` 待修，TLOVE_02/08 未收口**；产物仍标
unverified，审计台账 `build/audit/fuga_ledger.csv`。
**FMD5 同 bug 改善但不单调、仍未过**（MAZE00 1716→2085，MAZE01 1842→1658；
HOOT 3224 / 2363；ch3–ch7 仍只铺到 198 条/通道）。是下一刀。
下面 2026-11-23 的结案文字保留为历史记录。

## ⛔ 结案（2026-11-23，已被 2026-11-25 更新取代）

**A 代（`FMD9` / `FMD13`）已完成并交付**：Amaranth II GS 36 首 + MT-32 34 首，共 **70 个文件**，
与 HOOT 抓取逐事件对齐斜率 1.000（六首样本）。

**B 代（`FMD.EXE` 1.5x–1.72 / `FMD5` / `FMD7`）结案归档，不再继续。**
受限于**「音源槽/通道分配」未复刻（FMD-BUILDS.md §36.3）**，我们无法复现 HOOT 的实际演奏：驱动装得上、歌载得进、也有音符，
但**轨道→通道映射、鼓轨音高集合、事件密度**全都不对。用 `AMA4_015_HOOT.mid` 这个参考：

| 指标 | 通过线 | 实测 |
|---|---|---|
| 音高序列相似度 | ≥ 0.8 | **0.008** |
| 拍数/时长 | 差 < 5% | 不适用（导出不是自相似重复） |
| ch9 鼓音高集合 | 9 种 | **6 种** |
| 每 1/48 拍事件数 | — | HOOT 3.85 / 我们 1.64 |

**已排除**（都做过实验，不是猜的）：内存流程（三版 harness 输出逐字节相同）、`AH=48` 语义、
`cs:[7]` 缓冲区、`FMD.EXE` build 差异（1.71 与 1.72 引擎逐字节相同）、壳的初始化
（`FUGAM_98.COM` 反汇编确认只有 0201/0100/0300/01FF + 清 `[0x1E]`，**没有**轨道分配）。
**剩余可疑**只有一层：板子状态 / FIFO 语义（我们 `in 0xE0D0` 永远给 `0xFD`，一次只推进一条记录，
而 HOOT 的事件密度是 2.3 倍）。

这个驱动的难度**远高于本工程其它驱动**：每一轮都要「HOOT 录制 + 逐事件对齐 + 驱动反汇编」三件套，
而收益只有一个包的几首曲子。**继续逆向的成本不现实 → 结案**。解锁条件与全部证据链见
[`FMD-BUILDS.md`](FMD-BUILDS.md)（§9–§21）。

**交付口径（2026-11-23 历史口径，已废弃）**：当时只认 A 代那 70 个文件。B 代批量 237/255 已落盘
`build/hootcap/fmd_b/`，但仍标 **unverified**，待审计（台账
`build/audit/fuga_ledger.csv`：11 cap / TLOVE_02/08 / FMD5 未收口）；
`no-ref` 按「修完已知问题后新旧导出无差别」回归验收。
`build/hootcap/fmd/` 里其余 99 个文件标 **unverified**
（含 `fmd_synth/` 补过 program 的 41 首——底子错，不可当成果引用）。

> ⚠ 过滤陷阱：`.FMD` 是 **MDRV98 B 路线的数据扩展名**，不是这个驱动。必须按 HOOT
> 的 shell 行筛（`fmd*` / `fugam_98`），否则会得到 200 多个包。同理，reno/venus/ama3
> 那些 `(OPN)` 条目是 `opndrv` + `fgplay_h`（FM），跟这套驱动无关。

## 〇、这个驱动必须靠「MIDI 板高仿真」才能跑

和 MMD / MSDRV / FMP 不一样，**FMD 不能静态解析**——它的时间轴不在数据里，也不在驱动里：

| 环节 | 在哪 |
|---|---|
| 事件间隔 | 数据里只有 tick 数（4 字节记录的第二字节） |
| 1 tick 多长 | 板子：`$C2` 定 timebase（48 tick/拍）+ `$E0` 定 tempo（BPM） |
| 什么时候走一步 | 板子：`$95` 打开时钟输出，每个时钟回一个 `$FD`，驱动读到一个就推进一步 |
| 能不能读写 | 板子：`0xE0D2` 的 bit7（有字节）/ bit6（忙），命令要等 `$FE` ACK |
| 驱动内部开关 | 壳：`FUGAM_98.COM` 扫签名清 `[0x1E]`，否则 `INT D3` 直接 `iret` |

也就是说：**「下一步在哪」这个问题的答案，分散在 数据 + 驱动 + 板子固件 + 壳** 四处。
少仿一个环节就拿不到正确的时间轴——这正是前面几次标定（12 / 24 tick/拍）翻车的原因：
那时板子模型只是个「每次读都给一个 `$FD`」的桩子，时间分辨率完全由我们的拟合决定。

所以正确做法是：**16 位 x86 仿真（unicorn）+ MPU-401 板模型**，
板模型至少要有：状态位语义、命令 ACK、`$FD` 时钟输出、`$C2-$C8` timebase 与 `$E7` 分割解析。
导出器就是「让驱动自己跑」，不是「读数据猜音符」。

## 一、驱动两代

| 代 | 驱动 | 特征 | 状态 |
|---|---|---|---|
| A | `FMD9.EXE` / `FMD13.EXE`（ama2 系） | `INT D3 = 1010:0056`，`INT 0E = 1010:05BF`，装完就能用 | ✅ 已跑通 |
| B | `FMD.EXE` / `FMD5/7/14.EXE`（GS/SC-55 那批） | `INT D3 = 1010:003F`，带 `[0x1E]` 标志 | ⚠ 装载通了，tick 还没出声 |

两代都是 SLR/Zortech 编译的 MZ，**必须带 `/#`**（HOOT 的 shell 行是 `fmd9 /#`、`fmd /#`），
启动做自搬移 + 自解压，搬到段 `1010`。

**B 代必须补一步**：`/#` 会把驱动内部标志（B 代是 `cs:[0x1E]`）置 1，之后 `INT D3`
进门就 `iret`，任何 API 都不干活。HOOT 的壳 `FUGAM_98.COM` 正是拿签名 `2E F6 06 xx xx 01 75`
在 D3 入口扫到这个变量再**清 0** 的。仿真里必须照做（`build/_fmd_export.py: shell_patch()`），
否则装载、播放全静默。A 代没有这个标志。

安装要点（已实现，`build/_fmd_play3.py` / `_fmd_export.py`）：
1. PSP：命令尾 ` /#`、`0x2C` 环境段、`0x02` 内存顶；
2. `AH=48/49/4A` 返回真实段地址（bump 分配器）；
3. 搬移区 `0x10100-0x16000` 内拦 `CD 21`，命中后模拟 DOS 并 `IP += 2`；
4. `INT 15` 装 IRET 桩；把 `INT 0E` 指向自己的 tick 处理。

## 二、板子协议（公共 MIDI 板）

`0xE0D0` = 数据口，`0xE0D2` = 命令/状态口。

| 方向 | 语义 |
|---|---|
| `in 0xE0D2` | bit7=0 表示「有字节可取」，bit6=1 表示「忙」 |
| `out 0xE0D2, n` | 发命令 `n`，随后读数据口等 `0xFE`（ACK） |
| `out 0xE0D0, b` | 发 MIDI 数据字节（数据字节都 `< 0x80`） |
| `in 0xE0D0` | 读板子给的字节；`0xFD` 是板子的「该走一步了」标记，`0xFE` 是命令 ACK |

这套 0xE0D0/0xE0D2 + 复位 `0xFF` + ACK `0xFE` 在本仓库里 **MMD / MDRV98 / MSDRV / FMP
都在用**（见 `drivers/mmd/README.md`：MMD 安装要「复位 0xFF → 收到 0xFE → 厂商命令 0x94」；
`drivers/dofmdx/docs/MDRV98.md` 记的是同一套握手）。所以「公共 MIDI 板接口」这个假设
**成立**，而且 FMD 只是这条总线上的又一个用户。

### 命令序列（A/B 两代逐项相同，实测抓包）

```
装载 AX=0100：cmd 0xFF（复位）→ cmd 0x32
播放 AX=0300：cmd 0xE0 <tempo>   ← 设速度
              cmd 0xC2
              cmd 0xE7 0x04
              cmd 0x95
              16×（cmd 0xD0 <0xB0+ch>，随后 CC7=0x7F、CC121=0）
停止 AX=01FF：cmd 0xFF → cmd 0x32
```

`0xFF`+`0x32` 在装载和停止时都出现，是「复位 + 初始化」组合；`0x94`/`0xB9` 也出现在
停止路径里（厂商命令）。这些厂商号 MMD/MDRV98 也各有自己的，说明板子是同一族、命令集
按厂商分块。

## 三、速度（0xE0 的单位）

**结论：`0xE0` 的参数是 BPM，不是定时器计数。** 依据三条，互相独立：

1. **值域对得上**：各曲头的第 0 字节是 94 / 108 / 120 / 130 / 168 / 182，正好是 BGM 的
   BPM 范围；驱动的变速 API（`AH=6`）只做 `±` 和下限 `0x28`(40) 的钳制。
2. **驱动自己把 0xE0/0xE1 当定点 BPM 用**。A 代 `0xE7`（变速）处理函数在 `0x10C05`：
   ```
   cmd 0xE2 ← buf[3]         ; 渐变量
   cmd 0xE1 ← buf[2]         ; 速度倍率，单位 1/64（0x40 = ×1.0）
       if buf[2] >= 0x40:
           if buf[2] * song_tempo >= 0x3C00:  buf[2] = 0x3C00 / song_tempo
   ```
   也就是说板子的速度寄存器 = `(0xE0 整数 BPM) × (0xE1/64 小数)`，**上限 0x3C00/64 = 240 BPM**。
   这个 `0x3C00` 是驱动硬编码的钳制值，等于 240×64。
3. **MMD 用同一套**：MMD 的曲头第 0 字节就是 BPM（`drivers/mmd/src/mmd_parser.py` 的
   `+0x00 u8 bpm`），它的变速公式 `有效 BPM = 头部 bpm × buf[2] / 64` 与上面完全一致，
   而它的板子初始化序列 `cmd 0xC2 / 0xE0 <bpm> / 0xE7 04 / 0x95` 和 FMD **逐条相同**。

FMD **不是只发 `0xE0`**：曲头用 `0xE0` 定基准 BPM，曲中变速会发 `0xE1`
（`0x40` = ×1.0，单位 1/64）。例如 TLOVE_01：

```
tick 0   $E0 0x78 (120 BPM)
tick 30  $E1 0x3C (60/64) → 有效 112 BPM
```

旧导出只扫 `0xE0`，所以 TLOVE 整首按 120 走，比 WIN 版快 6.7%。现在
`build/_fmd_export.py: tempo_map()` 同时扫 `0xE0`/`0xE1`，按 tick 生成完整
timed tempo map；有效 BPM 按 NP2 的 `curtempo` 取整。`$E2`（graduation）仍未建模。

**每拍多少 tick**：**48**，来源是 **MPU-401 的 `$C2`（SET TIMEBASE）**，不是板子默认值、
也不是我们拟合出来的。整条命令链（Roland MPU-401 Technical Reference Manual 5.8 节 +
Sierra SC18000 数据手册；2026-11-23 查证）：

| 命令 | MPU-401 语义 | FMD 发的值 |
|---|---|---|
| `$FF` | RESET | 装载/停止时 |
| `$32` | 复位后的初始化 | 装载/停止时 |
| **`$C2`** | **SET TIMEBASE**：`$C2-$C8` = 48/72/96/120/144/168/192 tick/拍 | **`$C2` → 48** |
| **`$E0`** | **SET TEMPO**（BPM，8–240） | 曲头 BPM |
| `$E1` | SET RELATIVE TEMPO（`$40` = 1/1，单位 1/64） | 变速时（`0xE7` 处理函数） |
| `$E2` | GRADUATION（速度渐变） | 渐变时 |
| **`$E7`** | INT×4 / CLOCK TO HOST（每 host clock 几个内部时钟） | **`$04`** → 4/4 = 1 |
| `$95` | CLOCK TO HOST: ON | 打开 `$FD` 时钟输出 |
| `$FD` | 时钟字节本身 | `INT 0E` 读到的那个 |

```
每拍 tick 数 = timebase × 4 / $E7 值
FMD：48 × 4 / 4 = 48
```

`$E0` 的上限 240 BPM 正好对上驱动里 `0x3C00`（= 240×64）这个钳制常数——两条独立线索互相
印证。**别的驱动可能发 `$C3-$C8`（72–192）或不同的 `$E7` 分割**，所以导出器不写死 48：
`build/_fmd_export.py: parse_timebase()` 从 init 序列读 `$C2-$C8` 和 `$E7 <n>` 换算，
SMF 的 TPQ 直接取这个值（driver tick : SMF tick = 1:1）。


**实测验证**（六首、80–186 BPM，用 loopMIDI 录 HOOT 的事件表逐事件对齐；配对 = 同通道
同音高、时间差 ≤50 ms，斜率用最小二乘拟合）：

1. **六首斜率全 = 1.000**：

   | 曲 | BPM | 导出 | HOOT 实测一遍 | 配对 | 斜率 | 残差中位 |
   |---|---|---|---|---|---|---|
   | AMA2_001 | 80 | 60.0 s | 60.0 s | 469/688* | 1.0002 | 8 ms |
   | AMA2_000 | 94 | 42.4 s | 42.4 s | 919/919 | 1.0001 | 6 ms |
   | AMA2_003 | 108 | 48.87 s | 48.88 s | 454/454 | 1.0003 | 6 ms |
   | AMA2_004 | 125 | 23.26 s | 23.26 s | 613/613 | 0.9999 | 4.5 ms |
   | CHAOS | 168 | 51.41 s | 51.3 s | 919/919 | 1.0001 | 6 ms |
   | AMA2_007 | 186 | 30.95 s | 30.97 s | 350/624* | 1.0006 | 18 ms |

   \* 这两首的抓取本身有丢事件/时间戳抖动（配对率 68% / 56%），但**配上的那部分斜率仍是
   1.000**，不影响结论。6912 tick ÷ 51.41 s = 134.4 tick/s，168 BPM = 2.8 拍/s ⇒ **48.0 tick/拍**。
   同一系数下 `AMA2_000` = 3192/48 = 66.5 拍 × 60/94 = **42.4 s**。
2. **40.79 s 的 HOOT WAV 也自洽**：它其实覆盖了 42.4 s 那首的 96%，自相关主峰
   0.32 s / 0.64 s = 24 / 48 tick = 八分 / 四分音符；鼓轨间隔 24 tick = 八分音符脉冲。
3. 数据网格：所有 note-on 落在 12 tick 的整数倍上 = 十六分音符网格，合理。

> 走过的弯路（记下来省下次）：先按「和 HOOT 听感一致」定成 12 tick/拍（其实拿
> “播两遍的文件”比“播一遍的 HOOT”），又按 WAV 自相关定成 24（把 24 tick 当成八分）。
> **无限循环的曲子，只有“逐事件对齐”能定标**；比时长、比听感都会被循环数骗。
> 最后一步是查 MPU-401 命令表：`$C2` 把 48 直接写在命令里，前面所有拟合都是在猜一个
> 代码里明写着的东西。

## 四、数据格式（4 字节记录）

`.MMD` / `.GMD` / `.GS` 是同一种加密格式：**整文件 XOR 0xA5**（驱动读盘后自己解）。
只有 `.MD` 是明文（另一种布局，未处理）。

```
+0x00 u8  tempo(BPM)  +0x01 u8 移调  +0x02 16 × (u16 偏移, u8 key, u8 ch)  +0x50 曲名
```

装载后驱动在 `0xE64`（A 代）/ `0xEBC`（B 代）建 **18 条轨的轨道表**，每项 0x30 字节：
`+0 u16 数据段 +2 u16 循环起点 +4 u16 当前偏移 +0x27 启用位 +0x28 倒计时 +0x29 通道 +0x2A ...`。
事件流每条 **4 字节 `[cmd][dur][p1][p2]`**：`cmd < 0x80` 是音符（dur=到下一事件的 tick 数，
p1=门长、p2=力度）；`0x80-0xEF` 是 MIDI 类消息；`0xF9/F8` = 循环开始/结束、`0xFE` = 结束、
`0xFD`/`0xFC` = **同步/节拍标记**（实测：跳过该分支后鼓轨才完整、9 种音高全出，见 FMD-BUILDS §34.9；**不要当跳转**，按跳转处理会把鼓轨拉回开头）。另注意同名不同物：板子数据口读到的 `0xFD` 是时钟字节。

## 五、导出流程（`build/_fmd_export.py`）

1. 装驱动（含 `shell_patch` 清 B 代 `[0x1E]`）；
2. 有 `.TON`/`.DAT` 的包先走 `AX=0201` 送音色（目前只在 ama2 系验过；GS 包没有音色文件，跳过）；
3. `AX=0100` 送歌曲缓冲 → `AX=0300` 播放；
4. 逐 tick 调 `INT 0E`，把 `0xE0D0` 的字节按 tick 记下来；`0xE0D2` 的命令另记
   （记录 `0xE0`/`0xE1` 的完整序列，最后交给 `tempo_map()` 生成 timed tempo map）；
5. **结束判定（B 代 batch 用）**：按优先级 ①所有非空轨 `[bx+4]` 指向 `$FE` → `end=fe`；
   ②所有活跃轨 `(seg, loop, cur, en)` 同时回到同型状态 → `end=loop`，取一轮；
   ③跑满 `max_ticks` → `end=cap`，打警告、标 `truncated`，**不算 ok**。
   旧的 A 代 `round_mode=legacy` 仍用「同目标集合再次出现 + 间隔 ≥2000 tick」，
   保留为历史路径，不影响 B 代。下面几条是 A 代 legacy 的细节：
   - `AMA2_000`：3192 / 6264 两次同目标 ⇒ 截 3192（和 MIDI 流自相关 P=3072 对得上）；
   - **OP/ED 是一次性曲子**：确认不到整曲循环时，以**最后一个 MIDI 事件**为终点，不做循环截断。
     `OPENING.MMD` 就是这样：26799 tick / **698 秒**（安芸出 的炫技曲，PC-98 时代十来分钟的 OP
     是正常的，别当成 bug 去截断）；
   - ⚠ 反面教材：早先的「≥2 轨回跳就截」「≥5 轨回跳 +600 tick 就停」都被段落交界骗过，
     把 OPENING 截成过 7.5 秒 / 113 秒。
   - ⚠ **抓取预算不能只按静态走表**：计数循环会让静态长度严重偏小
     （`DHILTHY`/`AMA2_006` 静态只有 770 tick，真实循环在 6528），于是「2.5×静态」的预算
     根本到不了循环点，会截出 6.5 秒的短版。预算要带下限（`BUDGET_MIN`，默认给 6000，
     定向复核时调 16000 能确认 6528 的循环）。
   - ⚠ **同一曲名多扩展名要分开命名**：`AMA2_000.MMD` / `AMA2_000.GMD` 是两套编曲
     （长度可以差 10 倍，如 `AMA2_009` 93 s vs 9.5 s），按「去扩展名」命名会互相覆盖。
   - ⚠ **F8 是带次数的循环，不是无条件跳转**（反汇编 `0x60xx` 那段）：
     `mov dh,ah`（AH = 重复次数，**0 = 无限**）→ `dec al` / `mul 6` → `inc [si]` /
     `cmp al,dh` / `je 结束` → `mov bp,[si+2]`（目标）→ `mov [bx+2],ax`（回到目标）。
     所以 F9/F8 是**循环栈**（每项 6 字节），各轨可以有各自不同的次数和周期。
   - **「多段独立循环」型曲子**（典型：`OPENING.MMD`）：9 条轨各有计数循环
     （次数 2/21/2/2/4/12/16/12/6，周期 2626/1706/2829/99/2058/1688/1696/1688/16376），
     另 7 条在 tick 254 就 `0xFE` 停了，**整曲没有统一循环点**。
     这种曲子截到「最长轨的第一个周期」（= 静态走表长度，OPENING 是 16376 tick / 426.5 s），
     标注 `truncated at longest track cycle; multi-loop by design`；
     完整长度要按第 8 轨 6 次循环算 ≈ 98256 tick（42.6 分钟），没有实操价值。
6. 写 SMF：TPQ 取驱动 init 里的 timebase（`$C2-$C8`，FMD 是 48），driver tick 与 SMF tick
   **1:1**；tempo 不再是单一曲头 BPM，而是 `tempo_map()` 生成的完整 timed map
   （`$E0` 基准 + `$E1` 相对速度），末尾补 all-notes-off。
7. 覆盖护栏：新导出时长 < 旧文件的 50% 时不覆盖，改写 `X.suspect.mid` 并在报表里标 `suspect`。

## 六、历史未解记录（2026-11-25，已冻结）

> 以下为当时状态，已被顶部 2026-11-26 正式结档取代；保留作为踩坑记录。
> B 代、FMD5、FMD7 的最终结果见 [`FMD-STATUS.md`](FMD-STATUS.md)。

**B 代（`FMD.EXE` 1.71/1.72）已在 `AMA4_015` 上打通**：斜率 1.00024、窗内 2691 vs 2696 音、
鼓 9/9（含 42）、密度 0.88；1.71 与 1.72 输出相同。根因不是板子/音源槽，而是播放期
code hook 让 `cmp` 丢 CF（[`FMD-BUILDS.md`](FMD-BUILDS.md) §37）。
**批量已跑：237/255 首 ok，11 首 `end=cap` 待修**；TLOVE_02/08、FMD5 仍未收口，
台账见 `build/audit/fuga_ledger.csv`。

**FMD5（`FMD5.EXE`）仍差通道铺开**：MAZE00 2085 / MAZE01 1658 音
（原 1716 / 1842；HOOT 3224 / 2363），ch3–ch7 198 条/通道（HOOT 339），下一步单独查。
FMD5 的 HOOT 录音已登记：`D:\music\maze00_hoot.mid` / `maze01_hoot.mid`（约 58 s 部分窗口）。

**审计台账（第一版）**：414 行（A 130 / B 255 / FMD5 29）；`no-ref` 382、`empty` 14、
`re-pass` 11、`re-density` 5、`ok` 1、`re-tempo` 1。`no-ref` 不是失败：
修完已知问题后重导，新旧导出无差别即按回归通过；详见
[`AUDIT.md`](AUDIT.md) §七与 `build/audit/README.md`。

以下仍**未解但没有投入价值**（记录备查）：

- **`.MD` 明文数据**（bunnou2/ama2m 的一部分）格式未处理。
- **`.TON` 音色文件**（CM-64 映射表，22601 字节）的喂法未接线，MT-32 那批现在只是「音符对、
  音色可能是默认值」。
- **A 代批量**：`build/_fmd_export.py` 已能整首导出并验证（`AMA2_000` 42.4 s、`CHAOS` 51.4 s），
  36 + 34 首已落盘，可作为交付基线。

## 七、脚本

| 脚本 | 用途 |
|---|---|
| `build/_fmd_play3.py` | 板子模型 + 完整壳流程（0201→0100→0300→tick） |
| `build/_fmd_export.py` | 批量导出：装驱动、循环检测、写 SMF |
| `build/_fmd_cmds.py` | 抓 `0xE0D2` 命令序列（两代对照） |
| `build/_fmd_loopstats.py` / `_fmd_loopcheck.py` | 循环点/周期检查（偏移回跳 vs 流自相关） |
| `build/_fmd_dumpdrv.py` / `_fmd_mdis.py` | dump 常驻镜像、线性反汇编 |
| `build/_fmd_wav.py` | 读 HOOT 的 WAV 长度（定标用） |
| `build/_fmd_batch_all.py` | 整批导出（按 HOOT 标题建目录、按包读启动参数） |
| `build/_fmd_report.py` | 汇总 `_fmd_all_report_*.csv` → `_INDEX.md` / `_ALL.csv` |
| `build/_fmd_hootalign.py` | 与 HOOT 抓取逐事件对齐（斜率/残差） |
| `build/_fmd_packlist.py` | 从 HOOT XML 生成本驱动包表（标题/驱动/启动行） |

## 八、导出成果（2026-11-23 冻结，同日结案）

> **交付口径（重要）**：只有 **A 代**那 **70 个文件**（Amaranth II GS 36 + MT-32 34）算交付，
> 已与 HOOT 抓取逐事件对齐（斜率 1.000）。下表其余目录（ama4/amakh/venus/image2/fgsel 等）
> 是**同一套 harness 跑出来的近似结果，未通过结构校验**（AMA4_015 实测音高相似度 0.008），
> 一律标 **unverified**，**不要当成果引用**。`fmd_synth/` 里补过 program 的 41 首同理。

`build/hootcap/fmd/<HOOT 标题>/`，共 8 个目录 / 169 个文件；
其中 **70 个已验证**、99 个 unverified。索引见 `build/hootcap/fmd/_INDEX.md`，明细 `_ALL.csv`。

**能导出**（A 代 FMD9/FMD5/FMD13 的一部分，以及几个 FMD.EXE 构建）：

| 目录 | 曲数 | 时长 |
|---|---|---|
| Amaranth II(GS) | 36 | 57.8 min |
| Amaranth II(MT-32) | 34 | 42.6 min |
| Amaranth IV(GS) | 23 | 140.5 min |
| Amaranth KH | 18 | 53.9 min |
| VENUS(GS) | 15 | 23.7 min |
| イマージュ2(MT-32) | 14 | 18.6 min |
| 風雅セレクション カルカッタ | 11 | 34.2 min |
| 風雅セレクション メイズクエスト | 18 | 56.7 min |

**仍导不出的，按原因分三类**（都不是重试能解决的）：

1. **B 代驱动装得上但不出声**：`ama2m_98`(FMD13)、`farce`、`hiragi`、`momoko`、`mug-r`、
   `papa`、`reno`、`tlove12`、`yumecol`。根因在 `FMD.EXE` 的建表/音色初始化
   （`AMA4`/`AMAKH` 的 program 问题同源，已在 HANDOFF 记过）。
2. **装不上**：`ama3_98`（B 代安装逻辑）、`ayayo2_98` / `outside_98`（`-M6 -N0` 仍不装）、
   `bonnou2_98`（驱动是 `FMIDIDRV.EXE`，不是 FMD 家族）、`image1_98`（数据只有 `.MDI`）。
3. **个别曲**：`VENUS` 4 首、`AMA2_98` 的 `FGTTL`/`P0002`（`.GMD` 版）没重导。

**已记录、不再重试**：EDGE、SWORD DANCER 増刊号'93（TGL 壳）。

## 驱动 build 差异（2026-11-23 冻结后补充）（2026-11-23 晚发现，最重要的一条）

> **2026-11-23 复查：本节旧结论已推翻。** 4857 与 4969 是同一驱动的相邻版本
> （**1.72** / **1.71**），**引擎、AH 分派表、`0x0100` 装载路径逐字节相同**；
> 「入口地址不同 = API 不同」不成立（旧文里「4969 是 `1010:0056`」是把 A 代的数抄串了，
> 4969 与 4857 都是 `1010:003F`）。完整证据链见
> [`FMD-BUILDS.md`](FMD-BUILDS.md)。

FMD.EXE 的哈希分组仍然可用，但**它只说明"用了哪个 build"，不说明"卡在哪一层"**：

| 包 | FMD.EXE | md5 前 8 位 | 内部版本 | INT D3 | 导出 |
|---|---|---|---|---|---|
| reno / momoko / papa / tlove12 / yumecol / farce / hiragi | 4857 | `699a8a5e` | 1.72 | `1010:003F` | ❌ |
| ama4_98 / amakh_98 | 4969 | `991dbe8d` | 1.71 | `1010:003F` | ✅ |
| mug-r_98 | 5365 | `de5bf6f7` | 1.61 | `1010:003C` | ❌ |
| venus_98 | 4601 | `f06ac87f` | 1.51 | `1010:003B` | ✅ |
| image2_98 | 5248 | `3dfd0981` | （无版本串，A 代形态） | `1010:0056` | ✅ |

两版之间的实际差异只有三处（常驻镜像 24576 字节里 23597 相同）：

1. 安装器 `0x1BA1` 多一条 `add bx,0x0E` —— 1.72 比 1.71 **多要 14 段（224 字节）DOS 内存**；
2. `Version 1.71→1.72` 与 `-?` 帮助文本；
3. 运行时 loader 副本里的 3 个字节（未解明）。

**所以剩下的不是"1 个 build 差异"，而是"数据 / 命令行参数 / 安装环境"三选一。**
下一步与复现脚本：见 [`FMD-BUILDS.md`](FMD-BUILDS.md) §7、§8。

### 开工前必读（别上来就冲）

1. **先做 build 哈希对照**（`build/_lead_fmd_hashes.py` 可复现），不要按“包”逐个试；
2. **判"API 差异"要 dump 常驻镜像逐字节比**（`build/_fmd_dumpdrv.py <pack>` +
   `build/_lead_fmd_fulldiff.py`）——**文件大小差常常只是 MZ 头**；
3. **对比架构差异**：`INT D3` 入口 → **AH** 分派表（`0x73`，18 项 `0x00–0x11`，
   索引是 AH 不是 AL）→ `0x0100` 装载路径 → 轨道表初始化（18 项 / `+0x27` 启用位）；
4. **已知坑，别重踩**：
   - `E0`/`E7` 的参数走**数据口** `0xE0D0`，不是命令口；
   - MIDI 数据前有命令 `D0` 前缀；
   - 复位刷屏：事件数 >20 万判 bad；
   - 音符数 0 不要写文件（写 `.empty`）；
   - OP/ED 默认一次性；多轨独立循环没有整曲终点（OPENING 按 16376 tick 截）；
   - EDGE / SWORD DANCER 増刊号'93 需要 TGL 壳（见「TGL 的 FMP 壳」）；
   - MPU-401 `$C2` timebase=48 已定案，**不要重推**。


---

## （历史）结档说明（2026-11-24，已被 2026-11-25 更新取代）

> 2026-11-25：B 代根因是播放期 code hook 污染 `cmp` 的 CF，拆掉后 1.71/1.72 已在
> `AMA4_015` 上对齐 HOOT（`FMD-BUILDS.md` §37）。下面这段保留为历史。

**风雅（FUGA）驱动：逆向难度过大，结档归档。** 只交付 A 代，其余三条线停止投入。

| 线 | 状态 | 卡点 |
|---|---|---|
| **A 代（FMD9 / FMD13）** | ✅ **可交付**（Amaranth II GS 36 + MT-32 34，斜率 1.000） | — |
| 1.71（B 代） | ❌ 搁置 | `F8` 循环计数的运行时真值无法可信观测（三次观测均为 hook 噪声） |
| 1.72 | ⏸ 暂停 | `0x0100` 的 `call 0x15DA` 落在镜像全 0 区，需执行当刻的活镜像 |
| FMD5（fgsel） | ❌ 未过 | 音符只有 HOOT 的 53%/78%，ch3–ch7 应五条等长通道却只铺开 2–3 条 |

**共同缺口**：驱动把一条声部铺到多个通道（音源槽 / 通道分配）的机制没有复刻。
B 代与 FMD5 的失败是同一个形状，不是记录解析问题——音符内容对得上，是分发不对。
重启任一条线之前，必须先解决这一点，否则会重演「修一个症状、长出一个新症状」。

**不可引用的产物**：`build/hootcap/fmd/` 其余 99 个文件、`build/hootcap/fmd_synth/` 41 首、
`AMA4_015_1.71_fixed.mid`、`fgsel_MAZE0{0,1}.mid` —— 全部标 **unverified**。

完整依据见 `docs/FMD-BUILDS.md` §31–§36（DE 静默、A 代判决翻转、`.MD`/0201 死路、
鼓轨锁死、混轨真身、1.72 与 FMD5 的实测数字），方法论见 内部审查清单（不随库发布）。

---

## 九、2026-11-26 A/B 代当前收口（以本节为准）

> 这一节替代前面所有“A 代已交付 / B 代未收口 / 按旧 SHA 验收”的旧口径。
> 旧 SHA 只保留为回归参照，不再是验收判据。

### 9.1 验收口径

A 代每首只认两种停止方式：

| end | 判据 | 验收 |
|---|---|---|
| `pass` | 所有曾经启用的轨 `en=0`（驱动不再送数据，硬件尾走完） | 通过 |
| `loop` | `depth=1` 的外层循环回跳一次 | 通过 |
| `cycle` | 前段 + 无限循环尾：全轨 `(seg,loop,cur)` 首次重复；若 loop 锚点每轮更新，退化 `(seg,cur)` | 通过 |
| `fe` | 所有非空轨 `cur` 指向 `FE` | 仅作为自然结束记录 |
| `cap` | 跑到 max tick 仍未判定 | **未通过**，必须补跑/定位 |

`loop` 必须取**外层**：轨道表 `[bx+0x2B]` 的 depth：

- `depth=1`：外层，允许作为 loop 停止点；
- `depth>=2`：内层乐句，不能当整曲循环；只能作为 fallback，排序靠后；
- all-mode 的循环签名也把 depth 纳入，避免同 cur/不同内层深度误判。

`pass` **不等 FF/32**。ENDING1 板卡日志已确认末尾没有 FF/32；停止由
“驱动停止送数据 + 板卡走完最后 gate/队列”完成。

### 9.2 A 代轨道表：0xE64 与初始化代码

A 代（FMD9.EXE）轨道表偏移不是猜的，反汇编运行时初始化代码确认：

```text
CS:0x1A7  BF 64 0E          mov di,0xE64
CS:0x1AA  2E A1 07 00       mov ax,cs:[7]
CS:0x1AE  BE 01 00          mov si,1
CS:0x1B1  89 05             mov [di],ax
...
CS:0x1EA  83 C7 30          add di,0x30
CS:0x1ED  46                inc si
CS:0x1EE  83 FE 12          cmp si,0x12      ; 18
CS:0x1F1  76 BE             jbe 0x1B1
```

因此：

```text
A 轨道表 = CSBASE + 0xE64
18 项 × 0x30
```

B 代仍是 `CSBASE + 0xEBC`，两者不能混用。

轨道项字段（A）：

```text
+0x00 u16 seg      数据段
+0x02 u16 loop     循环锚点
+0x04 u16 cur      当前偏移
+0x27 u8  en       启用/结束
+0x28 u8  countdown
+0x29 u8  channel
+0x2B u8  depth    循环栈深度
```

A 的入口 `CS:0x43` 签名只适合找文件副本；HOOT 运行时表要用上面的
`0x1A7` 初始化代码签名定位，命中点 `-0x1A7 = CSBASE`，再 `+0xE64`。

### 9.3 HOOT A 代实采结论

用同步捕捉器（t=0 取 `cur` 第一次变化）采 OPENING：

- 146 s：0–8 活跃，9–17 `en=0`；不是“0–8 对齐、其余在走”；
- 18 条轨的 `seg` **全程唯一**：没有播放期换段；
- 自然结束：329.012 s，0–8 全部 `en=0`；
- 之前看到的 `9859→9B7D`、146 s 只有 0–6 活跃，来自错误表/时间未对齐，已撤回。

### 9.4 tempo：$E0 真值不是 120

OPENING 板卡日志：

```text
$E0 = 48
$C2 timebase = 48
$E7 = 4
$E1 = 42 / 160 / 169
```

实际 tempo 链：

```text
48 BPM  @ tick 0
31 BPM  @ tick 1248   (48×42/64)
120 BPM @ tick 1440   (48×160/64)
126 BPM @ tick 3864   (48×169/64)
```

**120 只是 HOOT PKL→MIDI 脚本的固定网格常数，不是 `$E0`。**
OPENING 最终 31033 tick 得到约 335–337 s；不能拿“tempo 事件 1 个 / 120”当判据。

### 9.5 ENDING1 与“最后一个 note + 2 秒”

ENDING1 GS 板卡日志：

```text
$FF / $32：只在 tick 0（初始化）
$FD clock：22734 条，tick 0–22733
$D0 数据：持续到 tick 22733
最后 note：tick 22731
末尾 FF/32：没有
```

说明停止是硬件尾，不是主机 stop 命令。

最终 ENDING1：

```text
end=pass
228.482 s
最后 note 226.478 s
尾部 2.004 s
最后 15 秒 259 音
最后 2 秒 24 音
```

所以 **228 不是被长尾巴撑长的**，尾部本来就只有约 2 秒。
`end=pass` 仍统一执行“最后一个 note + 2 秒”，用于去掉偶发长尾；
该规则对 ENDING1 几乎不改变（228.62→228.48）。

### 9.6 A 代全量结果（101）

表：`build/audit/A_end_table.csv`

```text
总数 101
loop 87
pass 13
placeholder 1（VENUS_00，空曲/占位，HOOT 播放列表不含）
```

关键值：

| 曲 | end | dur | notes |
|---|---|---|---:|
| ama2s_98/AMA2_001 | loop | 59.98 | 688 |
| ama2s_98/ENDING1 | pass | 228.48 | 3360 |
| ama2s_98/OPENING | pass | 336.90 | 9461 |
| ama2_98/OPENING | pass | 336.90 | 9461 |
| ama2_98/ENDING1 | pass | 228.482 | 3360 |
| ama2_98/ENDING2 | pass | 199.005 | 3690 |

MT-32 `ENDING1` / `ENDING2` 已于 2026-11-26 验收通过；源文件必须取 `.MMD`（见 §9.11）。

OPENING 对参考 `D:\music\AMA2_OPENING.MID` 334.406 s 的差为
**+2.494 s（+0.75%）**，仍在 2% 内；音符 9461，参考 9459。

A 的 pitchwheel 去重必须关闭（`pw_dedup=False`）才能复刻旧 A 的
`AMA2_000` 字节；旧 A SHA 只作参照。

#### 9.6.1 结档后复核：static/内层 loop 误停（2026-11-26，待 P0–P4 重判）

对比旧 `build/hootcap/fmd/`，发现 `DHILTHY` 等被 `static`/depth≥2 的
“最先满足判据”截短。已临时改取 `no_loop` 自然长度，但静态判定链尚未完成：

| 曲 | 旧 | 临时 |
|---|---:|---:|
| DHILTHY / AMA2_006 | 55.1 / 55.7 s | 55.73 s（tentative） |
| AMA2_012 | 103.1 s | 108.11 s（tentative） |
| AMA2_013 | 61.7 s | 93.54 s（tentative） |
| AMA2_020 | 31.75 s | 60.64 s（tentative） |

**重要**：`AMA2_006` 静态是无限曲：`L=1200, P_out=10752, C=11952`。
所以 55.73 s 仍是预算截断，不是终点；最终以 P0–P4 为准。

**经验：`static` 和 depth≥2 不是可靠结束判据，必须优先查自然结尾。**

### 9.7 B 代全量结果（248 + AMA3 GS 24）

表：`build/audit/B_end_table.csv`

```text
B 基线 248
loop 218
pass 8
cycle 1
fe   21
cap   0

另：AMA3 GS 24 首（build/hootcap/fuga-b/ama3s_98/）
loop 12 / cycle 10 / fe 2
```

关键值：

| 曲 | end | dur | notes |
|---|---|---|---:|
| tlove12_98/TLOVE_08 | fe | 197.017 | 19006 |
| tlove12_98/TLOVE_16（LOGO） | pass | 4.24 | 32 |
| ama3_98/AMA3_022 | loop | 438.547 | 20809 |
| oerstd98/OERS_018 | cycle | 104.058 | 3377 |
| ama3s_98/AMA3_000 | fe | 16.091 | 178 |

TLOVE_16 旧 JSON 标 `loop 840` 是早先长抓的元数据；实际是 `pass` 短曲。
TLOVE_08 的末 15 秒问题已按 coda/channel6 窗口接受，`end=fe`。
OERS_018 已按 cycle 收口，B 基线 cap=0；AMA3 GS 是额外 24 首，不改变 248 基线。

### 9.8 旧 SHA 回归

- A：`delivered_v1_fuga_a.sha256` 101 个；新全量中与旧 SHA 相同 **6**、不同 **95**；
- B：`delivered_v1_fuga_b.sha256` 248 个；相同 **228**、不同 **20**；
- 不同主要来自 end 口径（旧静态截断/旧 loop 点）、OPENING、TLOVE_08/16 和 cap 补跑。
- 因此“旧 SHA identical”不再作为完成条件；A 用 `end/dur/notes`，B 用 `end/dur/notes`。

### 9.9 产物与脚本

| 用途 | 路径 |
|---|---|
| A 全量导出 | `build/_fuga_reexport_a.py` |
| A 表/报告 | `build/audit/A_end_table.csv`、`build/hootcap/fuga-a/<pack>/_report.csv` |
| B 全量导出 | `build/_fuga_reexport_b.py` |
| B 表/报告 | `build/audit/B_end_table.csv`、`build/hootcap/fuga-b/<pack>/_report.csv` |
| pass 尾部规则 | `build/_trim_pass.py` |
| A 深度/循环探针 | `build/audit/opening_tracks_146s.txt`、`build/audit/hoot_a_aligned.md` |
| ENDING1 板卡诊断 | `build/audit/ending1_board.jsonl`、`build/audit/ending1_board.md` |
| 旧 SHA 基线 | `build/audit/delivered_v1_fuga_a.sha256`、`..._b.sha256` |

### 9.10 结档说明（不是未完成项）

1. `VENUS_00`：HOOT 播放列表不含，按制作方占位/空曲处理；A 记为 `placeholder`，不计入 448 首成品。
2. `OERS_018` 已按 `end=cycle` 收口：循环起点 3144、周期 7680、cutoff 10824，104.058 s / 3377 音；B 基线 cap=0。
3. FMD5 已在 `build/hootcap/fmd5/` 完成 29 首（loop27/fe2），属于风雅线，不再是“排除未做”。
4. EMD-98（ayayo2）/ ABIKO-98（sematte）已移出风雅，见 `drivers/emd98`、`drivers/abiko98`。
5. 所有技术结论以本节和对应 `build/audit/` 原始产物为准；历史“结案/未收口”文字冻结。

### 9.11 MT-32 尾巴根因：源文件选错 variant（2026-11-26）

`ama2_98`（MT-32 包）**每首都有 `.GMD` 和 `.MMD` 两份**；`ama2s_98`（GS）只有一份。
旧 MT-32 交付用的是 **`.MMD`**。

之前 A 全量脚本按 zip 顺序取第一个候选，结果把 **`.GMD`（GS 编排）** 当成 MT-32 导出，
所以只有 MT32 侧出现“额外尾巴/变速错位”。

实测：

| 曲/源 | 时长 | 音符 | SHA256 前缀 |
|---|---:|---:|---|
| `AMA2_000.GMD` | 43.165 | 533 | `69691BD5…` |
| `AMA2_000.MMD` | 42.420 | 533 | `8BD26EE7…`（=旧 MT-32） |
| `ENDING1.GMD` | 280.754 | 2369 | `2EA79219…` |
| `ENDING1.MMD` | 228.621 | 3360 | `B8DF3A0E…` |
| `ENDING2.GMD` | 242.134 | 3695 | （旧新差异来源） |
| `ENDING2.MMD` | 197.185 | 3690 | （旧 MT-32 接近） |

修正：`build/_fuga_reexport_a.py` 对 `ama2_98` 强制优先 `.MMD`。
重导后 MT32 `AMA2_000` = `8BD26EE7…`，与旧交付逐字节相同；
ENDING1/2 也回到 MT32/GS 同构的 228.48 / 199.00 s（末尾 +2 s 规则后）。

**纪律：一个包有多个同 stem 源文件时，必须按机种/旧交付选定 variant，不能取 `cand[0]`。**

#### 9.11.1 不是驱动 type 模式读错源

**不要写成“驱动的 type 模式读错了源”。** 实际链路是：

```text
包内同时有 ENDING1.GMD / ENDING1.MMD
→ 导出器按 cand[0] 选了 .GMD
→ 把 .GMD 的歌曲缓冲交给 FMD9 驱动
→ 驱动按它收到的缓冲正常播放
→ 产出是 GS 编排，不是 MT-32 编排
```

驱动没有“自己选错 type”；它只是播放了导出器提供的缓冲。
错误发生在**导出器源文件选择**，在驱动执行之前。

正确的是：

```text
ama2_98（MT-32）→ 选 .MMD
ama2s_98（GS）  → 选它自己唯一的那份
```

修正后 `AMA2_ENDING1/2` 两首 MT-32 验收通过：

```text
ENDING1 228.482 s / 3360 音
ENDING2 199.005 s / 3690 音
```

它们的旧 MT-32 文件仍是更短的旧静态截断（221.795 / 194.719 s），
但**新文件的源 variant 与旧 MT-32 同族**，不再含 GMD 的额外尾巴/变速错位。

## 十、FMD5 初查（2026-11-26）

### 10.1 轨道表基址

FMD5 的轨道表真实基址：

```text
CB + 0xD1A
```

`find_track_table()` 之前返回 `CB + 0xCEA`，早了一个 0x30，第一项是垃圾：

```text
0xCEA: seg=33C0 loop=8BD2 cur=F7CD en=A6 ch=EB dep=10
0xD1A: seg=4000 loop=009C cur=0040 en=FF ch=99 dep=1
```

已在 `build/_fmd_export.py` 加 `fix_table_base()`；A/B 首项合法，不受影响。

### 10.2 MAZE 初测

| 曲 | end | loop | 时长 | 音符 |
|---|---|---|---:|---:|
| MAZE00 | loop | period 4608 / start 24 | 32.290 s | 1732 |
| MAZE01 | loop | period 6144 / start 24 | 42.778 s | 1705 |

### 10.3 HOOT 参照不是一轮

```text
maze00_hoot.mid 58.488 s / 3224 音  ≈ 1.8 轮
maze01_hoot.mid 57.614 s / 2363 音  ≈ 1.35 轮
```

按一轮缩放后，ch3–ch7 分布接近 HOOT；旧记录中“FMD5 五通道只铺2–3条”的结论
至少受**时长口径**污染，不能直接当 fanout 缺失。

已收口（2026-11-26）：

- 24 tick 是 harness 前导；产品从曲首开始，不再按 loop_start 平移；
- 按“一轮 loop”交付；
- 29 首已全量重导：`build/hootcap/fmd5/maze` 18 + `calc` 11；
- 统计：loop 27 / fe 2 / cap 0；
- MAZE01 的 ch2/5 与 ch4/7 约 10% 相位差异保留为参照说明，不再阻塞交付。

详见 `build/audit/fmd5_probe.md`。

### 9.12 AMA3 GS / MT-32 双版本（2026-11-26 补）

`ama3_98` 包每首同时有 `.GMD` 和 `.MMD`，但这里的对应关系与 AMA2 不同，
必须看 SysEx，不能只看扩展名：

```text
.GMD = MT-32 版本：SysEx 41 10 42 12 ...（Roland MT-32 DT1）
.MMD = GS 版本：  SysEx 41 10 16 12 ...（Roland GS DT1）
```

现有 `ama3_98/` 24 首是 GMD/MT-32；补导的 GS 版单独放在：

```text
build/hootcap/fuga-b/ama3s_98/  24 首
```

GS 24 首统计：loop 12 / cycle 10 / fe 2 / cap 0。

**纪律：AMA2 与 AMA3 的扩展名/版本对应不可互换；先读 SysEx 判定机种，再选源文件。**

### 10.4 FMD5 一轮产品（2026-11-26 历史；当前见 FMD-FINAL-NOTES）

已按“包含 intro + 一轮 loop”导出，**不按 loop_start 平移**（否则会截掉开头）：

```text
build/hootcap/fmd5/maze/   18 首
build/hootcap/fmd5/calc/   11 首
```

统计：

```text
总数 29
loop 27
fe    2（MAZE18、CALC_VM4）
cap   0
```

MAZE00/01：

| 曲 | end | ticks | dur | notes |
|---|---|---:|---:|---:|
| MAZE00 | loop | 4608 | 32.290 s | 1732 |
| MAZE01 | loop | 6144 | 42.778 s | 1705 |

FMD5 通道分布（MAZE00）：

```text
ch1 144 ch2 152 ch3 192 ch4 176 ch5 176
ch6 176 ch7 176 ch8 144 ch9 396
```

表：`build/audit/fmd5_end_table.csv`  
摘要：`build/hootcap/fmd5/_summary.md`

HOOT 的 58 s 只是多轮窗口，不能当一轮时长；当前按一轮交付。
MAZE00/01 的循环相位和开头截断复核已完成（§10.5），不再作为待办。

### 9.13 导出前源文件结构预检（2026-11-26）

以后所有 FMD 包在导出前先跑：

```text
python build/_fmd_source_audit.py <pack...>
# 输出 build/audit/fmd_source_audit.csv
```

按 stem 看：

```text
exts        .GMD/.MMD/.MD/.MDI/.MI/.GS/.FM/.EMI/.MUS/.ONS
sizes       各扩展名大小
headers     前 12 字节
```

已踩过的坑：

```text
AMA2/AMA3: .GMD 与 .MMD 是不同机种/编排
image1:    .MD 是数据，歌曲入口是 .MDI
p_club:    .MD 是数据，歌曲入口是 .MI
sanina:    .GS/.FM/.LA
ayayo2:    .EMI
sematte:   .MUS/.ONS
```

**规则：先观察源结构，再选扩展名/机种/profile；不得取 `cand[0]` 猜。**

## 十一、当前总表

请优先看 [`FMD-STATUS.md`](FMD-STATUS.md)：按 build 列出已交付、特殊和未处理项。
本节之前的 §九/§十保留为细节记录。

### 10.5 FMD5 开头截断复核（2026-11-26）

对 29 首当前 `build/hootcap/fmd5/` 产物与旧产物首音比较：

```text
没有任何新首音晚于旧首音 0.12 s。
MAZE00 新旧首音均为 0.167597 s。
CALC_VM3 新首音 0.272 s，旧 0.793 s（新更早，不是截断）。
```

第一次 FMD5 导出曾按 loop_start 平移，确实截掉 intro；第二次导出已改为从曲首开始。
当前只剩首段配器/密度差异，不是开头缺失。

## 十二、构建 / HOOT 包名 / 表地址

详细对照已单独整理：

```text
drivers/fugam/docs/FMD-BUILD-MAP.md
```

它按 **build + HOOT 包 + 日文原名 + 表 offset + 源文件入口** 记录，
并标出哪些同名 `FMD.EXE` 其实不是同一代码。

核心区分：

```text
FMD9 4774                 0x0E64
FMD13/FMD9G 5301          0x0F0F   （同 hash）
FMD.EXE 4341 oerstd       0x0CD0
FMD.EXE 4601 venus        0x0CB8
FMD.EXE 4773 ama3         0x0C9E
FMD.EXE 4857 七包         0x0EBC
FMD.EXE 4969 三包         0x0EBC
FMD.EXE 5248 image/p_club 0x0E70
FMD.EXE 5365 mug-r        0x0D18
FMD14 4341 sanina         0x0CD2
FMD5 4485                 0x0D1A
FMD7 4998                 0x0E09
```

**表地址按 build 定，不按文件名定。** 同名的 4857/4969/5248/4341/5365
在表地址、双源和结束判据上都可能不同；`FMD13 = FMD9G` 是唯一完全同 hash 的一对。
