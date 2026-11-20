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
| [**MMD**](drivers/mmd/) | KAJA（跨 23 家） | 静态解析 | 94 部 | ✅ **35 首**（1 部验证） |
| [**MSDRV4**](drivers/msdrv/) | 黒パッケージ | 静态（部分） | 殻の中の小鳥 | ⚠ 格式七成，仿真卡在 DOS 环境 |
| [**MDRV98**](drivers/dofmdx/) | D.O. / ZyX | 运行驱动 + 抓包 | 独立驱动 6 包 | ✅ **117 首**（GS / MT-32 各一套） |
| [**Alice Soft**](companies/alicesoft/) | Alice Soft | 跑引擎 | 二律背反 | ✅ 21 首（Windows 侧） |

**合计 285 首 MIDI**，加上驱动分析文档。

> **MDRV98 只覆盖了一小部分。** 同一个驱动家族有三种打包方式：
> 独立驱动（`DOFMD_98.BIN` + `MDRV98`/`ZYXMD`）只有 **6 个包**，已经跑通（117 首）；
> `DOFMDX98.COM` + 游戏 EXE 的 **32 部**、`MDRV98.COM` + `mlp_hoot` 的 **28 包**都还没解。
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
  msdrv/         黒パッケージ MSDRV4 —— 格式分析 + 部分仿真
  dofmdx/        D.O. MDRV98 —— 逆向文档 + mdrvcap（抓包 / 导出）
docs/
  DRIVER-INVENTORY.md   246 个驱动的全清单
  CATALOG.md            A/B/C/D 分类方案
  MATERIALS.md          素材从哪来
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
| `drivers/dofmdx/src/mdrvcap/` | MDRV98 抓包导出（表 B + Timer B → SMF） |

## 下一步

- [ ] `MDRV98` 的 `DOFMDX98.COM` 路线（32 部，D.O. 18 / ZyX 5 / FOSTER 8 / 姫屋 1）——
      774 字节 DOS 装载器 + 游戏 EXE，驱动在 EXE 里，未解
- [ ] `MDRV98` 的 `MDRV98.COM` + `mlp_hoot` 路线（28 包，`.MUS` 数据），未解
- [ ] 独立驱动路线还剩 3 个 ZyX 包（`gbakuten_98` / `kyouiku_98` / `laidi1_98`）没导
- [ ] `FUGAM_98`（53 部）—— 数据疑似加密
- [ ] `MSDRV4` —— 需要更完整的 DOS 环境仿真
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
