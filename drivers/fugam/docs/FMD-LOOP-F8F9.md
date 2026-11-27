# FMD 记录 / `F9`·`F8` 循环解析结果（2026-11-26）

> 给「曲尾截断」方案用的语义说明。**全部结论来自活镜像 + 零扰动观测**，
> 不是静态反汇编（B 代驱动会改写自身代码区；见 §7）。

## 0. 速查

| 记录 | 语义 |
|---|---|
| `cmd < 0x80` | 音符：`[音高][dur][门长][力度]` |
| `0x80–0xEF` | MIDI 消息，经 `CS:0x0EA2` 的命令表 → `0x0D49` 查表分派 |
| `0xE6` | 选轨 |
| `0xE7` | 变速（tempo） |
| `0x98` | 特殊（`0x0951`） |
| `0xF9` | **循环开始：压栈**（目标 = 本条记录地址） |
| `0xF8` | **循环结束：计数/弹栈**（次数 = 第 2 字节，0 = 无限） |
| `0xFD` / `0xFC` | 同步标记 → `call 0x0CE7`；返回 CF=1 则停轨，否则同一拍继续 |
| `0xFE` | 停轨（`[bx+0x27] = 0`） |
| `0xF7` / `0xF6` | 其它特殊命令 |

轨道表项（A 代 `CSBASE+0xE64`，B 代 `+0xEBC`），每项 `0x30`：

```
+0x00 seg      +0x02 loop 锚点   +0x04 cur     +0x27 en（启用/通道有效）
+0x28 countdown +0x29 channel    +0x2B depth   +0x2C ...（DD 命令的地址字）
```

## 1. 每 tick 的推进语义

驱动每 tick 对每条轨：

```
if en == 0: skip
dec [bx+0x28]           ; countdown
if countdown != 0: skip ; 还没到
call 0x083E             ; 处理记录
```

`0x083E`（记录读取）的骨架：

```
083E  mov es,[bx]
0840  mov bp,[bx+4]        ; bp = cur
0843  mov ax, es:[bp]      ; al=cmd, ah=dur
0847  mov [bx+0x28], ah    ; 下一条的等待时间 = 本条 dur
084A  cmp al,0x80
084C  jae 0x8C5            ; 命令
      ... 音符处理（0xA8C）
08B8  add bp,4
08BB  cmp byte [bx+0x28],0
08BF  je 0x0843            ; ★ dur=0 → 同一拍继续处理下一条
08C1  mov [bx+4],bp        ; 提交 cur
08C4  ret
```

**要点**：`dur` 是"到**下一条**记录的 tick 数"。处理完一条记录后，
若它的 `dur==0`，驱动会在**同一拍**里继续读下一条——这就是 §4 的机制。

## 2. 命令分派（活镜像 `CS:0x08C5`）

```
08C5  cmp al,0F0h ; jae 0x8F1       ; ≥F0 → 特殊命令
08C9  cmp al,0E6h ; je  0x09F7      ; 选轨
08D0  cmp al,0E7h ; je  0x0BA1      ; tempo
08D7  cmp al,098h ; je  0x0951
08DB  test [bx+27h],1 ; je 0x08B8   ; 轨未启用 → 跳过
08E1  mov ah,[bx+29h]               ; 通道
08E4  cmp ah,8Fh ; je 0x08B8        ; 通道 = 0x8F → 跳过
08E9  mov si,0EA2h ; call 0D49      ; 表驱动 MIDI 消息
08F1  mov byte [bx+28h], 0          ; 特殊命令统一 dur=0
08F5  cmp al,0FDh ; je 0x091C
08F9  cmp al,0FCh ; je 0x091C
08FD  cmp al,0F9h ; jmp 0x0B3F      ; → 压栈
0904  cmp al,0F8h ; jmp 0x0B6A      ; → 计数/弹栈
090B  cmp al,0F7h ; je 0x097B
090F  cmp al,0F6h ; jmp 0x09EE
0916  cmp al,0FEh ; jb 0x08B8
091A  jmp 0x0924                    ; FE → en=0 停轨
091C  call 0x0CE7                   ; FD/FC
091F  jb 0x0924                     ; CF=1 → 停轨
0921  jmp 0x083E                    ; 否则同一拍继续读
0924  mov byte [bx+27h], 0          ; 停轨
```

## 3. `F9` 压栈（`0x0B3F`）

```
push bp
al = [bx+2Bh]            ; 当前深度
if al == 5: goto 0B66    ; 最多 5 层，超出就忽略
[bx+2Bh] = al+1
si = bx + 6 + al*6       ; 每层 6 字节：bx+6, bx+12, ...
[si]   = 0               ; 计数器
[si+2] = bp              ; ★ 目标 = 本条 F9 的地址
[si+4] = [bx+2]          ; 保存外层 loop 锚点
pop bp
jmp 0x8B8                ; 继续（同拍）
```

## 4. `F8` 计数/弹栈（`0x0B6A`）

```
dh = ah                  ; ★ 次数 = F8 记录的第 2 字节
al = [bx+2Bh]            ; depth
if al == 0: goto 0B9E    ; 没有循环栈 → 什么都不做
si = bx + 6 + (al-1)*6   ; 当前层的栈项
if dh == 0:              ; 0 = 无限
    bp = [si+2]; [bx+2] = [si+4]; goto 0B98   ; 回跳
ax = [si] + 1; [si] = ax
if al == dh:             ; 计数到
    [bx+2Bh] = al-1      ; 弹栈
    goto 0B9E
else:
    bp = [si+2]; [bx+2] = [si+4]   ; 回跳
0B98: jmp 0x8B8
```

