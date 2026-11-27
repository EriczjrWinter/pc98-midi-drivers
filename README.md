# PC-98 私有 MIDI 驱动考古

**中文** | [English](README.en.md) | [日本語](README.ja.md)

PC-98 的游戏音乐，很多是「**数据 + 驱动**」的结构：数据只是事件脚本，
真正的格式规范在那份几百字节到几 KB 的常驻驱动里。

麻烦在于：**驱动没有文档，只有运行时才是活文档。**

这个仓库做的事，就是把这些驱动一个个挖出来、跑起来、把音乐取出来。

> 核心手法：**不解析数据，让驱动自己跑**，抓它的输出。
> 能静态解的（格式已文档化）就静态解——选哪条看哪个省事，不看教条。

---

## 已完成

| 驱动 | 会社 | 手法 | 作品 | 输出 |
|---|---|---|---|---|
| [**MMDR**](companies/leaf/) | LEAF | 运行驱动 | 雫 / 痕 | ✅ **51 首**，两源验证 |
| [**MS.COM**](drivers/mscom/) | LEAF | 运行驱动 | 雀鬼 / Filsnown | ✅ **61 首** |
| [**MMD**](drivers/mmd/) | KAJA（跨 23 家） | 静态解析 | 36 部 / 40 包 | ✅ **756 首**（GAL 460 / 非GAL 296） |
| [**MDRV98**](drivers/dofmdx/) | D.O. / ZyX | 运行驱动 + 抓包 | 独立驱动 6 包 + B 路线 11 包 + C 路线 4 部 | ✅ **117 首**（GS / MT-32）+ **678 首**（B 路线）+ **50 首**（C 路线 `.MUS`）+ **507 首**（.MDT 转录） |
| [**MSDRV4**](drivers/msdrv/) | 黒パッケージ | 运行驱动 + 抓包 | 7 个包（共 9 个） | ✅ **129 个 MIDI**（82 首 × GS/SC-88 变体） |
| [**FMP / 音痴君**](drivers/fmp/) | TGL / 戯画 / 夢幻 | 运行驱动 + 抓包 | 19 包 | ✅ **574 个 MIDI**（405 首，GS/SC88/MT-32/SC-55） |
| [**Alice Soft**](companies/alicesoft/) | Alice Soft | 跑引擎 | 二律背反 | ✅ 21 首（Windows 侧） |

**合计 1493 首完整曲目 + 678 首 B 路线片段 + 50 首 C 路线片段 + 507 首 .MDT 转录**
（51 + 61 + 756 + 117 + 21 + 82 + 405），加上驱动分析文档。

> **MDRV98 家族的覆盖情况。** 同一个驱动家族有四种打包方式：
> 独立驱动（`DOFMD_98.BIN` + `MDRV98`/`ZYXMD`）**6 个包**，已跑通（117 首）；
> `DOFMDX98.COM` + 游戏 EXE 的 **32 部**已解（11 包 766 个文件 / 678 首，其余 FM / MMD / 缺包）；
> `MDRV98.COM` / `BGMDRV.COM` + 小壳的 **28 包**：`.MUS` 里 HOOT 挂 GS/GM 的 4 部已导
> （64 个文件 / 50 首），其余 `BGM.COM` 包是纯 FM（只写 OPNA，直接 PASS）；
> `MV2x`（DOR 系列，23 部）是纯 FM，没有 MIDI。
> `.MDT` 的 19 包也是 FM/SSG 演奏数据，已用静态解析转录成 507 首 MIDI
> （[`src/mdt/`](drivers/dofmdx/src/mdt/)）。
> 详见 [drivers/dofmdx](drivers/dofmdx/)。

> Alice Soft 那条不是 PC-98 驱动——它的 MIDI 出口在 Windows 版 exe 里，
> PC-98 侧的 `MAKO` 是纯 FM。详见该目录。

## 判断该不该解这个驱动

**PC-98 有 MIDI ≠ 一定要逆向驱动。** 有些作品反而是 Windows 移植版有 MIDI：

| 类 | PC-98 | Win | 怎么办 |
|---|---|---|---|
| **A** | 有 | 无 | 只能啃驱动 |
| **B** | 无 | 有 | 用 Win 版（通常是标准 MIDI） |
| **C** | 有 | 有 | 挑好啃的那个 |
| **D** | 无 | 无 | CD-DA / WAV / FM，跳过 |

目录见 [catalog/](catalog/)，方案见 [docs/CATALOG.md](docs/CATALOG.md)。

## 素材怎么来

仓库**不含任何游戏数据**。全部自备，见 [docs/MATERIALS.md](docs/MATERIALS.md)。

