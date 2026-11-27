# PC-98 MIDI 驱动清单

把这个生态摸清楚，比逐个拆驱动更重要——先知道有多少东西、谁和谁共用。

## 方法：按内容哈希聚类

**不依赖文件名**，因为 HOOT 的 rom 名不可靠（同名不同构建、不同名同一驱动都常见）。

```
1. 从 xml/*.xml 取所有 midiout=1 的作品
2. 打开对应 zip，取出可执行类文件（.COM/.EXE/.DRV/.SYS）
3. 按 MD5 聚类
```

工具：`tools/driver_clusters.py`，明细在 `build/driver_clusters.json`。

## 结果

| 项 | 数量 |
|---|---|
| MIDI 作品（去重后的包） | 405 |
| 能扫到驱动的包 | 288 |
| **不同的驱动文件** | **246** |
| 被 2 个以上作品共用 | 42 |

**246 个驱动，42 个是共享的**——其余两百多个是一个作品一个专用。

## 共用最多的驱动

| hash | 作品 | 大小 | 形态 | 文件名 |
|---|---|---|---|---|
| `18f786793e80` | 12 | 760 | COM | `ARTDI_98.COM` |
| `325f08e122ed` | 12 | 774 | COM | `DOFMDX98.COM` |
| `19845ff5bcb9` | 8 | 6592 | COM-跳转 | `MMD.COM` |
| `699a8a5e19df` | 7 | 4857 | MZ | `FMD.EXE` |
| `9df4716b568d` | 6 | 7128 | COM-跳转 | `MMD.COM` |
| `da3da3a89429` | 6 | 22499 | COM-跳转 | `FMP3.COM` |
| `59e64f42f05c` | 5 | 7057 | COM-跳转 | `MMD.COM` |

> **`FMD.EXE`（风雅）这一行要单列一类**：它**必须用 MIDI 板高仿真才能跑**，不能像 MMD 那样
> 静态解析——驱动自己不算时间，节奏全靠板子的 `$C2`(timebase) / `$E0`(tempo) /
> `$E7`(时钟分割) / `$95`(时钟输出) 和每个时钟回送的 `$FD`。详见
> [`drivers/fugam/docs/FMD.md`](../drivers/fugam/docs/FMD.md) 的「〇、必须靠 MIDI 板高仿真」一节。

## 两个重要发现

### ① MMD 不止 3 个构建

按哈希分，`MMD.COM` 至少有 **6 个不同构建**：

```
6592 (8 部)   7128 (6 部)   7057 (5 部)
7071 (3 部)   7081 (3 部)   6218 (2 部)
```

之前只看实际文件，以为只有 3 个。**同名同版本号，内容不同**——这直接印证了
「同名不等于同构建」。

### ② 很多 .COM 是桩，真身在隔壁

`ARTDI_98.COM` 只有 760 字节、`DOFMDX98.COM` 只有 774 字节，
但同目录下还有 11–24 KB 的 `MDRV98` / `FMD.EXE` / `DOFMD_98.BIN`。

**HOOT 的 `code` 条目经常只是加载器**，真正的驱动是旁边那个大文件。

所以「按最大可执行文件取驱动」这条规则不可靠——**要看 rom 列表的顺序和配对关系**。

## 已解 vs 未解

| 驱动 | 作品 | 状态 |
|---|---|---|
| `MMDR` / `MS.COM` | 4 | ✅ 仿真跑通，173 首 |
| `MMD` | 94 | ✅ 静态解析（部分构建验证过） |
| 其余 240+ | — | ⬜ 未动 |

## 保底导出（第一期，已完成）

`tools/dump_all.py` 把每个 MIDI 作品的文件**原样解出来**，按会社/作品归档：

```
dump\<会社>\<档案名>\...      ← 原始文件，一个不少
build\dump_manifest.json      ← 清单：每个作品的文件列表 + 主驱动哈希
```

结果：

| 项 | 数量 |
|---|---|
| 导出的作品 | **316** |
| 文件总数 | 17037 |
| 总体积 | 90.1 MB |
| 识别出主驱动 | 280 |
| 不同驱动（哈希） | **193** |
| 被多部共用 | 48 |

**即使驱动还没解开，数据已经不会丢了。**

> ⚠ **这个 193 和前面的 246 不是一回事，别混用。**
>
> | 口径 | 数字 | 依据 | 可靠度 |
> |---|---|---|---|
> | **主口径** | **246** | 按 XML 的 rom 列表取可执行文件 | ✅ 可靠 |
> | 导出统计 | 193 | 每个包取「体积最大的可执行文件」 | ⚠ 不可靠 |
>
> 后者会**挑错**：同时带 FM 和 MIDI 两套的作品，可能挑中 FM 驱动
> （例如 `OPNDRV.COM` 会被当成主驱动）。它只用于导出归档，**不能用来判断驱动数量**。
>
> 引用数字时请用 **246 / 42**。

### 改名问题

XML 里的 archive 名是旧版 HOOT 的，117 个对不上现名。
`tools/resolve_renames.py` 按编辑距离自动解析了 28 个：

```
gaogao3        → gao3_98
karanonaka_98  → karanon_98
eime_21        → eime_98
zatuon_21      → zatuon_98
```

剩下的对不上的，**171 个是 X68000**（别的机种），只有几十个是 PC-98 真正缺的。

