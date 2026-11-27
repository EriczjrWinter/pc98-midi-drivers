# 风雅驱动变体清单（按 build，不按"代"）

> ## 📌 已被取代（2026-11-27）
>
> 本文是 2026-11-26 的**变体待办清单**，其中「FMD7 导出只有 2–6 秒」「FMD13 未分析」
> 「FMD5248 未动」等均已解决。**现行档案表见 [`EXPORTER-PROFILES.md`](EXPORTER-PROFILES.md)**
> （每个 build 的轨道表地址、曲数与验收状态），本文仅留作过程记录。

> **教训**：A 代 / B 代这种分法太粗。
> 同一代里有多个 build（4773 / 4969 / 4857 / 5248 / 5365 / 4601 / 4341 …），
> 行为未必通用——`marple98`（FMD7）就是用 A/B 的判据导坏了。
> **验证与判据必须以 build 为单位。**

## 一、已知 build 与状态

| 驱动 | 大小 | 包 | 代 | 状态 |
|---|---|---|---|---|
| `FMD9.EXE` | 4774 | ama2_98 / ama2s_98 | A | ✅ 已验证（OPENING 335.0 s / 9461 音） |
| **`FMD7.EXE`** | **4998** | **marple98**（ま～ぷる・まぢっく，fugasystem） | ? | ❌ **坏了：导出只有 2–6 秒** |
| `FMD13.EXE` | 5301 | ama2m_98（Music Disc） | A | ❌ 未分析 |
| `FMD.EXE` | 4773 | ama3_98（MT-32） | B 早期 | ⚠️ 跑过 24 首，未单独验证；双源（.GMD/.MMD）未分 |
| `FMD.EXE` | 4969 | ama4_98 / amakh_98 / deadfc98 | B 1.71 | ✅ 已验证（TLOVE_08 197.0 s / 19006 音） |
| `FMD.EXE` | 4857 | farce_98 / hiragi_98 / momoko_98 | B 1.72 | ✅ 已导（与 1.71 引擎逐字节相同） |
| `FMD.EXE` | 5248 | image1_98 / image2_98 / p_club_98 | ? | ⚠️ 未单独验证 |
| `FMD.EXE` | 5365 | bonnou3_98 / mug-r_98 | B 1.61 | ✅ 已导 |
| `FMD.EXE` | 4601 | venus_98 | B 1.51 | ✅ 已导 |
| `FMD.EXE` | 4341 | oerstd98 | B | ✅ 已通过（原 end=cap 已解） |
| `FMD14.EXE` | 4341 | sanina_98 | B | ⚠️ **与上一条同大小，疑似同一份代码** |
| `FMD5.EXE` | 4485 | fgsel1c / fgsel1m | FMD5 | 🔄 重导中 |

## 二、待处理队列（按优先级）

1. **`FMD7.EXE`（marple98）** —— 导出只有 2–6 秒，先 `--no-loop` 看自然长度：
   - 自然长度正常 → 是结束判据误触发，修判据后重导 9 首；
   - 仍然很短 → 驱动初始化/参数不对，查板卡日志里 `$FF/$32` 何时出现。
2. **`FMD13.EXE`（ama2m）** —— 14 首，全新驱动，风险最高。
3. **`FMD.EXE` 4773（ama3）** —— 先确认现有 24 首用的是 `.GMD` 还是 `.MMD`；
   多入口包应各出一套（GS 用 `.GMD`，MT-32 用 `.MMD`）。
4. **`FMD.EXE` 5248（image1/image2/p_club）** —— 只在 3 个包出现，一并核。
5. **`FMD14.EXE` vs `FMD.EXE` 4341** —— 先比哈希，相同则合并结论。

## 三、先做一件省事的事

```
把上面所有 build 两两逐字节 diff（build/_lead_fmd_fulldiff.py 那套）：
  4341 vs 4341（FMD.EXE / FMD14.EXE）→ 大概率相同
  4773 / 4969 / 4857 / 5248 / 5365 / 4601 → 看差异集中在哪
```

真实不同的变体可能只有 3–4 个，其余是同一份代码的不同包装。

## 四、判据（每个 build 都要过一遍）

```
① 无 --no-loop 的默认导出，时长/音符与 HOOT 差距 <2% / <5%
② 结束 end 属于 fe/pass/loop/cycle/idle 之一，**不是 cap/timeout**
③ 鼓音高集合与 HOOT 一致
④ 多入口包（GS / MT-32）各出一套，源按 .GMD/.MMD 对应
```

---

