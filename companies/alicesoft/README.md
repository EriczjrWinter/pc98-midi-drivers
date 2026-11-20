# Alice Soft —— System3 引擎的 AMUS 音乐

## 和其它条目不一样

别的条目是「一个私有 MIDI 驱动 + 曲数据」。**Alice Soft 这边不同**，要分两条线看：

| 平台 | 音乐路径 | 我们解到哪 |
|---|---|---|
| **Windows**（system3.exe） | 游戏自己的引擎解析 `AMUS.DAT`，直接 `midiOutShortMsg` 发给 MIDI 设备 | ✅ **全解，21 首导出** |
| **PC-98**（MAKO.COM） | 通用 OPN/OPNA **FM** 驱动 | ⚠ 驱动本身解了，音色未提取 |

也就是说：**A 社没有 PC-98 专用的 MIDI 驱动**。它的 MIDI 出口在 Windows 版的 exe 里。

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
docs/
  AMUS.md           完整格式记录（容器 / 字节码 / 时间轴 / MDA / 8 个坑）
```

## 用法

```bash
pip install unicorn capstone

python src/extract_mda.py        # 从 system3.exe 提取 MDA 资源
python src/amus_allsongs.py      # 21 首全导出，约 15 秒
python src/amus_allsongs.py 1    # 只跑第 1 首
```

## PC-98 侧（MAKO）的结论

`MAKO.COM` 是 **3907 字节的通用 OPN/OPNA 驱动**（`-a` 切 YM2608、`-n` 切 YM2203、`-px` 换端口），
**里面没有音色库**——音色由调用方通过 `INT 40h` 喂进去。

它和 AMUS 的关系：同样的 `.DAT` 数据，Windows 侧翻译成 MIDI，PC-98 侧翻译成 FM 寄存器。
**数据层一致，只有驱动不同。**

要提取 FM 包络参数，得 hook 它的 `out dx, al`（`0x6B7` / `0x6C2` / `0x6E1` / `0xBB4`，端口在 `cs:[0xa83]`）。
**未做。**

## 已知限制

- 第 2–21 首截在 300 秒（循环 BGM，引擎不会自然结束）
- 还原的是「引擎的意图」，不是当年 OPNA 芯片的波形
