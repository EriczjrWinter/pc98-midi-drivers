# A 代：已知 vs 假设（HOOT 验证前）

> 2026-11-26。目的：把“已实测”与“还在假设”分开，等 HOOT 打开后只验假设，不重复验证已知。
> 当前不启动 HOOT，等用户开好并播放 OPENING。

## 一、已知（有实测证据）

| 项 | 已知内容 | 证据 |
|---|---|---|
| 命令集 | A 代：`$FF $32 $E0 $C2 $E7 $95` + 数据口 `$D0`；停止走 `$FF/$32` | 板卡 JSONL / FMD-BUILDS |
| timebase | `$C2` → 48 tick/拍；`$E7 04` → 每 host clock 4/4=1 | 实测命令序列 |
| 轨道表 | 18 项 × `0x30`；`+0 seg`、`+2 loop`、`+4 cur`、`+0x27 en`、`+0x28 countdown`、`+0x29 ch`、`+0x2B depth` | 反汇编 + 运行时 dump |
| 记录格式 | 4 字节 `[cmd][dur][p1][p2]`；`<0x80` 音符；`0x80–0xEF` MIDI；`F8/F9` 循环；`FD/FC` 同步；`FE` 结束 | 反汇编 / 静态解码 |
| 三个主 API | `AX=0100` 装载歌曲、`AX=0300` 播放、`AX=01FF` 停止；`AX=0201` 是音色/前置（ama2 系） | 壳反汇编 / FMD.md |
| 默认轨迹 | `OPENING` 旧默认在 tick12000（约146 s）停；此时 0–8 活跃、9–17 `FE`、6/7 depth=1 | `build/audit/opening_tracks_146s.txt` |
| HOOT OPENING | 334.406 s / 9459 音 / 1 tempo / 120 BPM，sha1 `57D9C5B8…` | WIN MIDI + 用户确认 |
| 当前 pass | `end=pass` 后默认参数自然停在 tick31033，335.015 s / 9461 音 / 4 tempo | `build/audit/probe_opening_pass/OPENING.mid` |

## 二、假设（未验证，等 HOOT 采样）

| 假设 | 当前实现/判断 | HOOT 验证点 |
|---|---|---|
| 结束条件 | `end=pass`：所有曾启用轨 `en=0` 即停 | 146 s 时 HOOT 的 18 轨是否同样“0–8 活跃、9–17 FE”；真机是否在 146 s 继续 |
| tempo 来源 | 默认 120 → `$E0` → `$E1` 累乘；OPENING 得到 4 个事件（48/31/120/126） | HOOT 的 `$E0/$E1` 实际值、板卡 tempo 寄存器、为什么 HOOT 只有 1 个 120 |
| 变轨行为 | 怀疑 `seg` 会变；但当前 26000 tick 采样里 `[bx+0]` 未变 | HOOT 在 146/200/结束前的 18 项 `seg` 是否变化；若不变，“变轨”不是 `seg` |
| 每 tick 推进 | 当前每 `INT 0E` 推一条记录（1:1） | HOOT 的 `cur` 每 tick 增量；是否一条 tick 推多条/被 FD/FC 拉回 |
| F8/F9 | F8 带 AH 次数，F9 压栈；当前只读 loop 锚点，未按 AH 复刻 | 读 HOOT 的 `depth`/`loop`/`cur` 随时间变化，核对 AH 次数 |
| `+0x28` | 倒计时/时长字节；当前未用于 pass | HOOT 该字段在 146 s/结束时是否归零 |
| `[0x309C]` 初速 | 旧代码曾用；当前 `tempo_map` 不再读内存初速 | HOOT 内存该字节与 `$E0` 的关系 |

## 三、HOOT 采样清单（用户开好、播放 OPENING 后执行）

1. 先确认 HOOT 运行时基址/段地址；之前 dump 到过 `0xDCA57C8`，**不要直接把它当线性地址**，先复核镜像与运行时内存的偏移。
2. 定位 18×0x30 轨道表；每个采样点记录：
   `track, seg, loop, cur, en, countdown, channel, depth`。
3. 采样点：
   - 0 s / 30 s / 60 s / 100 s / **146 s** / 180 s / 200 s / 结束前后；
   - 146 s 必须与 `opening_tracks_146s.txt` 逐项对照。
4. 记录 `seg` 变化：若 18 条轨的 `seg` 全程不变，则“变轨”不是 `[bx+0]`，改查 `cur`/通道/loop 栈。
5. 记录 `cur` 每 tick/每 1/48 拍增量，验证“每 tick 一条记录”。
6. 记录 `depth`、`loop`、`en` 在结束前后的变化，验证 pass/FE。
7. 读板卡 tempo 状态与 `$E0/$E1` 值，解释 4 vs 1。

## 四、判据

- 146 s HOOT 仍在走、且 0–8/9–17 状态与我们的表不同 → 我们的 146 s 停是误判。
- HOOT `seg` 会变 → 变轨确实存在，按段做 pass。
- HOOT `seg` 不变 → 变轨是别的东西，别继续改 seg 逻辑。
- tempo 仍 4 个 vs HOOT 1 个 → 3a 不通过，OPENING 保持 candidate。
