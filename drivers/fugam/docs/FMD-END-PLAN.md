# FMD 曲尾截断方案

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

> 背景：风雅驱动的**出声问题已全部解决**（板卡模型、分派、鼓、通道）。唯一没通的是
> **曲尾截断/终止**：批量 237/255 判 `ok`，11 首 `end=cap`（不算 ok），另有 186 首被标
> `SUSPICIOUS`。本文给出一个替代方案：**静态音序器精确算长度**，不再依赖运行时等循环。

## 1. 为什么现在的两条路都不行

| 路径 | 做法 | 问题 |
|---|---|---|
| `static_total()`（`build/_fmd_export.py:158`） | 从轨首走到**第一个 `0xF8`** 数 tick | 不知道计数与嵌套，只能当**下界** |
| 运行时状态重复（`loop`/`cycle`，`REVIEW-CHECKLIST` §1A） | 等所有活跃轨 `(seg,loop,cur,en,depth)` 整轮重复 | 风雅是**多轨独立计数循环**，整轮周期是各轨周期的 LCM，可能几十万 tick → 等到 `cap` 也等不到 |

两条都在"猜"：一个算不准，一个等不到。

## 2. 实测数据（AMA4_015，2026-11-26 探针）

加载（`AX=0100`）后轨道表在运行时 `0x10FBC`（`find_track_table` + `fix_table_base`），
每轨从 `cur=0x2C` 起，记录 **4 字节** `[cmd][dur][p1][p2]`。

轨 0 的记录流（节选）：

```
0xD4  FD 01 00 00    同步
0xD8  F9 01 00 00    循环开始
0xDC  F9 01 00 00    循环开始（第二层）
0xE0..0xE8  三个音符
0xEC..0xFC  三个音符 + 两条 0x3C 记录
0x100 F8 03 00 00    循环结束，次数 3
0x104 FD 00 00 00
```

运行时逐 tick 状态（`build/_lead_fmd_track0.py` 同法）：

```
轨0: t=0   loop=00D8 cur=002C depth=0
     t=73  loop=0108 cur=00EC depth=2   ← 回跳
轨1: t=73  loop=0074 cur=0060 depth=2   ← 回跳
```

回跳目标**不是** `F9` 的下一条记录：

| 轨 | F9 位置 | 观测回跳目标 | `loop` 字段 |
|---|---|---|---|
| 0 | 0xD8、0xDC | **0xEC** | 0x108 |
| 1 | 0x50、0x54 | **0x60** | 0x74 |

### 2A. `F9`/`F8` 的处理代码（2026-11-26 已从**活镜像**反汇编确认）

> 注意：B 代驱动会改写自身代码区，**静态镜像反汇编不可靠**。以下是在播放到第 264 tick
> 时、用**内存写 watchpoint**（只盯轨 0 的 `cur` 两字节，不挂全范围 code hook）触发后
> 读取活内存得到的。

分派链（活内存 `CS:0x08C5` 起）：

```
08C5 cmp al,0F0h ; jae 0x8F1      ; ≥F0 → 特殊命令
08C9 cmp al,0E6h ; je  0x9F7      ; 选轨
08D0 cmp al,0E7h ; je  0xBA1      ; tempo
08D7 cmp al,098h ; je  0x951
08DB test [bx+27h],1 ; je 0x8B8   ; 轨未启用 → 跳过
08E1 mov ah,[bx+29h]              ; 通道
08E4 cmp ah,8Fh ; je 0x8B8        ; 通道无效 → 跳过
08E9 mov si,0EA2h ; call 0D49     ; 表驱动 MIDI 消息
08F1 mov byte [bx+28h],0
08F5 cmp al,0FDh ; je 0x91C       ; FD → call 0CE7
08F9 cmp al,0FCh ; je 0x91C       ; FC → call 0CE7
08FD cmp al,0F9h ; jmp 0B3F       ; F9
0904 cmp al,0F8h ; jmp 0B6Ah      ; F8
090B cmp al,0F7h ; je  0x97B
090F cmp al,0F6h ; jmp 0EEh
0916 cmp al,0FEh ; jb  0x8B8
091A jmp 0x924                    ; FE → [bx+27h]=0（停轨）
091C call 0CE7                    ; FD/FC：CF=1 → 停轨，否则立即重读
```

**`F9`（0x0B3F）——压栈**：

```
al = [bx+2Bh]            ; 当前深度
if al == 5: skip         ; 最多 5 层
[bx+2Bh] = al+1
si = bx + 6 + al*6       ; 每层 6 字节
[si]   = 0               ; 计数
[si+2] = bp              ; 目标 = 当前记录地址（F9 自身）
[si+4] = [bx+2]          ; 保存外层 loop 锚点
```

**`F8`（0x0B6A）——计数/弹栈**：

```
dh = ah                  ; ★ 次数 = F8 记录的第二个字节
al = [bx+2Bh]
if al == 0: nothing
si = bx + 6 + (al-1)*6
if dh == 0:              ; 0 = 无限
    bp = [si+2]; [bx+2] = [si+4]; continue
ax = [si] + 1; [si] = ax
if al == dh:             ; 计数到
    [bx+2Bh] = al-1      ; pop
else:
    bp = [si+2]; [bx+2] = [si+4]; continue   ; 回跳
```