### 一个已知的缺陷

「主驱动 = 体积最大的可执行文件」这条规则**会挑错**：
同时带 FM 和 MIDI 两套的作品，可能挑中 FM 驱动（比如 `OPNDRV.COM` 排到了第一）。

所以清单里的「主驱动」只作参考，**准确的配对要看 rom 列表**（还没做）。

## 下一步

**优先做共用度高的**，而不是随便挑：

1. `ARTDI_98`（12 部，Artdink）—— 桩 + 大 BIN
2. `DOFMDX98`（12 个包 → 79 部作品）—— `.FMD` 明文
3. `FMD.EXE`（7 部，FUGAM）—— A 代已交付 70 文件；B 代 2026-11-25 打通并批量导出 237/255 首，
   11 首 `end=cap` 待修，TLOVE_02/08 与 FMD5 未收口；B 代产物仍 unverified，见
   [`FMD.md`](../drivers/fugam/docs/FMD.md)、[`FMD-BUILDS.md`](../drivers/fugam/docs/FMD-BUILDS.md)
   - **ayayo2_98 / sematte_98 已移出风雅**：分别是
     [`EMD-98`](../drivers/emd98/README.md) + `.EMI`、
     [`ABIKO-98`](../drivers/abiko98/README.md) + `.MUS/.ONS`
4. `FMP3.COM`（6 部）

**`DOFMDX98` 仍然是首选**：79 部作品、数据是明文 `.FMD`（有 `68V2` 签名和偏移表）、
驱动是 11.5 KB 的 COM 式 TSR。

## 已知的坑

- XML 里的 `archive` 名是**旧版 HOOT** 的，117 个包对不上现名
  （`gaogao3` → `gao3_98`、`karanonaka_98` → `karanon_98`）
  → 所以下载时**不靠映射，直接全下**
- HOOT 的 rom 名有时是内部编号（`000_BOOT`、`MT32_ROM`），不是真实文件名
- 同名驱动的不同构建必须按哈希区分

## 长尾的分层（2026-11-24 重跑 triage）

`tools/triage.py` → `triage2.py` → `driver_clusters.py` 重跑后（`build/driver_clusters.json`），
把 204 个「一对一驱动」按形态和大小分了层：

| 层 | 数量 | 例子 |
|---|---|---|
| **已知家族名** | 69 | `FMD.EXE`、`FMD13.EXE`、`MMD.COM`、`MSDRV.EXE`、`FMP3.COM`、`MUSIC.COM`、`PMD`、`MDRV`、`FMX.COM`、`IBGM.EXE` |
| **小壳（<2KB）** | 34 | `7COLM_98.COM`(400B)、`INT7C.COM`(1188B)、`BUNKA_98.COM`(510B)、`G3M.COM`(736B) |
| **中等未知（2–100KB）** | 71 | `MOTV21.EXE`(89KB)、`HTRON.EXE`(86KB)、`NADL.EXE`(82KB)、`AD.EXE`×3、`MIRAGE.EXE` |
| **疑似游戏 EXE（>100KB）** | 30 | `A1.EXE`、`A4.EXE`、`LUNA.EXE`、`BR2_98.EXE`、`HSB3.EXE` |

**结论**：真正“从零逆向”的核心约 **100 个**（71 中等 + 30 游戏 EXE），不是 204。
其中：

- 69 个已知家族大概率可**复用现有解析器**（MMD/FMD/MSDRV/FMP 系），只需小适配；
- 34 个小壳**跑一下看它调哪个驱动**即可分类；
- 30 个游戏 EXE 是驱动嵌在游戏里，最费劲，**压到最后**。

**建议顺序**：先跑 69 个已知家族（复用现有解析器，最便宜），再扫 34 个小壳（看它调谁），
71 个中等未知按 HOOT 标签里有没有 `GS`/`GM`/`MT-32` 过滤（FM 一律 PASS），最后动 30 个游戏 EXE。
**先建共用 `loop_detect`**，否则每个驱动都要重写一遍循环判定。

## 未做作品清单（按音源过滤，2026-11-26）

见 **[`WORKS-TARGETS.md`](WORKS-TARGETS.md)**。由 `build/driver_clusters.json` 生成，
已排除交付目录（mmd / fmd / fmd_b / cmidi7 / msdrv / fmp）里的包。

**口径**：

| 类别 | 包数 |
|---|---|
| 未做且音源明确为 MIDI（GS / GM / MT-32 / SC-55 / SC-88 / CM-64） | **306** |
| 未做但无音源标签（需人工判断） | 19 |
| 纯 FM（不列，直接 PASS） | 4 |
| 驱动家族 | 234 |

**音源标签取自作品标题里的括号**（如 `…(MT-32)`），不是 `driver_clusters.json` 的第三个字段——
那个字段是**厂商**（ARTDINK / WOLFTEAM / TGL…），别搞混。

**便宜优先**：38 个家族的驱动我们已经写过解析器（MMD / FMP / DOFMDX / MSDRV / FMD 系），
共 **88 个包**——多数只需适配容器，不是从零逆向。

**复现**：`python tools/triage.py && python tools/triage2.py && python tools/driver_clusters.py`，
分层统计脚本见 `build/_lead_triage_layers.py`（临时脚本，未入库）。

