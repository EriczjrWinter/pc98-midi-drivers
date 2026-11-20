# mdrvcap —— MDRV98 的 MIDI 抓包器

只跑驱动「MIDI 那条腿」，把 C/G 变体（`.FMD`）的 MIDI 事件抓出来写成 SMF。

```
DOFMD_98.BIN（INT 7F 前端）
        │  板命令 0x7E0
        ▼
   MDRV98 表 B（0x17D4）
        │  Timer B 中断（INT 12h → 0x5BF）
        ▼
   0xE0D0 数据 / 0xE0D2 状态（ACK 0xFE）
        │
        ▼
   字节流 → SMF
```

表 A 的 FM 音乐推进完全不跑；不需要音频合成，也不需要屏幕。

## 模块

| 文件 | 作用 |
|---|---|
| `model.py` | 16 位实模式最小模型：装载 BIN@0x600 / 驱动@0xFA0，手动派发 `INT`（unicorn 16 位模式不自动走 IVT），端口回读 |
| `capture.py` | `CapSim`：BIN 启动 → 板命令 1（加载+播放）→ 反复触发 `INT 12h` → 抓 `0xE0D0` 的字节 |
| `smf.py` | 字节流 → 消息（running status、SysEx），以及时间线查看 |
| `export.py` | 写 SMF（tempo、PPQ、结尾补 note-off），按参考 MIDI 定长 |
| `batch.py` | 一部作品全曲批量导出 + 与参考逐首对比 |
| `calib.py` | 用 Win95 GM 版参考反解「一次 Timer B 中断 = 多少毫秒」（DP 对齐 + 最小二乘） |
| `loop.py` | 没有参考时用自相似估循环长度（只保证事件，不保证曲长） |

## 用法

```bash
# 单曲
python -m mdrvcap.export cl_98 CR001G.FMD out.mid

# 整部（GS/MT-32 任选 C.FMD / G.FMD）
python -m mdrvcap.batch cl_98 G.FMD D:/out/cl_98_G

# 只看抓到的字节流
python -m mdrvcap.capture cl_98 CR001C.FMD 200
```

依赖 `unicorn`（跑 16 位代码）、`mido`（写/读 SMF）。
驱动本体 `DOFMD_98.BIN` / `MDRV98` 放在上一级目录（不进仓库）。

## 关键常量

| 常量 | 值 | 说明 |
|---|---|---|
| `TICK_MS` | **4.9082** | 一次 Timer B 中断。由两条独立参考拟合：4.9082 / 4.9008 |
| `DATA_SEG` | `0x4000` | 曲子数据装载段 |
| `IVT_IRQ` | `0x12` | 驱动自己装的处理器（`0x5BF`） |
| PPQ | 480 | 与参考 MIDI 一致 |

## 硬件语义（模型里必须实现的几条）

- `0x188` 读 = 状态：bit0 Timer A、bit1 Timer B、bit7 busy；**读不清**，写 `0x27` 才清。
- `0x18A` / `0x188` 回读：功能 0 靠「写 `0xBF` 再读回」判断声卡存在。
- `0xE0D2` 状态：bit7 有数据、bit6 忙；`0xE0D0` 读回 `0xFE` 当 ACK。
- 板命令走 `0x7E0`（0=设置，1=加载+播放），数据指针走 `0x7D4`/`0x7D6`。

## 覆盖边界

只支持「独立驱动」这一种打包方式：

| 路线 | 形态 | 支持 |
|---|---|---|
| **A 独立驱动** | `DOFMD_98.BIN` + `MDRV98` / `ZYXMD`（11519 字节） | ✅ 6 个包全部导出：cl_98(46)、you4_98(46)、zatuon_98(17)、gbakuten_98(15)、kyouiku_98(24)、laidi1_98(15) |
| **B `DOFMDX98.COM`** | 774 字节 DOS 装载器 + 游戏 EXE（驱动在 EXE 里） | ❌ 没有这条装载路径 |
| **C `MDRV98.COM`** | 11987 字节 DOS 常驻版 + `mlp_hoot.com`，`.MUS` 数据 | ❌ 不同驱动/不同数据 |

注意：

- A 路线的 6 个包驱动内容完全相同（sha1 `e8177a9bf8a3`），名字可能是 `MDRV98` 或 `ZYXMD`。
- `herceq_98` 的 `ZYXMD` 是 **5801 字节**的另一个构建，不要直接套。
- B 路线的 `.CM/.GS` 数据同样是 `68V2`，**可以用 A 的驱动解析**，但那是串驱动，
  输出不能当原版结果（见 `docs/MDRV98.md` 的 brm2_98 记录）。

## 局限

- 只覆盖 `pc98vx` + **FMD/MSC**（`68V2`）的作品。
- 时间分辨率 = 一次 Timer B 中断（4.9 ms），驱动本身就只有这个分辨率。
- 没有参考 MIDI 时长度只能估：自相似找循环会把「段落重复」误判成整首循环。
