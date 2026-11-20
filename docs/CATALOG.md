# 作品目录与优先级

## 为什么要建这个

一开始我们默认「PC-98 有 MIDI → 得逆向驱动」。

**但有些作品正好相反**：

```
PC-98 版没 MIDI，Windows 移植版有 MIDI
例：聖少女「Angel Halo」、A 社早期 PC 版 GAL
```

这类作品**根本不需要碰 PC-98 驱动**——Windows 版的 MIDI 通常是标准差量 MIDI，
或者像 A 社那样能跑引擎导出（`companies/alicesoft/` 那套已经做完了）。

所以真正要问的是：**这个作品的 MIDI 从哪个平台取最容易**，而不是「PC-98 有什么」。

## 数据的真实优先级

「PC-98 有没有 MIDI」只是起点。实际排序应该是：

```
① 现成 MIDI（任何平台）
     PS1 / SS / SFC 的序列格式转出来的、同人做的、官方发布的
     → 直接能用，零成本
② Windows 版提取
     标准 SMF，或像 A 社那样跑引擎导出
     → 一次性工作，通常不难
③ PC-98 驱动逆向
     私有驱动，要仿真或静态解
     → 最贵
④ 放弃
     CD-DA / WAV / 纯 FM 且无转换途径
```

**关键认识：其他平台的「类 MIDI」也是 MIDI 来源。**

PS1 的 SEQ/VAB、SS 的序列、SFC 的 SPC 序列，社区都有转 MIDI 的工具和成品。
这些**和 PC-98 驱动完全无关**，但成果是一样的——能听的 MIDI。

所以 B/C 类的判断不能只看 Windows，要按「**这个作品在任何平台有没有可用的 MIDI**」来算。

> **但要注意来源质量。** 类 MIDI 转换出来的文件年代未必对应 PC-98 版本，
> 转换质量参差，有的只是「能出声」。这类来源只适合判断**存在性**，
> 不能当作可靠音源。详见 [catalog/WIN95.md](../catalog/WIN95.md) 的免责声明。

## 四种情况（修订）

| 类 | 任何平台有现成 MIDI | PC-98 有 MIDI | 怎么办 |
|---|---|---|---|
| **A** | 无 | 有 | **只能啃驱动** |
| **B** | 有（Win/PS1/SS/SFC…） | 无 | 直接用 |
| **C** | 有 | 有 | 用现成的，驱动不用碰 |
| **D** | 无 | 无 | 跳过 |

**修订点**：原来的 B/C 只看 Windows，现在放宽到任何平台。
C 类从"两边都有，挑好啃的"变成"**有现成的就用现成的**"——
因为现成 MIDI 的成本是零，逆向驱动的成本是几小时。

## 数据结构

`catalog/games.json`，一行一个作品：

```json
{
  "title": "Angel Halo",
  "company": "seishoujo",
  "systems": ["PC-9821"],
  "pc98_midi": false,        ← PC-98 侧有没有 MIDI
  "variants": [],
  "archives": ["anglhalo_21"],
  "drivers": [],
  "win_midi": null,          ← 待补：true / false / null(未知)
  "other_midi": null,        ← 待补：其它平台（PS1/SS/SFC…）有没有可用的 MIDI
  "source": null,            ← 待补：从哪来
  "status": ""               ← A/B/C/D，等上面补上再自动判定
}
```

**`other_midi` 是新增字段**——你的收藏里有 PS1/SS/SFC 的类 MIDI 转换，
这些和 Windows 版一样属于「现成 MIDI」，会直接把作品从 A 类划走。

### 判定规则

```
any_midi = win_midi or other_midi

A: pc98_midi and not any_midi     ← 必须啃驱动
B: any_midi and not pc98_midi     ← 直接用
C: any_midi and pc98_midi         ← 用现成的
D: not pc98_midi and not any_midi ← 跳过
```

生成工具：`tools/build_catalog.py`（只用 HOOT 的 XML，Win 侧留空）。

当前：

| 项 | 数量 |
|---|---|
| 作品总数 | **4411** |
| PC-98 有 MIDI | **414** |
| Win 侧已标注 | 0（待补） |

## 怎么补

按可靠性排序：

1. **本地收藏** `D:\music\90S Galgame music\` —— 已经有 MIDI 的，直接标上
   （含 PS1/SS/SFC 的类 MIDI 转换 → 记到 `other_midi`）
2. **A 社那套** —— System3.x 的引擎已经做好，能跑出 MIDI 的直接标
3. **再版/合集**（GOG、Steam、DMM）—— 大多数带 MIDI 或以 WAV 重录
4. **VGMrips / 其他音乐库** —— 只作参考，因为它多数是 FM 录音

补上之后，`status` 就能按上面的规则自动算。

## 对驱动工作量的影响

现在 414 个 PC-98 MIDI 作品，**每多一个现成 MIDI 来源，就少一个必须逆向的驱动**。

你的收藏里那批 PS1/SS/SFC 转换是**新增的一整类来源**——
之前只考虑 Windows，漏掉了这部分。

优先级应该是：

```
先扫一遍所有已知来源（本地收藏 / Win / 其它平台）
    ↓
剩下真正没有替代的，才是 A 类
    ↓
A 类才值得投入驱动逆向
```

## 免责声明

`catalog/` 里的「本地已有 MIDI」来自**上传者个人收藏**的扫描，
只用来判断「这个作品是不是已经有现成 MIDI」，**不代表那些文件可用**。

- 部分是从 PS1 / SS / SFC 等平台转换来的，年代未必对应 PC-98，质量参差
- 部分来源已不可考
- **这些文件不在仓库里**，仓库只记录存在性

## 下一步

- [ ] 把本地收藏里已有的 MIDI 标进去（自动扫描）
      —— 含 PS1/SS/SFC 的类 MIDI 转换，记到 `other_midi`
- [ ] A 社那套跑出来的标进去
- [ ] 统计 A/B/C/D 各占多少
- [ ] 按 A 类的驱动重新排优先级