**注意**：`[si+4]`（外层锚点）在**每次回跳**时写回 `[bx+2]`，所以运行时看到的
`loop` 字段会随层级变化——这不是异常。

### 4A. 回跳后"目标差"的来源（零时长消费）

`F8` 回跳后 `bp = target`，然后 `0x8B8 add bp,4`，接着在 `0x0843` 循环里
**连续消费 dur=0 的记录**，直到遇到 dur≠0 才 `mov [bx+4],bp` 提交。

所以运行时读到的 `cur` 是"回跳后第一个吃 tick 的记录"：

| 轨 | F9 位置 | 栈目标 | 实际 commit 的 cur | 中间被同拍吃掉的记录 |
|---|---|---|---|---|
| 0 | 0xD8、0xDC | 0xDC | **0xEC** | 0xE0/0xE4/0xE8（dur=0） |
| 1 | 0x50、0x54 | 0x54 | **0x60** | 0x58/0x5C（dur=0） |

**不需要怀疑 `0x0CE7` 改 `bp`**——差值完全由这个机制造成。

## 5. 静态音序器（可直接实现）

```python
def track_total(data, cur):
    """返回 (总 tick, 终止类型)。data 是解密后的曲目字节，cur 是轨首偏移。"""
    pos, tick, stack = cur, 0, []
    for _ in range(2_000_000):                  # 安全上限
        cmd, dur, p1, p2 = data[pos:pos+4]
        tick += dur
        if cmd == 0xF9:
            if len(stack) < 5:
                stack.append({'target': pos, 'count': None, 'used': 0})
            pos += 4
        elif cmd == 0xF8:
            if not stack:
                pos += 4
                continue
            e = stack[-1]
            if dur == 0:                        # 无限循环
                pos = e['target']
            else:
                e['used'] += 1
                if e['used'] < dur:
                    pos = e['target']
                else:
                    stack.pop(); pos += 4
        elif cmd == 0xFE:
            return tick, 'fe'
        elif cmd in (0xFD, 0xFC):
            pos += 4                            # 同步：继续（是否停轨需另判）
        else:
            pos += 4
    return tick, 'overflow'
```

- 每条轨算完后：**曲终 = `max(轨总长)`**（所有轨都有限时）；
- 有轨 `F8` 次数为 0 → 该轨无限，整曲标 `infinite`，按产品规则切一个周期；
- `cap` 不再需要：长度是算出来的，不是等出来的。

## 6. 验证方法

1. 对 237 首已判 `ok` 的产物，比较"静态预测总长"与"导出器实测 `cutoff`"，**要求逐首相等**；
2. 不等的，按 §2A 的机制定位（多半是 `FD/FC` 的停轨条件或跨轨的 `E6` 选轨）；
3. 全绿后，用它重判 11 首 `end=cap`。

## 7. 观测纪律（务必遵守）

- 风雅之前"查表分派不命中 / `F8` 计数永远已完成 / 锚点步长异常"三个假象，
  是**播放期 `UC_HOOK_CODE` 污染了 `cmp` 的标志位**造成的（`lessons/heisenberg/`）；
- 本文所有反汇编取自**内存写 watchpoint**（只盯 `[bx+4]` 两字节）触发时的活内存读取；
- 需要再看别的地址时：用**内存 watchpoint / 外部读内存**，不要挂全范围 code hook；
- 驱动会改写自身代码，**静态镜像地址可能对不上**；以活镜像为准。

## 8. 各 build 的差异（已实测一条，其余待查）

风雅有多个 build（FMD9/FMD13 = A 代；FMD.EXE 1.51/1.71/1.72 = B 代）。本文的地址来自
**B 代 1.71**（AMA4_015）。A 代轨道表基址是 `0xE64`（B 代 `0xEBC`），其余 handler 的地址
需要用同样方法在各 build 上复核；结构预期相同，但**不要假设地址相同**。

### 8.1 A 代轨道表基址 = `CS:0x0E64`（2026-11-26 实测确认）

```
ama2_98 / ENDING1.MMD / FMD9.EXE，AX=0100 加载后：
  CS:0E64  轨0 seg=4000 loop=0034 cur=002C en=FF ch=99
           轨1 seg=40F2 ... ch=91
           轨2 seg=419B ... ch=92
```

**坑**：`build/_fmd_export.py` 里的 `find_track_table()` / `fix_table_base()`
是**为 B 代写的**，对 A 代会返回误判结果（实测给出 `0x10F64`，读出来全零）。

**规则**：A 代（`FMD9.EXE` / `FMD13.EXE`）**直接用固定 `0x0E64`**，不要走自动探测；
B 代才用 `find_track_table()`。

### 8.2 静态音序器首个实测（ENDING1，一次性曲子）

```
轨总长：22728 / 22524 / 21360 …  全部 kind=fe（无无限轨）
曲终 = max(轨总长) = 22728 ticks
运行时实测（导出器 capture）= 22734 ticks / 228.62 s
差 6 tick（0.026%）
```

**结论**：`F9/F8` 算术 + `max(轨总长)` 这套静态算法成立，
尾巴那 6 tick 属于"最后一条记录的 dur 提交时机/尾音"，不是语义错误。
**"等运行时循环重复"这条路线可以废弃。**

