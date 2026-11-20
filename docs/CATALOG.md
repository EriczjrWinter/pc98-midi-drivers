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

## 四种情况

| 类 | PC-98 | Win | 怎么办 |
|---|---|---|---|
| **A** | 有 | 无 | **只能啃驱动** ← 现在的主力 |
| **B** | 无 | 有 | **用 Win 版**，通常简单得多 |
| **C** | 有 | 有 | 挑好啃的那个（一般还是 Win） |
| **D** | 无 | 无 | CD-DA / WAV / FM，跳过 |

**A 类才是真正需要逆向的**，D 类直接放弃。

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
  "source": null,            ← 待补：Win 版从哪来
  "status": ""               ← A/B/C/D，等 win_midi 补上再自动判定
}
```

生成工具：`tools/build_catalog.py`（只用 HOOT 的 XML，Win 侧留空）。

当前：

| 项 | 数量 |
|---|---|
| 作品总数 | **4411** |
| PC-98 有 MIDI | **414** |
| Win 侧已标注 | 0（待补） |

## 怎么补 Win 侧

按可靠性排序：

1. **本地收藏** `D:\music\90S Galgame music\` —— 已经有 MIDI 的，直接标上
2. **A 社那套** —— System3.x 的引擎已经做好，能跑出 MIDI 的直接标
3. **再版/合集**（GOG、Steam、DMM）—— 大多数带 MIDI 或以 WAV 重录
4. **VGMrips / 其他音乐库** —— 只作参考，因为它多数是 FM 录音

补上之后，`status` 就能自动算：

```
pc98_midi and not win_midi  → A（必须啃驱动）
win_midi and not pc98_midi  → B（用 Win 版）
both                        → C（挑好啃的）
neither                     → D（跳过）
```

## 对驱动工作量的影响

现在 414 个 PC-98 MIDI 作品，**如果 B/C 类占两三成，需要逆向的驱动就少一大截**。

这直接改变第二期的优先级：

```
先做 A 类（PC-98 独占）→ 那才是没有替代来源的
B 类的驱动即使解开了，也没有额外价值
```

## 下一步

- [ ] 把本地收藏里已有的 MIDI 标进去（自动扫描）
- [ ] A 社那套跑出来的标进去
- [ ] 统计 A/B/C/D 各占多少
- [ ] 按 A 类的驱动重新排优先级
