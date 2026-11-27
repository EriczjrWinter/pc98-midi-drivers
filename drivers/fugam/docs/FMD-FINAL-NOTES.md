# FMD 最终技术记录（2026-11-27）

## 1. 交付

```text
build/hootcap/fmd-collection/
build/audit/fmd-collection-2026-11-27.zip
```

```text
A 100
B 263
FMD5 32
FMD13 34
FMD7 9
FMD5248 10
合计 448
```

VENUS_00 为空占位，未计入；EMD-98 / ABIKO-98 已移出风雅。

## 2. 构建与表地址

完整包名/日文名见 [`FMD-BUILD-MAP.md`](FMD-BUILD-MAP.md)。

```text
FMD9 4774                  0x0E64
FMD13/FMD9G 5301           0x0F0F   （同 hash）
FMD.EXE 4341 oerstd        0x0CD0
FMD.EXE 4601 venus         0x0CB8
FMD.EXE 4773 ama3          0x0C9E
FMD.EXE 4857 七包          0x0EBC
FMD.EXE 4969 三包          0x0EBC
FMD.EXE 5248 image/p_club  0x0E70
FMD.EXE 5365 mug-r         0x0D18
FMD14 4341 sanina          0x0CD2
FMD5 4485                  0x0D1A
FMD7 4998                  0x0E09
```

**表地址按 build，不按文件名。** `find_track_table()` / `fix_table_base()` 返回的是
**线性地址**（如 `0x10F70`），不要再加 `CSBASE`；加两次会读到全零表。

## 3. FUGAM_98 / 0201

`FUGAM_98.COM` 228 字节，所有 FMD 包同 hash `0b08bf9788db`：

```text
BX=5 AH=3F      读 init 数据到 AH=48 申请的缓冲
DS=缓冲段 DX=0  SI=0
AX=0201 INT D3  ← 入参是 DS:DX 数据指针，不是文件名
AX=0100         歌曲
AX=0300         播放
```

顺序固定：

```text
0201(init) → 0100(song) → 0300
```

对已批准 `*-static` 的对比：0201 不改变 FMD5/FMD13/FMD7 的 cut/dur/notes/P3；
FMD5 文件逐字节相同。旧 2026-11-26 包不是正确性基准。

## 4. 静态音序器

记录格式：

```text
[cmd][dur][p1][p2]
F9 压栈：target=本条地址
F8：dur 次数；0/0xFF=无限；回跳 target+4；有限回跳恢复 anchor，弹栈不恢复
FE 停轨
FD/FC：锚点同步
```

FD/FC：

```text
si = anchor; bp = si
沿 FC 链最多 10 层；目标 0 退回 si
停轨判定看目标记录 data[bp]==FE，不看扫描结果
扫描从 si 本身开始；普通记录 +4，FD +4，遇 FC/FE/FF 停
cur=bp; anchor=s，同拍继续
```

FC 掩码：

```text
A/B 代     0xFFFC
FMD5248    0x00FC（低 8 位对齐 4）
```

当前这 6 首两种掩码结果相同，掩码不是差异原因。

## 5. 周期定义（最终）

不再按 depth/层号挑周期。用**全轨状态向量**：

```text
V(t) = 所有 18 轨 (seg, cur, anchor, depth, en) 拼接
找最小 P≥96、最早 A，使
  V(A..A+P) == V(A+P..A+2P) == V(A+2P..A+3P)
C = A + P
```

有限曲：

```text
T = max(T_k)
文件切到 T，再按 pass 规则收到最后 note+2s
```

运行时二次校验：

```text
跑到 C/T + 2 小节；之后无新 note，有限曲全轨 en=0
失败 → unresolved / _tentative / flips.csv
```

## 6. A/B

```text
A 100
B 263
358 回归：旧切点 358/358 不变
5 首预期修正：AMA4_018/019、MAG-R_00、SAN_005/011
```

A/B 无限曲保留旧 `track_total_legacy` 口径，避免已封板结果被新公式改动。

## 7. FMD5 / FMD13 / FMD7

```text
FMD13 5301 0x0F0F   34/34
FMD7 4998 0x0E09     9/9
FMD5 4485 0x0D1A    32/32
```

FMD5 含新增：

```text
FGTTL（maze/calc）
MAZE03（maze）
```

这三组在 0201 前后结果一致；当前已批准的 `*-static` 可直接使用。

## 8. FMD5248

入口：

```text
image1_98  .MDI  ← init .MD
p_club_98  .MI   ← init .MD
表 0x0E70；FC mask 0x00FC
```

全向量周期：

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

GOAL/GOVER 为 finite：

```text
GOAL  cut 912  9.50 s
GOVER cut 864  9.856 s
```

TITLE SHA：

```text
1fc94d30d249...
```

与旧动态版/回归锚点相同。10 首已并入 `fmd5248/`。

DORA_M 静态/运行时状态序列前 12000 tick 全部一致（见
`build/audit/dora_state_diff.csv`），证明 FD/FC/F9/F8 路径无早分叉；
差异只在周期 key。

## 9. 重要口径

- 旧动态版不是正确性真值：自相似会把半周期/整周期混在一起；
- 正确性判据：`|runtime−static| ≤ 1`、end 分类、循环接缝；
- 播放期不挂 code hook；需要跳变事件只做只读差分；
- 同一 `FMD.EXE` 文件名不代表同一 build，地址/源入口必须按 hash 记录。

## 10. 产物/脚本索引

```text
drivers/fugam/docs/FMD.md
drivers/fugam/docs/FMD-STATUS.md
drivers/fugam/docs/FMD-BUILD-MAP.md
drivers/fugam/docs/FMD-LOOP-F8F9.md
drivers/fugam/docs/EXPORTER-PROFILES.md
build/_fmd_static_seq.py
build/_fmd_static_cut.py
build/_fuga_static_a.py
build/_fuga_static_b.py
build/_fuga_fmd5248_static.py
build/_collect_fmd.py
build/audit/static_a.csv
build/audit/static_b.csv
build/audit/static_fmd5248.csv
build/audit/dora_repeat.csv
build/audit/dora_repeat.md
build/audit/dora_state_diff.csv
```