## 6. `track_total` 的 `L_k`（2026-11-26 交接第一步）

`track_total()` 现在在 `infinite` 的 detail 里同时返回：

```text
L       首次永久 F9 的 tick（不是第一次 F8 的 tick）
cycle   旧字段：F8 回跳点到下一次同 F8 的 tick 数
period  从 L 到该 F8 完整一圈的 tick 数
```

无限曲切点：

```text
A = max(有限轨 T_k, 无限轨 L_k)
C = A + P_out

P_out = max(period_k)
```

### 6.1 自测

```text
有次数循环 14/fe           OK
无限循环   cycle=4 L=0 P=8 OK
两轨 max   14/fe           OK
```

### 6.2 真实数据

`AMA2_006.MMD`（FMD9）：

```text
轨0–6/9  infinite  L=1152  P=10752
轨7      infinite  L=1200  P=10752
有限轨    T=0
→ A=1200, P_out=10752, C=11952
```

所以 `FMD-STATUS` 里的 55.73 s 是预算截断，不是终点；该曲的静态切点是
1200 + 10752 = 11952 tick。

`ENDING1.MMD`（FMD9）：

```text
静态 22728 ticks
运行时 22734 ticks
差 6 tick（0.026%）
```

## 7. P0 静态预检（2026-11-26）

工具：

```text
python build/_fmd_static_p0.py <pack> <song> [drvname]
```

只做：

```text
install_pack → call 0100 → 读轨道表 → track_total
```

不播放、不挂 code hook。A 代（FMD9/FMD13）固定用 `CS:0x0E64`；
B 代才走 `find_track_table()/fix_table_base()`。

### ENDING1（有限）

```text
T_max=22728
classification=finite
```

### AMA2_006（无限）

```text
轨0–6/9  L=1152 P=10752
轨7      L=1200 P=10752
A=1200  P_out=10752  C=11952
classification=infinite
```

下一步：P1 按 `A,C` 切文件；P2 有限曲切到最后 note-on+2s；P3 运行时二次校验；P4 失败进 `unresolved`。

## 8. P1/P2 静态切点原型（2026-11-26）

工具：

```text
python build/_fmd_static_cut.py <pack> <song> <drv> [out.mid]
```

关键：运行时 capture 必须用 `natural_end=True` 跑到 `C` 之后，不能用旧 static
预算（6600 tick）提前停，否则会把预算截断误当成 C。

### AMA2_006（infinite）

```text
P0: A=1200 P_out=10752 C=11952
静态切: 100.895 s / 3620 音 / end=loop
```

**55.73 s 确定是预算截断**；静态切点约 100.9 s。

### ENDING1（finite）

```text
P0: T=22728
静态切 + pass 尾: 228.482 s / 3360 音 / end=pass
```

P3（到 max(C,T)+2 小节后断言无新 note / 全轨 en=0）尚未实现；当前只完成 P1/P2 原型。

## 9. P3/P4 运行时二次校验（2026-11-26）

同一个 `_fmd_static_cut.py` 在写出 MIDI 后执行 P3：

```text
probe = cutoff + 2 小节（192 tick）
finite:  probe 之后无新 note，且所有 seg≠0 轨 en=0
infinite: probe 之后仍有 note（确认不是静默截断）
```

不挂 code hook；只读 `capture` 的事件和轨道表。

### ENDING1（finite）

```text
P0 T=22728
输出 228.482 s / 3360 音
P3 OK  after_notes=0  active_en=0  runtime_ticks=22734
```

静态/运行时 6 tick 相位差已由 2 小节 probe 吸收。

### AMA2_006（infinite）

```text
P0 C=11952
输出 100.895 s / 3620 音  end=loop
P3 OK  after_notes=2243  active_en=9
```

### P4

P3 失败时：

```text
build/audit/_tentative/<file>.mid
build/audit/flips.csv
```

不把失败文件写成 ok；P4 状态为 unresolved。

## 10. A 代静态全量（2026-11-26）

### 10.1 老日志/报表

没有找到 venus/image2 的历史 tab 记录；只能手工扫描。

### 10.2 手工扫描结果

按 CS:0x0000–0x2000，0x30 步长，18 项判据：

```text
venus_98  tab = 0x0CB8
image2_98 tab = 0x0E70
```

image2 的非活动轨 `ch=0xA0`，扫描时需要接受 0x80–0xA0。

### 10.3 A 静态重导

```text
build/hootcap/fuga-a-static/   98/100
```

`ama2s_98/AMA2_024`、`ama2_98/AMA2_024` 静态算得 1,370,880 tick，
超过 200k 上限，标 `unresolved-huge`，没有写成品。

其余 98 首 P3 全 OK，包括：

```text
DHILTHY / AMA2_006  → 100.895 s / 3620 音 / loop
image2 IMAG2_00     → 164.939 s / 2864 音 / loop
venus VENUS_01      → 151.562 s / 7255 音 / loop
```

`fuga-a` 和 `fmd-collection` 仍未替换，等 B 代一并重导后再刷新。

## 11. `F8` 次数 `0xFF` 也是无限（2026-11-26）

`AMA2_024` 静态曾算出：

```text
1,370,880 = 5376 × 255
```

根因：F8 第二字节 `0xFF` 被当成次数 255。

### 先验

`0xFF` 与 `0` 一样是“无限”哨兵。

### 运行时验证

`ama2_98/AMA2_024.MMD` 轨 9，跑到 200000 tick：