## 五、2026-11-26 全量构建差分（实测）

完整清单与差分见 `build/audit/fmd_build_diff.md`（CSV：`build/audit/fmd_build_diff.csv`）。

### 5.1 新增/修正的构建

| 驱动 | 大小 | SHA256 前缀 | 包 | 说明 |
|---|---:|---|---|---|
| FMD.EXE | 4341 | `beea535a847a` | oerstd98 | 与 FMD14 同大小但不同 |
| FMD.EXE | 4601 | `c9ce5a6a44df` | venus_98 | |
| FMD.EXE | 4773 | `b3902511d3fe` | ama3_98 | GS/MT 双源 |
| FMD.EXE | 4857 | `f6e72c26b375` | farce/hiragi/momoko/papa/reno/tlove12/yumecol | 7 包 |
| FMD.EXE | 4969 | `77ebe2d1353f` | ama4/amakh/deadfc | 已验证 |
| FMD.EXE | 5248 | `93552bfd878c` | image1/image2/p_club | 未单独验证 |
| FMD.EXE | 5365 | `6903b7ea0f0c` | bonnou3 | 与 mug-r 不同 |
| FMD.EXE | 5365 | `b676d5872d75` | mug-r | 与 bonnou3 不同 |
| FMD.EXE | 7051 | `f20427a9b524` | ayayo2 | 旧清单漏项 |
| FMD.EXE | 22392 | `69a971353ade` | sematte | 旧清单漏项 |
| FMD13.EXE | 5301 | `91904cc5f29c` | ama2m | 未分析 |
| FMD9G.EXE | 5301 | `91904cc5f29c` | ama2 | **与 FMD13 完全相同** |
| FMD14.EXE | 4341 | `75277fa99046` | sanina | **不是 FMD 4341** |
| FMD5.EXE | 4485 | `8d4f8913859d` | fgsel1m | |
| FMD5.EXE | 4485 | `cdb4af30e180` | fgsel1c | 与 fgsel1m 仅差 5 字节 |
| FMD7.EXE | 4998 | `f6c5709faaf3` | marple98 | 坏了 |
| FMD9.EXE | 4774 | `ba05444e7d6a` | ama2/ama2s | 已验证 |

### 5.2 差分结论

- **完全相同**：FMD13 = FMD9G。
- **近似相同**：FMD5 fgsel1m / fgsel1c 仅 5 字节（`0x0E62–0x0E66`）。
- **不能合并**：
  - FMD14 4341 vs FMD 4341：diff 3443 字节；
  - FMD 5365 bonnou3 vs mug-r：diff 4421；
  - FMD 4857 vs FMD 4969：diff 4783；
  - FMD7 4998 vs FMD9 4774：diff 4692；
  - FMD 7051 / FMD 22392 各自独立。
- FMD 4857/4969 旧文档说“引擎逐字节相同”，但原始 EXE 差异很大；
  若要合并，必须用**活镜像/引擎区**重新验证，不能按大小或旧结论。

### 5.3 处理顺序修正

1. FMD7 4998：先 `--no-loop` MP4，查自然长度与 `$FF/$32`；
2. FMD13 5301：装一首，验证命令集；
3. FMD 5248：image1/image2/p_club 一并核；
4. FMD14 4341：不并入 FMD 4341，单独验；
5. FMD 5365 两个变体分别验；
6. FMD 4857/4969：先做活镜像 diff，再决定是否合并。

## 六、按已验收作品做 A/B 二次分类（2026-11-26）

> 只列已有验收依据的组合；没有再宣称新结论。
> `marple98 / FMD7` 已排除，单独分析。

### 6.1 A 导出路径已验证

| build | 包 | 验收依据 |
|---|---|---|
| `FMD9.EXE` 4774 | ama2s_98 / ama2_98 | OPENING 335.0 s / 9461 音；MT ED12 已收口 |
| `FMD.EXE` 4601 | venus_98 | A 代 15 首旧交付 + 新表 |
| `FMD.EXE` 5248 | image2_98 | A 代 14 首旧交付 + 新表 |

### 6.2 B 导出路径已验证

