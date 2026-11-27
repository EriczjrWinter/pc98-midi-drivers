# Alice Soft —— System3 引擎的 AMUS 音乐

> **状态（2026-11-26）：已拍板。** 两条线都收口了——Windows 侧 21 首 MIDI 导出并验证过，
> PC-98 侧的 FM 音色也解出来了，做成了可播的音色库 + 重映射后的 MIDI。

## 和其它条目不一样

别的条目是「一个私有 MIDI 驱动 + 曲数据」。**Alice Soft 这边不同**，要分两条线看：

| 平台 | 音乐路径 | 我们解到哪 |
|---|---|---|
| **Windows**（`system3.exe`） | 游戏自己的引擎解析 `AMUS.DAT`，直接 `midiOutShortMsg` 发给 MIDI 设备 | ✅ **全解**，21 首导出并逐项验证 |
| **PC-98**（`MAKO.COM`） | 通用 OPN/OPNA **FM** 驱动 | ✅ **全解**，音色提取成 OPN 音色库，21 首 MIDI 已重映射 |

也就是说：**A 社没有 PC-98 专用的 MIDI 驱动**。它的 MIDI 出口在 Windows 版的 exe 里，
而 FM 出口是一个**通用的、不带音色的** OPN 驱动——音色两版各有一套，见下。

## 手法：不解析数据，把引擎跑起来

`AMUS.DAT` 既不是 MML 也不是压缩 MIDI，是「乐句表 + 命令流」。但它最大的坑不在数据本身，
而在**音色是七层间接**：

```
游戏ID(哈希) → MDA 资源 → 曲号 → 256字节块 → 9字节记录 → 驱动 → 合成器
```

每一层的键都是运行期才确定的。静态读文件只能看到字节，只有让引擎跑起来才知道「第 21 首会去取第 21 块」。

所以做法是：**在 Unicorn 里跑 `system3.exe` 的音乐引擎，hook `midiOutShortMsg`**。
产物是「引擎本来想表达的东西」，不是对格式的猜测。

详见 [docs/AMUS.md](docs/AMUS.md)。

## 结果

| 对照物 | 结果 |
|---|---|
| 第 1 首 vs 官方参考 `AmbivalenZOP.mid` | 7303/7303 音符，音高直方图 0 差异，27/27 program change |
| 第 21 首 vs PC-98 实机录音 | 6 个通道 program 全对，音高分布 0 差异 |

21 首全部导出。

## 两版的音色层：各有一套，但能对上

| | MIDI 版（Windows） | FM 版（PC-98） |
|---|---|---|
| 音色在哪 | `system3.exe` 的 MDA 资源，每曲一块 | **`AMUS.DAT` 每曲块内部**，`u16[0]` 偏移处 |
| 每条大小 | 9 字节（idx/bank/program/vol/pan/chorus/base/reverb） | **43 字节**（alg/fb + keymask + 4 operator × 6 寄存器） |
| 每曲条数 | 9 条 voice + 3 条固定声部 | 1–10 条（21 首共 121 条，去重 26 种） |
| 性质 | MIDI 音色号（GM 语义） | 芯片寄存器原始值（无 GM 语义） |

**两版唯一的桥是 MDA 记录里的 `idx`**：它等于 FM 块里第 `idx` 条 43 字节音色。
⇒ `(曲号, program) → idx → OPN 音色`，是确定性的。

验证：第 1 首 5 条 FM 通道、第 21 首 3 条，首个 `F5` 与推算值全部命中；
其余曲子因通道共用「引子」乐句（`0xFF` 需按行表跳转）没做静态全验，
改由 libOPNMIDI 实际播放确认听感一致。

## 产物（`build/_mako_lab/`）

```
ambi_fm.wopn        26 个 FM 音色 + SSG 方波替身 + GM 鼓，OPNA 模式
midi_fm/            21 首 MIDI，program change 已重映射到上面这个库的槽号
midi2fm_mapping.csv 曲 × 通道的 idx/bank/program/patch 对照
precheck_report.md  完整证据链（字节、地址、验证表、工具说明）
instruments.csv     121 条音色 × 4 operator 的全部寄存器解码
```

## 目录

```
src/
  amus_emu.py       Unicorn 装载 PE、导入打桩、接管分配器/文件读取
  amus_ticks.py     tick 边界挂钩、按速度精确累积时间
  amus_allsongs.py  批量导出（含 MDA 音色块提取、固定声部）
  smfio.py          极简 SMF 读写
  extract_mda.py    从 .rsrc 提取 MDA 资源
  exe_dis.py        capstone 反汇编辅助
  rename_tracks.py  按曲名重命名
  midi_to_wopn.py   把 MIDI 的 program change 改写成 WOPN 槽号
docs/
  AMUS.md                 完整格式记录（容器 / 字节码 / 时间轴 / MDA / 8 个坑 / MAKO 小结）
  MAKO-FM-EXPERIMENT.md   实验交接单（顶部有状态与"被证伪的观点"）
```

## 用法

```bash
pip install unicorn capstone

# Windows 侧
python src/extract_mda.py        # 从 system3.exe 提取 MDA 资源
python src/amus_allsongs.py      # 21 首全导出，约 15 秒
python src/amus_allsongs.py 1    # 只跑第 1 首

# PC-98 侧（只需要 PC-98 版的 AMUS.DAT，不需要 system3.exe）
python ../build/_mako_lab/wopn_build.py       # AMUS.DAT → ambi_fm.wopn
python src/midi_to_wopn.py --map-csv ../build/_mako_lab/midi2fm_mapping.csv \
       --song 1 --bank ../build/_mako_lab/ambi_fm.wopn \
       --ssg-channels 3,4,5 -o 01_fm.mid "01 オープニング.mid"
```

## PC-98 侧（MAKO）的结论

`MAKO.COM` 是 **3907 字节的通用 OPN/OPNA 驱动**（`OPN,OPNA driver 'MAKO' ... Ver 2.43`，
`-a` 切 YM2608、`-n` 切 YM2203、`-p0..3` 选端口基址 `088h`…`388h`），**里面没有音色库**——
音色由调用方经 `INT 40h` 喂进去：`AH=00` 时 `DS:SI` 指向的就是整曲数据块，块内 `u16[0]` 处即音色表。

* **9 条通道固定分工**：内部 ch0-2 / ch6-8 → FM 0-5；ch3-5 → **SSG（方波）**，
  SSG 三条没有音色可切（选音色函数对 ch3-5 直接返回）。
* **端口按通道分组**：FM 0-2 在 `base+0/+2`，FM 3-5 在 `base+4/+6`
  （PC-98 上即 `0x188/0x18A` 与 `0x18C/0x18E`）。基址默认 `0x0088`，要 `0x188` 得带 `-p1`。
* **音序器自带**：`0xF4` tempo → 定时器分频（`0x5161 / tempo`）、`0xF5` 选音色、
  `0xF9` 音量（只改载波 TL，不动包络）。

## 已知限制

- Windows 侧：第 2–21 首截在 300 秒（循环 BGM，引擎不会自然结束）。
- FM 侧：**ch3/4/5 的 SSG 用方波替身**——WOPN 是 FM 音色库，装不下 AY 的 16 种包络波形。
- FM 侧：打击乐目前借的是 GM 鼓库；本作自己的鼓音色（P01/P02）缺「鼓音高表」，还没接上。
- 音色映射的静态验证只覆盖 4 首（其余靠听感 + 槽位自洽检查）。