```text
每 20000 tick 检查：en=FF，cur/loop 持续变化，未停轨
final en=FF
```

成立。

### 修改

`track_total`：

```python
if dur in (0, 0xFF):   # 0/0xFF = infinite
```

自测新增 `F8 0xFF` 项通过。

### 结果

```text
AMA2_024: A=0 P=10752 C=10752
静态输出 111.969 s / 2042 音 / loop
P3 OK after_notes=1598 active_en=7
```

A 静态全量现为 **100/100**，`fuga-a-static` 完整。

## 12. B 代静态全量（2026-11-26）

### 12.1 各 build 的表基址

```text
ama3_98 / ama3s_98                         0x0C9E
ama4_98 / amakh_98 / deadfc98              0x0EBC
farce/hiragi/momoko/papa/reno/tlove12/yumecol 0x0EBC
mug-r_98                                   0x0D18
oerstd98                                   0x0CD0
sanina_98 (FMD14)                          0x0CD2
venus_98                                   0x0CB8
image2_98                                  0x0E70
```

### 12.2 结果

```text
build/hootcap/fuga-b-static/
总数 263
ok       258
unresolved 5
infinite 238
finite    25
```

P3 失败（进 `_tentative` / `flips.csv`）：

```text
ama4_98/AMA4_018
ama4_98/AMA4_019
mug-r_98/MAG-R_00
sanina_98/SAN_005
sanina_98/SAN_011
```

A 静态：100/100 all P3 OK。  
`fuga-a` / `fuga-b` / `fmd-collection` 仍未替换，等这 5 首处理完再统一刷新。

## 13. B 代 5 首 unresolved 诊断（2026-11-26）

| 曲 | static T | runtime last note | 差 | 末态 |
|---|---:|---:|---:|---|
| ama4_98/AMA4_018 | 14568 | 16116 | +1548 | 全轨 en=0 |
| ama4_98/AMA4_019 | 12744 | 14292 | +1548 | 全轨 en=0 |
| mug-r_98/MAG-R_00 | 2184 | 2568 | +384 | 全轨 en=0 |
| sanina_98/SAN_011 | 2184 | 2568 | +384 | 全轨 en=0 |
| sanina_98/SAN_005 | 26664 | 30660（cap） | ≥3996 | 轨0–5仍 en=FF |

结论分两类：

1. **静态偏短，但运行时已停轨**：AMA4_018/019、MAG-R_00、SAN_011。
   表基址正确、轨都读到，问题在 `track_total` 对有限轨的 tick 累计
   （多计/少计某个 F8/FE 位置或零时长记录），不是表地址。
2. **静态判 finite，运行时仍在循环**：SAN_005。
   轨0–5 到 cap 仍 en=FF，说明 `track_total` 漏掉了无限循环
   （可能嵌套 F8 / 0xFF / 外层 F9 的组合），不能按 finite 切。

P3 把这些正确判成 unresolved；下一步先逐轨对比 static T 与运行时 cur/en 轨迹，
不要改全局判据。

## 14. 5 首逐轨追踪结果

逐轨同时记录 static T、运行时 `en0` tick、最后 `cur/en`：

### AMA4_018

```text
static T: t0 14568; t1–8 13416..14376
运行时: 全部轨在 16104 同时 en=0（t7 为 16116）
```

### AMA4_019

```text
static T: t0 12744; t1–8 6024..11604
运行时: 全部轨在 14280 同时 en=0（t4 为 14292）
```

### MAG-R_00 / SAN_011

```text
static T: max 2184
运行时: 全部轨在 2568 同时 en=0
```

结论：这四首不是某一轨的 `track_total` 单独算错，而是末段 **FD/FC 同步屏障**：
所有轨各自到达 T 后还要一起等同步，最后在同一个公共 tick 停轨。
P3 按 `T+2小节` 检查，正好把这部分同步等待判成“还有 note”。

### SAN_005

```text
static max 26664
运行时到 34000：轨0–5 仍 en=FF
```

这不是同步等待，是静态把实际还在循环的曲判成了 finite；需要单独查它的 F8/F9 组合。

下一步：

1. finite 曲的 P2 改用“公共 en0 / 最后 note+2s”作为真实终点，或在 P0 里显式计 FD/FC 屏障；
2. SAN_005 重新做无限判定；
3. 不要用这 4 首去改 `track_total` 的普通 tick 累计。

## 15. FD/FC/网格 第一版（2026-11-26，未收口）

已改：

```text
FD → 记录 fd_ticks，末尾按 96 网格向上取整
FC → pos = (word@pos+2 & 0xFFFC)
网格 GRID=96
```

selftest 新增并全过：

```text
FD 屏障/网格: T=4 fd=[0] ceil96=96
FC 跳转: T=0 fe
```

但重跑 5 首时，4 首从 P3 FAIL 变成 `overflow`（步数超限）：

```text
AMA4_018 / AMA4_019 / MAG-R_00 / SAN_011
```

说明 `FC → word&0xFFFC` 的解释虽然符合当前文字，但和这些曲目的实际控制流不闭合：
跳转后在轨内形成无计数回环，静态 2M 步上限被触发。

因此：

- FD 屏障/网格先保留；
- FC 先不能作为最终判据；
- 下一步必须按 SAN_005 同样方式做 **静态 (pos,depth,anchor) vs 运行时 (cur,[bx+2B],[bx+2]) 前 500 个变化点**；
- 在 FC 目标语义确认前，A/B 静态产物不替换，5 首仍 unresolved。