| build | 包 | 验收依据 |
|---|---|---|
| `FMD.EXE` 4969 | ama4_98 / amakh_98 / deadfc98 | TLOVE_08 197.0 s / 19006 音 |
| `FMD.EXE` 4857 | farce/hiragi/momoko/papa/reno/tlove12/yumecol | B 批量无 cap，1.72 组 |
| `FMD.EXE` 4773 | ama3_98 | MT 24 + GS 24 已导出 |
| `FMD.EXE` 5365 | bonnou3_98 / mug-r_98 | B 批量通过；两个不同 hash 分开 |
| `FMD.EXE` 4601 | venus_98 | B 批量也通过 |
| `FMD.EXE` 4341 | oerstd98 | end=cap 已解（cycle） |
| `FMD.EXE` 5248 | image1_98 / image2_98 / p_club_98 | image2 通过；image1/p_club 仍需核 |

### 6.3 未分类（不能按 A/B 猜）

| build | 包 | 原因 |
|---|---|---|
| `FMD13.EXE` 5301 | ama2m_98 | 未装过/未验证命令集 |
| `FMD9G.EXE` 5301 | ama2_98 | 与 FMD13 同 hash；仍按 A 候选，不单独定 |
| `FMD14.EXE` 4341 | sanina_98 | 与 FMD 4341 同大小但 diff 3443；不是同一代码 |
| `FMD.EXE` 7051 | ayayo2_98 | 原清单漏项，未验证 |
| `FMD.EXE` 22392 | sematte_98 | 原清单漏项，未验证 |

### 6.4 特殊

```text
FMD5.EXE 4485  → FMD5 线，单独一轮 loop 导出
FMD7.EXE 4998  → marple98，排除，需单独分析
```

### 6.5 重要边界

同一个 build 可以同时出现在 A/B 两条交付路径：

```text
FMD.EXE 4601  → venus_98 的 A 与 B 都通过
FMD.EXE 5248  → image2_98 的 A 与 B 都通过
```

所以 **build 不能单独决定 A/B**；A/B 是“包/数据集 + 导出路径”的组合。
二次分类只回答“这个 build 在哪个路径上被验证过”，不是重新定义代际。

## 七、技术分类：P1–P5 profile（2026-11-26）

> A/B 代降级为 preset；真实单位是 build profile × source variant × 每曲 end。

### 7.1 profile 字段

```text
driver           文件/哈希
tail              /# /e /-# ...
table_mode        0xE64 / 0xEBC / 0xD1A
capture_mode      legacy / all
startup_trim      FMD5 专用
tempo             E0+E1
pass_tail_seconds pass 尾部截断
loop_depth        外层=1
source_variant    GMD/MMD + SysEx 机种
```

### 7.2 P1：legacy-A

```text
table_mode=0xE64
capture_mode=legacy
```

已验证：

```text
FMD9.EXE 4774 → ama2s_98 / ama2_98
```

候选未定：

```text
FMD13.EXE 5301 / FMD9G.EXE 5301
  → 同 hash，但尚未装过；FMD9G 只作 A 候选
```

### 7.3 P2：FMD.EXE all-B

```text
capture_mode=all
find_track_table（B 语义）
loop_depth=1
```

已验证子类：

```text
P2a 4969   ama4 / amakh / deadfc
P2b 4857   farce / hiragi / momoko / papa / reno / tlove12 / yumecol
P2c 4773   ama3（GS/MT）
P2d 5365-a bonnou3
P2e 5365-b mug-r
P2f 4601   venus
P2g 4341   oerstd
P2h 5248   image2；image1/p_club 仍待核
```

**P2 内部不能因为都叫 FMD.EXE 就合并**；4857/4969/4773/5365 原始 EXE 差异很大。

### 7.4 P3：FMD5 `/e`

```text
FMD5.EXE 4485
table_mode=0xD1A
tail= /e
capture_mode=all + 一轮 loop + intro
```

两个 hash 近似同源：

```text
8d4f8913 fgsel1m
cdb4af30 fgsel1c
```

### 7.5 P4：未分类

```text
FMD14.EXE 4341  sanina
FMD.EXE 7051    ayayo2
FMD.EXE 22392   sematte
FMD13/FMD9G 已按 P1 试导（FMD9G 同 hash）
```

### 7.6 P5：排除

```text
FMD7.EXE 4998  marple98 → 单独驱动，不能套 P1/P2
```

### 7.7 A/B preset

```text
preset_legacy_a = table 0xE64 + legacy + pass/loop
preset_all_b    = dynamic table + all + depth1 loop
preset_fmd5     = table 0xD1A + /e + one-loop
```

同一个 build 可以同时走两个 preset（4601/5248 已证）；A/B 不是驱动属性。

## 八、剩余驱动处置（快速核查，2026-11-26）

### 8.1 FMD13 / FMD9G（5301）

快速装 `ama2m_98` 的 `000.GMD` 跑 2000 tick：