**两个要点**：
1. `F8` 的次数在**第二个字节**（`mov dh,ah`，AH 来自记录的第二字节），0 = 无限；
2. 回跳时会把 `[si+4]`（外层 loop 锚点）写回 `[bx+2]`，所以运行时看到的 `loop` 字段
   会随层级变化——这解释了 §2 里 `loop` 与目标对不上的现象。

`FD/FC` 走 `0x0CE7`：返回 CF=1 就停轨（`[bx+27h]=0`），否则立刻重读记录（不耗 tick）。

**回跳目标与 `F9` 位置的差值已解释**：`F8` 回跳后 `bp` 先 `+4`（`0x0B98 → 0x8B8`），
随后记录读取循环（`0x843`）会**连续消费 dur=0 的记录**（`cmp [bx+28h],0; je 0x843`），
直到遇到 dur≠0 才把 `bp` 写回 `cur`。所以运行时看到的 `cur` 是"回跳后第一个吃 tick 的记录"：

- 轨 0：目标 0xDC → +4 = 0xE0 → 0xE0/0xE4/0xE8 都是 dur=0 → **commit 0xEC**；
- 轨 1：目标 0x54 → +4 = 0x58 → 0x58/0x5C 是 dur=0 → **commit 0x60**。

**不需要怀疑 `0x0CE7` 移动 `bp`**——差值完全由"零时长记录同拍消费"造成。

> ⚠ **观测纪律（`lessons/heisenberg/`）**：以上结论全部来自**内存写 watchpoint**
> （只盯 `[bx+4]` 两字节）触发的活内存读取，**没有挂全范围 code hook**。
> 风雅之前"查表不命中 / F8 计数永远完成"的假象，就是播放期 `UC_HOOK_CODE` 把 `cmp` 的标志位
> 弄丢造成的；任何"驱动怪癖"结论都必须用零扰动观测复核。

## 3. 方案：静态音序器

用已解出的语义，对每条轨做**确定性模拟**，算出精确总长：

```python
def track_len(data, cur):
    pos, tick, stack = cur, 0, []
    while True:
        cmd, dur, p1, p2 = data[pos:pos+4]
        tick += dur
        if cmd == 0xF9:            # 压栈：目标 = 本条记录地址，保存外层锚点
            stack.append({'target': pos, 'count': None, 'used': 0})
            pos += 4
        elif cmd == 0xF8:          # 计数/弹栈：次数在第二个字节，0 = 无限
            if not stack:
                pos += 4
                continue
            e = stack[-1]
            if dur == 0:                  # 无限
                pos = e['target']
            else:
                e['used'] += 1
                if e['used'] < dur:
                    pos = e['target']
                else:
                    stack.pop(); pos += 4
        elif cmd == 0xFE:          # 停止
            return tick, 'fe'
        else:                      # 音符 / MIDI 消息 / FD / FC
            pos += 4
```

得到每轨总长后：

- **所有轨有限** → 曲终 = `max(轨总长)`，即驱动会停的那一刻，**不需要运行时等重复**；
- **有轨无限**（`F8` 次数 0）→ 标 `infinite`，按「最长有限轨」或「首个完整循环」切，
  并按 `REVIEW-CHECKLIST` §1A 的产物标注规则打标；
- `cap` 自然消失：算出来多长就是多长。

## 4. 落地步骤

1. ~~定目标算术~~ **已完成**（§2A）：`F9` 压栈（目标 = F9 自身地址、保存外层锚点）、
   `F8` 用第二个字节作次数（0=无限）、计数到就弹栈；回跳后的"目标差"由**零时长记录同拍消费**
   解释（0xDC→0xEC、0x54→0x60），不涉及 `0x0CE7` 改 `bp`。
2. **写 `build/_fmd_static_seq.py`**：解密 `.GMD`（整文件 XOR `0xA5`）→ 取运行时轨道表
   （只需加载、不播放，`AX=0100` 后读 `0x10FBC`）→ 按 §3 模拟 18 条轨 → 输出每轨总长与曲终 tick。
3. **回归**：对 237 首 `ok` 的现有产物，比较"预测总长 vs 实测 `cutoff`"，
   要求逐首一致（误差 0）；不一致的就是 `F9`/`F8`/`FD`/`FC` 语义还缺东西。
4. **接进导出器**：`end=cap` 的 11 首先用静态长度重判；通过后把 `cycle`/`cap` 分支
   换成静态结果，并保留运行时轨迹作为二次校验。

## 5. 验收标准

- 11 首 `end=cap` 全部得到明确 `end`（`fe`/`loop`/`cycle`/`infinite`）且时长可解释；
- 237 首 `ok` 的时长**不变**（回归零差异）；
- 186 首 `SUSPICIOUS` 用静态长度复核，能解释的降级为正常。

## 6. 相关脚本

| 脚本 | 用途 |
|---|---|
| `build/_lead_fmd_tracks.py` | 加载后 dump 18 条轨的 `cur` 与记录里的 `F8/F9/FD/FC/FE` |
| `build/_lead_fmd_track0.py` | 播放时逐 tick 记录单轨 `(loop, cur, depth, en)` |
| `build/_lead_gmd_walk.py` | 解密 `.GMD` 后顺序打印 4 字节记录 |
| `build/_fmd_export.py` | 现有导出器（`static_total`、`capture`、`to_smf`） |

## 7. 一句话

**别再等循环自己重复**——把 `F9`/`F8` 的算术定死，静态算长度，曲终就是 `max(轨总长)`。
`cap` 是观测不足的产物，不是音乐事实。