## 16. anchor 模型第一版（2026-11-27，未收口）

已实现：

```text
track_total(data, cur, anchor)
F9 压栈保存 old_anchor
F8 回跳恢复 old_anchor；弹栈不恢复
FD/FC → 锚点同步：
  si=anchor, bp=si
  FC 链最多 10 层，0 指针退回 si
  目标 FE → 停轨
  从 si+4 向后扫，普通记录 +4，FD +4，遇 FC/FE/FF 停
  cur=bp, anchor=s，同拍继续
```

selftest 6 项全过，5 首不再 overflow，但 P3 仍 FAIL：

```text
AMA4_018  static finite cut 2304   runtime notes after
AMA4_019  static finite cut 2784   runtime notes after
MAG-R_00  static finite cut 1632   runtime notes after
SAN_005   static finite cut 28128  runtime active 6 tracks
SAN_011   static finite cut 1632   runtime notes after
```

结论：锚点同步方向对了（不再 2M 步死循环），但 `si+4` 扫描/FC 链细节仍需用运行时
`(cur,[bx+2B],[bx+2])` 变化点对齐；5 首继续 unresolved。

已封板的 A/B 440 首基于旧静态产物，未被这次实验覆盖。

## 17. 五首已对齐（2026-11-27）

按驱动实际语义修正：

```text
扫描从 si 本身开始（不是 si+4）
停轨判定看 FC 链目标 data[bp] == FE（不是扫描结果 s）
```

FD/FC 锚点同步 + F9/F8 anchor 恢复后：

| 曲 | static cut | runtime | P3 |
|---|---:|---:|---|
| AMA4_018 | 16116 | 16117 | OK |
| AMA4_019 | 14292 | 14293 | OK |
| MAG-R_00 | 2568 | 2569 | OK |
| SAN_005 | 37032 | 37033 | OK |
| SAN_011 | 2568 | 2569 | OK |

`AMA4_018` 的 16116 是轨7的最大值；runtime 对应 16117，正好 `static+1`。
5 首现在都可以从 `_tentative` 转正。

下一步：358 首（A100+B258）回归，确认旧切点不变或统一 +1，再刷新 445 汇总。

## 18. 358 回归与 445 恢复（2026-11-27）

回归口径：A100 + B258（不含 5 首待修）。

```text
旧切点 = 新切点：358 / 358
```

5 首是预期变化：

```text
AMA4_018 14568 -> 16116
AMA4_019 12744 -> 14292
MAG-R_00  2184 -> 2568
SAN_005  26664 -> 37032
SAN_011   2184 -> 2568
```

无限曲为了保持已封板结果，仍用旧 `track_total_legacy` 口径；FD/FC 新语义只在有限曲生效。

5 首全部 P3 OK，已转正。最终：

```text
build/hootcap/fmd-collection/   448 首
build/audit/fmd-collection-2026-11-27.zip
```

## 19. 其他 FMD 分支的表地址（2026-11-27）

地址按 build 区分，不通用：

```text
FMD5.EXE 4485 8d4f8913 / cdb4af30   /e   0x0D1A
FMD13.EXE 5301 91904cc5                  0x0F0F
FMD9G.EXE 5301 91904cc5（同 FMD13）       0x0F0F
FMD7.EXE 4998 f6c5709f                   0x0E09
FMD14.EXE 4341 75277fa9                  0x0CD2
FMD.EXE 5248 93552bfd（image1/p_club）    0x0E70
```

B 代其余：

```text
ama3/ama3s 0xC9E
ama4/amakh/deadfc + farce/.../yumecol 0xEBC
mug-r 0xD18
oerstd 0xCD0
venus 0xCB8
```

`FMD5` 两个 hash 只差 5 字节，但仍按两个 build 记录；`FMD9G` 与 FMD13 同 hash。

## 20. FMD5248 静态化前置条件（2026-11-27）

FMD5248 的 image1 / p_club **不能按 `.GMD/.MMD` 的直接歌曲流处理**：

```text
image1_98:
  .MD   = 数据
  .MDI  = 歌曲入口
p_club_98:
  .MD   = 数据
  .MI   = 歌曲入口
```

因此：

1. 先用运行时确认 `.MDI/.MI` 如何交给 FMD.EXE 5248（装载路径、shell 参数、是否先读 `.MD`）；
2. 再讨论静态 `track_total` 和表 `0x0E70` 的 cut；
3. 在入口未确认前，**不跑 FMD5248 的静态重导**，否则得到的是 0 音/空表，不是长度。

当前 `fmd5248/` 的 10 首仍是动态 capture 产物，不是静态重导；保留为已验证交付，
但静态化任务挂起。

## 21. 其他分支静态重导（2026-11-27）

按显式 build 表地址，不含 FMD5248：

| 分支 | build | 表 | 输出 | 结果 |
|---|---|---|---:|---|
| FMD13 | 5301 `91904cc5` | `0x0F0F` | `fmd13-static/` | 34/34 ok |
| FMD7 | 4998 `f6c5709f` | `0x0E09` | `fmd7-static/` | 9/9 ok |
| FMD5 maze | 4485 `8d4f8913` | `0x0D1A` | `fmd5-maze-static/` | 20/20 ok |
| FMD5 calc | 4485 `cdb4af30` | `0x0D1A` | `fmd5-calc-static/` | 12/12 ok |