```text
命令集：FF 32 E0 C2 E7 95 D0 + DF
首段：600 tick 即 loop，155 音
```

结论：命令集与常规 FMD 同族，`$DF` 长消息也会出现；**可优先做一次完整
A/B profile 对照**。FMD13 与 FMD9G hash 完全相同，先只验一份。

### 8.2 FMD14（sanina_98，4341）

`sanina_98` 的源文件是 `.GS` / `.FM` / `.LA`，不是 `.MMD/.GMD`。
现有 B 批量能产出 sanina，说明 **B profile 大概率可用**，但 FMD14 与 FMD 4341
diff 3443，不能引用 oerstd 的结论。下一步只抽 `SAN_005/008` 做完整导出对照。

### 8.3 FMD.EXE 5248（image1 / image2 / p_club）

- `image2_98` 用 `.GS`，A/B 都已通过；
- `image1_98` 用 `.MDI`，p_club 用 `.MI`；`.MD` 只是数据，不是歌曲入口。
- **表基址修正**：`find_track_table()` 返回 `CB+0xE98/0xE9D`（表内部），真实表在
  `CB+0xE70`。修正后：
  - image1 7 首：6 cycle + 1 loop；
  - p_club 3 首：GOAL `fe`、GOVER `pass`、TITLE `loop`（用户确认 TITLE 是循环曲）。

```text
DORA_M 138.08 s / 4714 音
HOU_M   51.86 s /  241 音
S1_1M  122.25 s / 2225 音
TITLE   31.76 s /  865 音  loop
```

产物：`build/hootcap/fmd5248/`，表 `build/audit/fmd5248_end_table.csv`。

### 8.4 EMD-98（ayayo2）——已移出风雅

`ayayo2_98` 实际入口是 `EMD_98.COM`，`.EMI` 是独立格式，不是 FMD 直接歌曲流。
详见 [`drivers/emd98/README.md`](../../emd98/README.md)。

### 8.5 ABIKO-98（sematte）——已移出风雅

`sematte_98` 实际入口是 `ABIKO_98.COM`，数据是 `.MUS/.ONS`。
详见 [`drivers/abiko98/README.md`](../../abiko98/README.md)。

### 8.6 FMD7 / FMD5

```text
FMD7.EXE 4998  → marple98，已按 P2+40000 重导
FMD5.EXE 4485  → 已按 /e + 0xD1A + 一轮 loop 导出
```

### 8.7 建议顺序

1. FMD13/FMD9G：已完成试导；
2. FMD14 sanina：已固定 max40000/cycle off；
3. FMD 5248：image1/p_club 已导出；MAIN1–6 无 `.MI` 配套，后续单独处理；
4. FMD7：已完成；
5. EMD-98 / ABIKO-98：移出风雅，各自独立逆向。

### 8.8 本轮快速实测补充

#### FMD13 / ama2m_98

先发现 `find_track_table()` 对 FMD13 返回 `CB+0xF42`，实际表在 `CB+0xF0F`
（偏 0x33，表内偏移，不是 ±0x30）。已改成 `table_ok()` 扫描候选。

修正后 34 首完整试导：

```text
build/hootcap/fmd13/ama2m_98/
loop 29 / pass 5 / fe 0 / cap 0
```

`019` / `023` 已从错误的 `fe@40000` 改为正常 loop：

```text
019: loop 48.75 s / 297 音
023: loop 64.47 s / 1458 音
```

FMD13 按 **P1 legacy-A** 处理；FMD9G 与它同 hash，只验一份。

#### FMD14 / sanina_98

`SAN_005/008.GS` 新的 cycle 检测会误判内层循环：

```text
cycle: 61.1 / 19.2 s（错）
cycle_mode=False, 40000 tick:
  SAN_005 end=fe   298.645 s / 9082 音
  SAN_008 end=loop 117.625 s / 3680 音
```

这与现有 B 产物完全一致。  
**FMD14 profile：max_ticks=40000, cycle_mode=False**；不要对它启用 cycle。

#### FMD.EXE 5248

- `image2_98` 的 `.GS`：A/B 均通过；
- `image1_98` / `p_club_98` 的 `.MD`：常规 capture 2000 tick 仍 0 音；
  这不是 profile 问题，是 `.MD` 数据/入口问题，先解容器。

#### FMD.EXE 7051 / 22392

- `.EMI` / `.MUS/.ONS + ABIKO 壳`，当前导出器无入口；先做容器/壳，不批跑。

#### FMD13 完整试导（2026-11-26）