要点：HOOT 的 pc98 库整个才 122 MB（只含音乐数据），一次下完即可。

```bash
python tools/hoot_download.py --go --jobs 8
```

## 规模

| 项 | 数量 |
|---|---|
| HOOT pc98 包 | 1777 |
| 有 MIDI 的包 | 405 |
| **不同的 MIDI 驱动** | **246**（按内容哈希去重） |
| 被多部作品共用的驱动 | 42 |

完整清单：[docs/DRIVER-INVENTORY.md](docs/DRIVER-INVENTORY.md)

### 复用度排名

| 驱动 | 作品 | 会社 |
|---|---|---|
| `MMD.COM` | 94 | 23 |
| `MMP_HOOT.COM` | 91 | 23 |
| **`DOFMDX98.COM`** | **79** | 3 |
| `FUGAM_98.COM` | 53 | 4 |
| `TGLFMP2.COM` | 35 | 3 |
| `MUSIC.COM` | 27 | 5 |
| `ARTDI_98.COM` | 26 | 1 |

## 通用方法

不管哪家驱动，步骤一样：

1. **找到驱动**：`.COM` / `.SYS` / `.BIN`，几百字节到几十 KB
2. **看它装了什么中断**：常驻型会挂钩件中断 + 功能调用中断
3. **找输出口**
   - MIDI → 接口板数据口（PC-98 常见 `0xE0D0`）
   - FM → OPNA 寄存器口（`0x188` / `0x388`）
4. **接管定时器** ← 「不用实时等」的关键
   - 有的驱动自己挂钩件定时器（MDRV98 就是：声卡 Timer B 中断，
     一次中断 = **4.908 ms**，用两份 Win95 参考反解出来的）
5. **收字节 → 拼 MIDI**

### 反复踩到的坑

| 坑 | 表现 | 解决 |
|---|---|---|
| Unicorn 不走实模式 IVT | `UC_ERR_EXCEPTION` | 按地址 hook `CD xx`，手动 `IP += 2` |
| `IN` 的 hook 不返回值 | `'NoneType' cannot be interpreted` | 回调里 `return value` |
| 定时器被驱动改写 | 快慢不对，且**每首不同** | 记录 `out 0x77/0x71`，逐 tick 换算 |
| 时钟频率搞错 | 快/慢 20–30%，不报错 | PC-98 的 8253 是 **2.4576 MHz** |
| 循环曲目 | 导出好几遍 | 字节流周期检测——但**段落重复 ≠ 整首循环**，有参考就用参考定长 |
| **同名不同构建** | 换游戏就崩 | **按内容哈希区分**，不看文件名 |
| 装中断不走 `INT 21h/25h` | 搜 `INT 21h`/IVT 写入一无所获 | 老驱动用 `mov ds,0` + 绝对地址直接写 IVT（MDRV98 就是这样漏的） |

### 一条重要的经验

**文件格式不等于音乐的完整定义。**

`.MS` / `.FMD` / `.MMD` 里没有「这条命令等几拍」——只有操作码和操作数。
真正的语义（一个延迟单位是多少 tick、某个未知命令干什么）
**只存在于驱动的运行时行为里**。

所以能静态解出来的只是**结构**，解不出来的是**时间语义**。
这也是为什么 MMDR、MS.COM、MSDRV4 最后都指向同一个答案：**让它自己说话**。

## 目录

```
companies/
  leaf/          LEAF：MMDR（雫 / 痕）+ FM 侧说明
  alicesoft/     Alice Soft：System3 引擎的 AMUS（Windows 侧）
drivers/
  mmd/           KAJA 的 MMD —— 静态解析，跨 23 家会社
  mscom/         LEAF 的 MS.COM —— 运行驱动
  msdrv/         黒パッケージ MSDRV4 —— 格式分析 + 运行驱动导出
  dofmdx/        D.O. MDRV98 —— 逆向文档 + mdrvcap（抓包 / 导出）
docs/
  项目交接文档（不随库发布）            交接指南（本地维护，不随上传版发布）
  DRIVER-INVENTORY.md   246 个驱动的全清单
  CATALOG.md            A/B/C/D 分类方案
  MATERIALS.md          素材从哪来
  进度记录（不随库发布）               当前进度与下一步（本地维护）
  流水线说明（不随库发布）           流水线化方案（本地维护）
catalog/
  games.json     4411 部作品（全平台）
  win95.json     414 部 PC-98 MIDI + VNDB 平台信息
  WIN95.md       98 部有 Windows 版，带置信度
  CROSS.md       与本地收藏的对照
tools/           下载、分诊、聚类、对照、转换
```

## 工具