FMD5 源里包含 `FGTTL`、`MAZE03` 等旧 29 首交付没有的条目：

```text
maze 20 = 旧18 + FGTTL + MAZE03
calc 12 = 旧11 + FGTTL
```

已并入最终交付：`FGTTL`（maze/calc）、`MAZE03`（maze）；
FMD5 最终 32 首，总交付 448 首。
FMD5248 仍按 §20 挂起，等 `.MDI/.MI` 入口确认后再谈静态。

## 22. FUGAM_98 / 0201 与分支重导（2026-11-27）

### 22.1 0201 参数约定

`FUGAM_98.COM`（228 B，所有 FMD 包相同 hash `0b08bf9788db`）：

```text
BX=5 AH=3F      读 stdin/init 数据到 AH=48 申请的内存
DS=缓冲段 DX=0  SI=0
AX=0201 INT D3  ← 0201 的入参就是 DS:DX 数据指针，不是文件名
```

后续：

```text
AX=0100 DS:DX=歌曲缓冲 SI=0
AX=0300
```

所以成品顺序固定：

```text
0201(init 数据) → 0100(歌数据) → 0300
```

本轮分支重导已在 `install_pack(..., init_name='<stem>.MD')` 中把 init 数据
挂到 handle5，让壳自己执行 0201；静态 `cur` 全部从运行时轨道表读取，不硬编 `0x2C`。

### 22.2 分支结果

```text
FMD13  34/34 ok   → 已替换 fmd13/
FMD7    9/9  ok   → 已替换 fmd7/
FMD5   32/32 ok   → 已并入 fmd5/（含 FGTTL/MAZE03）
```

FMD5248 仍按 §20 挂起，等 `.MDI/.MI` 入口。

最终 448 首已重新汇总。|runtime-static| 的逐首数值化校验留给下一步。

## 23. 分支哈希对比（2026-11-27）

记录文件：

```text
build/audit/branch_hashes_2026-11-27.csv   当前静态+0201 版（75）
build/audit/branch_original_hashes.csv     原方法重导（72）
build/audit/branch_compare.csv             逐文件 hash 对比
```

结果：

```text
72 个共同文件：全部 hash 不同
3 个 only-new：FGTTL(maze/calc)、MAZE03(maze)
```

### 时长/音符对比（原方法 → 当前静态）

```text
FMD5 MAZE00   32.29/1732 -> 64.47/3464
FMD5 MAZE01   42.78/1705 -> 85.44/3410
FMD7 MP0      60.23/3455 -> 104.23/5985
FMD7 MP3      78.80/3840 -> 148.61/7207
FMD13 005     93.39/2587 -> 164.89/4550
FMD13 006     21.60/922  -> 93.55/4344
```

这不是 0201 造成的（加 0201 前后哈希/时长不变），而是**静态无限曲 cut 把一轮算成了约两轮**。
FMD5/FMD7 的当前静态版不能替换旧交付；FMD13 同样需要逐首复核。

旧验证版仍在：

```text
build/audit/fmd-collection-2026-11-26.zip
```

下一步应恢复 13/7/5 旧交付，再单独修静态无限曲的 `A/C` 公式，不能把“2 倍长度”当成品。

## 24. 0201 对已批准静态版的结论（2026-11-27）

对比对象是**已批准的 `*-static`**，不是 2026-11-26 旧交付。

结论：

```text
0201(init) 不改变 FMD5/FMD13/FMD7 的静态结果
```

依据：

- 加 init 前后分支 `cut / dur / notes / P3` 完全一致；
- FMD5 的 32 个文件逐字节相同；
- FMD13/FMD7 与对应 `*-static` 文件一致（当前 collection 已核对）。

旧 2026-11-26 只用于说明“改了什么”，不作为正确性判据。

## 25. FMD5248 10 首静态试跑（2026-11-27，未并入）

入口：

```text
image1_98  .MDI  ← init .MD
p_club_98  .MI   ← init .MD
表：0x0E70
```

10 首全部 P3 OK，但结果是：

```text
finite:
  GOAL  cut 912  9.50 s    diff=1
  GOVER cut 864  9.856 s   diff=1

infinite:
  DORA_M cut 36112 460.53 s
  TITLE  cut 6723  61.77 s
```

与现有动态版相比，infinite 曲明显接近 2 倍（例如 TITLE 31.76 → 61.77 s），
和 FMD5/FMD7 的“无限曲按两轮”问题同形。因此这 10 首**不并入**当前 448 交付；
FMD5248 继续保留现有动态版，等无限曲 A/C 公式修正后再替换。

## 26. FMD5248 两首 A/P/C 对照（2026-11-27）

不先改公式，先看旧动态版停在什么位置。

| 曲 | static A | static P | static C=A+P | 旧动态时长 |
|---|---:|---:|---:|---:|
| DORA_M | 784 (≈9.93 s) | 35328 (≈450.6 s) | 36112 (460.53 s) | 138.08 s |
| TITLE | 195 (≈1.79 s) | 6528 (≈60.0 s) | 6723 (61.77 s) | 31.765 s |

旧动态版的 loop 元数据：

```text
DORA_M:  cycle start=2000  period=8832   cutoff=10832  (138.08 s)
TITLE:   loop start=195    period=3264   cutoff=3459   (31.765 s)
```

判断：

- **TITLE**：旧 = `A + 3264`，新 = `A + 2×3264`；静态 P 把旧的一个 3264 period
  算成了 6528。这是明确的“公式重复一轮”。
