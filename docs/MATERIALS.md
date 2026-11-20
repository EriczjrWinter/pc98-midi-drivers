# 素材获取

仓库里**不含任何游戏数据或驱动本体**。下面说明怎么自备。

## HOOT（主要来源）

本站收录 PC-98 等平台的音乐数据，每个包只有音乐相关文件（不含游戏本体），
**整个 pc98 库加起来才 122 MB**。

```
https://hoot.joshw.info/pc98/
```

压缩包命名即作品代号，例如 `ringout_98.zip`、`karanon_98.zip`。

### 元数据

`hoot.joshw.info` 只提供压缩包，**不提供 XML**。
作品的元数据（用哪个驱动、是否 MIDI、版本名）在 HOOT 发布版的 `xml/` 目录里：

```
xml/<会社名>.xml      每个会社一个文件
```

XML 里每个 `<game>` 条目包含：

| 项 | 说明 |
|---|---|
| `archive` | 压缩包名（**注意：可能是旧版命名**） |
| `<name>` | 作品全名，含 `[机种]` 前缀和 `(音源)` 后缀 |
| `name="midiout" value="1"` | 该变体是否有 MIDI 输出 |
| `<rom type="file">` | 该变体加载的文件列表 |

**重要**：`archive` 名可能和站点现名不一致（HOOT 改过名）。已知例子：

```
gaogao3        → gao3_98
karanonaka_98  → karanon_98
eime_21        → eime_98      （_21 = PC-9821，后来统一成 _98）
```

改名解析见 `tools/resolve_renames.py`。

## 自动下载

```bash
python tools/hoot_download.py            # 看计划
python tools/hoot_download.py --go       # 下载缺的
```

脚本读站点目录索引，跳过本地已有的，8 并发约 13 分钟下完 1700 个包。

## 其它来源

| 来源 | 用途 |
|---|---|
| [VNDB](https://vndb.org/) | 平台信息（`p98` / `win` / `fmt` …），有 API |
| [VGMRips](https://vgmrips.net/) | 其它机种的音乐包，多含曲目表 |
| 官方 MIDI / 原声 | 对照验证用（如 ZUN 的东方 MIDI） |

## 目录约定

脚本默认在以下位置找素材，可用参数覆盖：

```
D:\GamedataUnpack\hoot20251231\
├── pc98\       压缩包
└── xml\        会社 XML
```

## 版权

所有游戏数据、驱动、音乐版权归原权利人所有。
本仓库只包含**分析与转换代码**，以及由数据推导出的**格式文档**。
