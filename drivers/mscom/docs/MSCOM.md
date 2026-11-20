# MS.COM（LEAF）—— `.MD` / `.MID` 格式

雀鬼和 Filsnown 用的 MIDI 驱动。**这是本库里第二个靠仿真解出来的驱动。**

## 结论先说

**`MS.COM` 和 MMDR 是同一套 TSR 框架的两个分支。**

| | MMDR（雫/痕） | MS.COM（雀鬼/Filsnown） |
|---|---|---|
| 大小 | 3218 / 3954 B | **6531 B** |
| 加载器 | `mmdr_98.com` 400 B | **`ms_98.com` 400 B** |
| 定时器 | `INT 08h` | **`INT 08h`** |
| 功能调用 | `INT 7Eh` | **`INT 7Fh`** |
| 8253 | `out 0x77/0x71` | **`out 0x77/0x71`** |
| MIDI 口 | `0xE0D0/0xE0D2` | **`0xE0D0/0xE0D2`** |

连加载器都同样是 400 字节——**这不是巧合，是同一条技术路线**。

## 数据格式：加密的

```
52 4d 05 00 00 02 20 20 20 20 | e8 cc ad 54 39 39 ...
└─"RM"┘ └版本5┘    └ 空格 ┘     └── 高熵数据 ──┘
```

- 魔数是 **`RM`**，版本 5
- 后面是**压缩/编码过的数据**，看不到结构
- `.MD`（Filsnown）和 `.MID`（雀鬼）**是同一种格式**，只是后缀不同

**所以静态解析走不通。** 这和 MMDR 的 `.MD`（8253 计数 + 通道指针表，明文）
完全是两回事——**同名 `.MD`，不同格式**，又一个"同名不等于同构建"的例子。

## API

`INT 7Fh`，**`AX = 功能号 << 8`**（即 AH = 功能号）：

```asm
cmp word ptr [0x814], 0    ; 初始化了吗
je  退出
shr ax, 7                  ; AX>>7 = 跳转表字节偏移（偶数）
mov di, ax
call word ptr [di + 0x514] ; 跳转表
```

跳转表 @ `0x514`：

| 功能 | 入口 | 作用 |
|---|---|---|
| 0 | `0x164F` | 设 MIDI 端口（`0xE0D2`/`0xE0D0`）与时间常数 |
| **1** | `0x1716` | **播放**：从 `ES:BX` 取数据指针 |
| 2 | `0x1869` | 停止 |
| 3+ | ... | 其它（未细查） |

**功能 1 的数据指针走 `ES:BX`，不是 `DX`。**

## 仿真要点

`drivers/mscom/src/mscom_emu.py` 是从 `companies/leaf/src/mmdr_emu.py` 改的。
改动只有四处：

1. `IVT_API = 0x7F`（原来是 `0x7E`）
2. `INT 21h` 要处理 **AH=35h（取向量）/ 25h（设向量）**，
   自己维护一份 IVT 表——MMDR 那边不需要
3. 播放调用：`AX=0x0100, ES=DATA_SEG, BX=0`
4. 数据文件整块写进 `DATA_SEG`，不用管里面的加密——**驱动自己解**

MMDR 的 `scan_timer_writes()`（8253 计数 → 毫秒）和 `smf_build.build_ms()`
**原样复用**，一行没改。

### 最终采用的导出参数

```
silence_ticks = 10**9     ← 等于不判静音，让驱动跑到自己停
不做循环裁剪
```

原因见下面「关于长度」一节——试过的四种裁剪方案都不成立，
最后决定**不裁剪**，接受部分曲目偏长。

## 驱动是同一构建

雀鬼和 Filsnown 两个包里的 `MS.COM` **md5 完全相同**：

```
dr^2_98      MS.COM  6531 B  md5 cc90f4a7e01c...
filsnown_98  MS.COM  6531 B  md5 cc90f4a7e01c...
```

所以这不是「同名不同构建」，是真的同一个文件——
两家作品共用一份驱动，只是数据后缀不同（`.MID` vs `.MD`）。

## 成果

```
DR²ナイト雀鬼    18/18 首
Filsnown         43/43 首
```

全部能被标准 MIDI 库读取。

## 曲名

| 游戏 | 来源 |
|---|---|
| DR²ナイト雀鬼 | 「NIGHT JANKI ~ Team-Ios GAME Sound collection Vol.1」(LFCD-0001) |
| Filsnown | 「Filsnown ~ Team-Ios GAME Sound collection Vol.2」(LFCD-0002) |

两者在 [VGMRips 的 pack 页面](https://vgmrips.net/packs/pack/dr2-night-janki-nec-pc-9801-opna)
有完整对照。文件数与曲目数正好相等（18 / 43），按下标一一对应。

雀鬼的映射关系：

```
LEF_GSLG → 01 Brand Logo
MRJ_GS01 → 02 Trance Mind
...
MRJ_GS13 → 14 Piece for Memory
MRJ_GSG1 → 15 Game Over      ← GSG 是四个短音效
MRJ_GSG4 → 18 Appearance!!
```

## 关于长度：已决定不追

**游戏里这些曲子本来就是无限循环的**，所以「一遍」有多长没有客观答案。
部分曲目偏长（驱动把循环播了不止一遍）**不影响曲子本身的正确性**，
决定不再处理。

如果以后要精确截断，正解是**监视数据指针的回跳**——
驱动循环时一定会改写数据指针，回跳的那一 tick 就是循环点，
在仿真里 hook 内存写就能拿到，不用猜。

## 走过的弯路（记录，避免重走）

1. **静音判定结束**（`silence_ticks=800`）
   → 真实曲子里有 1000+ tick 的休止，会被误判成结束
   （`06 Attack the Time` 只剩 1.8 秒）。

2. **字节流窗口比对截循环**（`window=512/1024`）
   → 密集鼓点会被误判成整曲循环，有的截多有的截不住。

3. **用 VGMRips 的时长截断** ❌ **这个方法不成立**
   → **VGM 录的是 FM 版，MIDI 是另一套编曲，长度本来就不该相同。**
   雫和痕就是活例子：FM 和 MIDI 的编曲长度差一截。

4. **字节流周期检测**
   → 理论上最干净，但实测没检出周期，说明驱动每轮输出不完全一致。

## 文件

```
src/mscom_emu.py    仿真运行器（含导出）
src/probe_api.py    API 功能号探测（存档，可删）
data/               解出来的数据（未提交）
docs/MSCOM.md       本文
```

导出成品在 `D:\music\MSCOM_TEST\`：
```
DR2ナイト雀鬼\   18 首
Filsnown\        43 首
```

> 注：这两个游戏的**同人 MIDI 已经有现成的**
> （用户收藏里的 `RINGOUT` 和 `time stripper` 用的是同一个 DOFMDX98 家族，
> 不是本驱动；本驱动对应的是雀鬼/Filsnown，暂无现成对照）。