- **DORA_M**：旧 cutoff = 2000 + 8832，不在 static A=784 也不是 A+P；而静态
  `P=35328 = 4×8832`。旧版是外层的某一次 cycle，新版是 A+4 个旧周期，不能直接按
  “旧≈A”验收。

所以先不动 A/C 公式。至少要把 DORA_M 的外层起点/周期口径对齐，再决定 P 是否该取
“一个旧 period”还是当前 4 倍。

## 27. P 改成 F8 执行间隔 + DORA 锚点探测（2026-11-27）

### P

`track_total` 对无限 F8 记录 `t1,t2,t3`：

```text
P = t2 - t1
断言 t3-t2 == t2-t1，否则 kind=unstable
```

selftest 全过。

### TITLE

```text
A=195  P=3264  C=3459
```

旧动态：

```text
loop start=195 period=3264 cutoff=3459  (31.765 s)
```

完全对齐，直接接受“前奏+一轮”口径。

### DORA_M

新：

```text
A=784  P=17664  C=18448
```

旧动态：

```text
cycle start=2000 period=8832 cutoff=10832  (138.08 s)
```

运行时 `[bx+2]` 采样（track0）：

```text
t=20000 728
t=40000 1464
t=60000 2152
t=80000 3092
t=100000 868
```

没有找到稳定的 2000；静态 `last_f9=46864`，也不是 2000。  
所以 DORA 的 A 口径仍未对齐，暂不修改 A、不并入 FMD5248 交付；TITLE 可以单独验收。

## 28. DORA_M 运行时 (cur, anchor) 周期（2026-11-27）

只读采样：

```text
0201(DORA_M.MD) → 0100(DORA_M.MDI) → 0300
40,000 tick，逐 tick 读 track0 (cur, [bx+2])
build/audit/dora_repeat.csv
build/audit/dora_repeat.md
```

首次重复：

```text
P1 = 784    cur=0xE8 anchor=0x118
P2 = 9616   cur=0xE8 anchor=0x118
间隔 = 8832
```

判读：

```text
8832 是最小整曲周期
17664 也匹配，但 = 2×8832
t=2000 与 t=10832 是同一周期的另一相位
```

因此旧动态版周期 8832 是对的；当前静态 `P` 仍是 17664，说明
`track_total` 的 F8 执行序列还把两个周期并成了一个，需要继续修 P 的统计口径。

`A=784` 与首次重复的 P1 一致；运行时 t=2000 是另一相位，不否定 784。

## 29. 5248 10 首：state 首次重复 P（2026-11-27）

P 改为静态状态 `(pos, anchor, depth)` 首次重复间隔，第三次断言；优先取 P≥600
的稳定重复，避免内层 192/384。

回归锚点 TITLE：

```text
A=195 P=3264 C=3459
新文件 SHA = 旧动态版 SHA = 1fc94d30d249
```

完全一致，保护点通过。

DORA_M：

```text
旧动态：cutoff 10832 / 138.08 s
新静态：A=784 P=8832 C=9616 / 122.57 s
```

P 已从 17664 退回 8832；新文件比旧动态短。

10 首对比：

| 曲 | 旧动态 | 新静态 | hash |
|---|---:|---:|---|
| DORA_M | 138.08/4714 | 122.57/4241 | diff |
| HOU_M | 51.86/241 | 51.86/241 | same |
| KEI_M | 80.01/2126 | 67.78/1763 | diff |
| S1_1M | 122.25/2225 | 95.08/1700 | diff |
| S1_2M | 73.54/1252 | 58.38/997 | diff |
| S1_3M | 105.89/1551 | 88.52/1332 | diff |
| ST_0M | 120.06/2917 | 120.20/2924 | diff |
| GOAL | 9.50/135 | 9.50/135 | diff（统计同） |
| GOVER | 8.31/173 | 9.86/173 | diff |
| TITLE | 31.76/865 | 31.76/865 | **same** |

目前只有 TITLE 和 HOU 可判完全一致；其余差异要逐首判断是旧动态版相位/周期误截，
还是新 state 重复口径仍不对。10 首仍未并入 448 交付。

## 30. 无限层状态重复后的 10 首结果（2026-11-27）

约束改为：只取无限循环层状态，且优先最小稳定 P≥600。

回归锚点 TITLE：

```text
A=195 P=3264 C=3459
SHA = 1fc94d30  ← 与旧动态版相同
```

通过。

DORA_M：

```text
A=784 P=8832 C=9616
122.57 s / 4241 音
旧动态：138.08 s / 4714 音
```

P=8832 已对上，但文件比旧动态短，A 相位仍不同。

其余 8 首**没有回到旧时长**：

```text
KEI_M   67.78 vs 80.01
S1_1M   95.08 vs 122.25
S1_2M   58.38 vs 73.54
S1_3M   88.52 vs 105.89
ST_0M  120.20 vs 120.06
GOAL     9.50 vs 9.50（hash 不同）
GOVER    9.86 vs 8.31
HOU_M   51.86 vs 51.86（hash 相同）
```

所以“其余 6 首回到旧值附近”未成立，不能并入 448。
下一步必须逐首采运行时 `(cur, anchor, depth)` 的 A/P，和静态逐首对；差 0 的才收。

## 31. 状态重复命中点 count 检查（2026-11-27）

在 `_state_period` 命中点打印：