| 工具 | 用途 |
|---|---|
| `hoot_download.py` | 下载缺的 HOOT 包（增量） |
| `driver_clusters.py` | 按内容哈希聚类驱动 |
| `dump_all.py` | 保底导出：所有 MIDI 作品的文件归档 |
| `build_catalog.py` | 生成作品目录 |
| `vndb_win95.py` | 查 VNDB 判断有没有 Windows 版 |
| `scan_collection.py` | 清点本地收藏 |
| `triage2.py` | 给每个包找出真正的驱动文件 |
| `mdrv98_routes.py` | 统计 MDRV98 家族的打包路线 + 32 字节签名扫描 |
| `make_upload.py` | 生成不含游戏数据的上传版（只含 git 跟踪文件） |
| `drivers/dofmdx/src/mdrvcap/` | MDRV98 抓包导出（表 B + Timer B → SMF） |

## 下一步

- [x] `MDRV98` 的 `DOFMDX98.COM` 路线（32 部）—— 11 包 766 个文件（678 首）已导，FM 4 部跳过、MMD 8 部另走、7 包缺失
- [x] **MMD 批量** —— 36 部 / 756 首，按作品归档（GAL 460 / 非GAL 296）
- [x] `MDRV98` 的 `MDRV98.COM` / `BGMDRV.COM` + 小壳路线 —— 收口：`.MUS` 4 部 GS/GM 已导（64 文件 / 50 首），FM 包 PASS；`.MDT` 已静态解析（19 包 507 首）
- [x] `MV2x`（DOR 系列，23 部）—— 确认是纯 FM 驱动，没有 MIDI 输出
- [x] `FUGAM_98`（53 部）—— **结案**：448 首已交付（A 100 / B 263 / FMD5 32 / FMD13 34 / FMD7 9 / FMD5248 10），全量静态/运行时收口，产物在 `build/hootcap/fmd-collection/`（[FMD.md](drivers/fugam/docs/FMD.md)、[FMD-FINAL-NOTES.md](drivers/fugam/docs/FMD-FINAL-NOTES.md)）
- [x] `MSDRV4` —— 运行驱动成功，导出 **7 个包 / 129 个 MIDI**（82 首 × GS/SC-88，按 OPNA Timer B 校准）；剩 `stjan2`（取 `.BM2`）与 `rekiai`（取 `.MF` 末段）两个容器**已解**，已出 23 首，时长待循环检测（[MS-FORMAT.md](drivers/msdrv/docs/MS-FORMAT.md)）
- [ ] 长尾：204 个一对一驱动

## 参考

- [HOOT](https://hoot.joshw.info/) —— 跑真驱动，验证的最佳对照物；
  它的 `xml/*.xml` 是查「某游戏用什么驱动」的最好索引
- [VNDB](https://vndb.org/) —— 平台信息，有 API
- [VGMRips · PC-98 Sound Drivers](https://vgmrips.net/w/index.php?title=PC-98_Sound_Drivers)
- [PMD 源码](https://github.com/d2mirrors/pmd) —— FM 侧的标准驱动

## 版权

游戏数据、驱动、音乐版权归原权利人所有。
本仓库只含**分析与转换代码**和由数据推导出的**格式文档**。

## 风雅（FUGA / FMD）完成清单

驱动已全部解出并按 build 分别验证；曲尾截断改用**静态音序器**（按记录流算长度，
不等运行时循环），循环曲的切点与开头无缝衔接。

| 分支 | build | 曲数 | 说明 |
|---|---|---:|---|
| A 代 | `FMD9.EXE` 4774 | 100 | Amaranth II（GS / MT-32）等 |
| B 代 | `FMD.EXE` 4969 / 4857 等 | 263 | Amaranth III/IV、TRUE LOVE、VENUS 等 |
| FMD13 | `FMD13.EXE` 5301 | 34 | Amaranth II ミュージックディスク |
| FMD5 | `FMD5.EXE` 4485 | 32 | 風雅セレクション |
| FMD5248 | `FMD.EXE` 5248 | 10 | イマージュ / パノラマ倶楽部 |
| FMD7 | `FMD7.EXE` 4998 | 9 | ま～ぷる・まぢっく |
| **合计** | — | **448** | 全部通过 `|runtime − static| ≤ 1` 与循环衔接校验 |

技术细节见 `drivers/fugam/docs/`：`FMD.md`（驱动与容器）、`FMD-BUILDS.md`（各 build 差异）、
`FMD-LOOP-F8F9.md`（记录流与 F9/F8 循环语义）、`EXPORTER-PROFILES.md`（每 build 的轨道表地址与能力）。

两个包（`ayayo2_98`、`sematte_98`）使用自有壳与 `.EMI` / `.MUS` 格式，不属于 FMD 记录流，另行处理。