`ama2m_98` 实际包内有 **34 个 stem（000–033）**，不是 14 首。
按 P1 legacy-A 已导出：

```text
build/hootcap/fmd13/ama2m_98/   34 首
pass 32 / fe 2 / loop 0 / cap 0
```

- `019`、`023` 在 40000 tick 仍为 `fe`（cutoff≈40000），
  实质接近 cap，需要再确认是否应更长；
- 表：`build/audit/fmd13_end_table.csv`
- 摘要：`build/hootcap/fmd13/_summary.md`

#### FMD14 注意

`SAN_005/008.GS`：

```text
当前 B 产物：298.6 / 117.6 s
新代码 max40000：cycle 61.1 / 19.2 s
```

新 cycle 判据可能把 FMD14 的内层循环误当结束。  
FMD14 不能直接套 cycle；下一步要按 build 单独决定 pass/loop，先不要覆盖现有 298/117 s 产物。

#### FMD5248 源文件补充（2026-11-26）

```text
image1_98:
  DORA_M.MD   → 0 音（数据）
  DORA_M.MDI  → 2000 tick 815 音
p_club_98:
  GOAL.MD     → 0 音（数据）
  GOAL.MI     → loop 600 tick / 104 音
  TITLE.MI    → loop 600 tick / 127 音
```

结论：image1/p_club 不是“解析器没实现”，而是 **源文件选错**；
profile 仍按 FMD.EXE 5248，源优先 `.MDI` / `.MI`。
image2 继续用 `.GS`。

#### FMD.EXE 5248 源文件实导（2026-11-26）

```text
image1_98 .MDI → 7 首，全部 loop
p_club_98 .MI  → 3 首，全部 loop
```

产物：

```text
build/hootcap/fmd5248/image1/
build/hootcap/fmd5248/p_club/
```

样本：

```text
DORA_M  122.57 s / 4241 音
GOAL      6.21 s /  104 音
TITLE     5.44 s /  127 音
```

`p_club` 的 `MAIN1–6.MD` 没有 `.MI` 配套，仍未导出；它们不能直接当歌曲源。

**流程要求：导出前先跑 `build/_fmd_source_audit.py`，按 stem 看 exts/headers，
不要按 `cand[0]`。**

#### FMD7 / marple98 重导结果（2026-11-26）

之前 2–6 秒是旧 max/结束判据造成的，不是驱动死亡。

按 `MMD` 源、all-mode、max 40000 重导 9 首：

```text
build/hootcap/fmd7/marple98/
loop 5 / fe 4 / cap 0
```

样本：

```text
MP4  15.00 s / 850 音   fe
MP0  60.23 s / 3455 音  loop
MP6 132.17 s / 5245 音  fe
```

表：`build/audit/fmd7_end_table.csv`

FMD7 仍作为独立 build 验证，但已不再标“坏了”。

#### 8.9 FMD7051 / FMD22392 源结构最后确认

`ayayo2_98`：

```text
AYA*.EMI
头：45 4D 00 06 ...（"EM" 自定义头）
不是 FMD 的 4 字节记录流；FMD.EXE 7051 也带有独立入口。
```

`sematte_98`：

```text
RIKA*.MUS  2 字节左右的参数流（FA/FB/FC/FD/FE/FF 命令密集）
RIKA*.ONS  固定 256 字节的元数据/控制块
壳：ABIKO_98.COM
```

这两个都不是“换 profile / 换扩展名”能解决的，必须先写 **EMI / MUS+ONS 解析器**，
或者找到对应壳的播放入口。暂不纳入 FMD P1–P3 批量。

### 8.10 壳/参数也是源结构的一部分

`ayayo2_98` 的 HOOT 元数据：

```text
shells: FMD -M6 -N0, EMD_98
```

直接给 FMD.EXE 7051 传 ` -M6 -N0` 跑 `.EMI` 会触发
`UC_ERR_EXCEPTION`，说明 **`.EMI` 不是 FMD7051 的直接歌曲流**；
包内另有 `EMD_98.COM` 入口。

`sematte_98`：

```text
shells: FMD, ABIKO_98
```

歌曲实际走 `ABIKO_98.COM` 壳，`.MUS/.ONS` 也不是 FMD 4 字节记录。

所以这两个包不能按 FMD P1–P3 处理；已经移出风雅：

```text
ayayo2_98  → drivers/emd98
sematte_98 → drivers/abiko98
```

**流程规则：源文件预检必须同时记录 `shells`/`tail`，不能只看扩展名。**