```text
STATEHIT A P pos anchor depth count cmd
```

10 首共 75 条命中：

```text
count=0xFF: 62
count=0x00: 13
count=有限值: 0
```

所以无限层过滤器是生效的；6 首结果没变不是“又命中了有限层”。

命中的典型形态：

```text
DORA_M  A=784 P=8832 pos=0x0D4 anchor=0x0D8 depth=0 count=0xFF cmd=0xFD
TITLE   A=195 P=3264 pos=0x0060 anchor=0x007C depth=0 count=0x00 cmd=0xF9
```

下一步按交接：检查 FMD.EXE 5248 的 `0x0C13` FC 链如何改写 anchor/cur；
6 首的 A/P 差异应在该链，而不是状态过滤器。

## 32. depth 过滤候选与 DORA 矛盾（2026-11-27）

`STATECAND` 实测 DORA_M track0 有两类稳定候选：

```text
depth=2  P=8832     （与运行时时序一致）
depth=1  P=17664    （两个 8832 并在一起）
```

若按“depth 最小 = 最外层”直接选，会选 `depth=1 / P=17664`，**破坏 DORA 的 8832**。
说明“depth 最小”不能直接等同于运行时整曲层：

- 运行时的 `[bx+2B]` 与静态 `len(stack)` 的层级编号/含义还需要对齐；
- TITLE 的 depth0/P3264 不受影响；
- 6 首命中里仍有 depth2/3 的 inner 无限层；它们没变，说明没有可用的更外层无限候选，
  或外层候选被当前 depth 排序压掉。

状态过滤器本身已证明没问题（75 条命中 count 全 0/0xFF）。
下一步不是再改 P 公式，而是把运行时 depth 与静态 depth 对齐，明确哪一层才是整曲层。
FMD5248 仍不并入交付。

## 33. F9 起点 S + 更深无限层优先（2026-11-27）

按“第一个无限 F8 的 F9 起点状态 S，等 S 再出现”实现并测试。

TITLE：

```text
S hits = 192, 3456, 6720
P = 3264
```

保持正确。

DORA_M：

```text
S hits = 784, 18448, 36112
P = 17664
```

仍不是运行时确认的 8832；说明当前选中的 S/深度仍对应“两个 8832”，
不是运行时的整曲层。更深优先规则尚未真正选到正确层。

因此这版不作为最终实现，10 首继续不并入交付。
下一步要把“更深”与运行时 `[bx+2B]` 的层号对齐，而不是仅按静态 stack 深度。

## 34. DORA_M 静态/运行时状态序列对齐（2026-11-27）

输出：

```text
build/audit/dora_state_diff.csv
build/audit/dora_state_diff.md
```

对齐方式：

```text
static: 处理完当前记录后的 (pos, anchor, depth)，事件间保持
runtime: 每 tick 后的 (cur, [bx+2], [bx+2B], en)
前 12000 tick
```

结果：

```text
12000 tick 内全部一致
第一个不一致 tick: 无
```

所以 FD/FC、F9/F8 路径本身与运行时一致；不是“早分叉”bug。
DORA_M 的 8832 重复在静态序列里确实存在，问题只在**选哪个重复状态/哪一层**，
也就是 key 不统一，而不是状态推进错误。

务实结论：

- 静态路径可保留；
- FMD5248 的 10 首切点可以直接用运行时状态重复的 A/P，静态只用于已验证曲；
- 静态工具的层选择问题不阻塞 448 交付。

## 35. 全轨状态向量周期与 5248 收口（2026-11-27）

规则改为全轨向量：

```text
V(t) = concat[(seg,cur,anchor,depth,en) for all 18 tracks]
找最小 P≥96 与最早 A，使连续三段相同
C = A + P
```

结果：

| 曲 | A | P | C |
|---|---:|---:|---:|
| TITLE | 195 | 3264 | 3459 |
| DORA_M | 784 | 8832 | 9616 |
| HOU_M | 16 | 3648 | 3664 |
| KEI_M | 984 | 4608 | 5592 |
| S1_1M | 16 | 6912 | 6928 |
| S1_2M | 796 | 3840 | 4636 |
| S1_3M | 400 | 7680 | 8080 |
| ST_0M | 5537 | 3984 | 9521 |

GOAL/GOVER 是 finite，无周期。

TITLE SHA 保持 `1fc94d30d249`；DORA_M 为 `a2655cc11478`。
10 首已并入 `fmd5248/`，最终 448 首不变（只是替换内容）。

旧动态版的时长不作为正确性基准；这 6 首本来就不该按旧值拉长。

### 35.1 为什么不能用 depth / 层号挑周期

之前的几版判据都试图"选某一层"（取最外层、取最深无限层、按 depth 过滤），
在这 6 首上全部失效，原因是同一个：

```text
同一段重复可能发生在"不同层的同一个状态"上。
按层挑 → 要么漏掉它（该层不是无限层），要么切到更浅的内层（提前结束）；
而且"哪一层算外层"本身要额外定义，定义一变结果就变。
```

全向量周期性绕开了这个问题：**只看"整体状态是否复现"，与层无关**，
且要求连续三段一致（避免偶然重合）。代价是需要逐 tick 采样全部 18 轨，
但静态算完之后可与运行时逐 tick 状态序列直接对齐（差 0 才算过）。

判据补充：A 取"三段一致"的最早起点；若前奏本身也有重复，
要求 A..A+P 内不存在更短的稳定周期（即取最小 P）。
