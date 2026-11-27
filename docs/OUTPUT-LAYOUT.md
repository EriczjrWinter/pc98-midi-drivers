# 输出目录约定（2026-11-26）

> 背景：FMD 前后经过多个会话，各自建了自己的输出目录（`build/hootcap/fmd`、
> `fmd_b`、`build/_fmd_tmp/...`、`build/ama4_single/` 等），导致三件事反复出问题：
> ① 审计脚本认不出"已做"；② 同一首曲子有多个版本的产物；
> ③ 产物被复制进 `D:\music` 的参照目录，被当成"独立参照"。

## 一、标准布局

```
build/hootcap/<driver>/<pack>/<song>.mid        ← 交付产物
build/hootcap/<driver>/<pack>/_report.csv       ← 每包一份报表
build/hootcap/<driver>/_summary.md              ← 驱动级汇总
build/_scratch/<session>/                       ← 会话临时产物（随时可删）
```

`<driver>` 用短名：`fuga-a` / `fuga-b` / `fuga5` / `mmd` / `fmp` / `msdrv` / `mdrv98` …

**判据**：只要在 `build/hootcap/<driver>/<pack>/` 下出现 `.mid`，审计就认为"这个包已做"。

## 二、三条硬规则

1. **产物只写 `build/`，绝不写进参照目录**（`D:\music\90S Galgame music\` 等）。
   参照目录只读——往那里写东西，下次审计就会把自己的产物当参照。
2. **一个包只认一个目录**。同一包的新版本写到 `<pack>_v2/`，旧版保留，由 `_report.csv` 说明哪个是当前版。
3. **临时脚本和中间产物进 `build/_scratch/<session>/`**，不进 `hootcap/`。

## 三、现存目录的映射（迁移参考）

| 现路径 | 归属 | 建议 |
|---|---|---|
| `build/hootcap/fmd/` | A 代（FMD9）70 个 | → `fuga-a/<pack>/` |
| `build/hootcap/fmd_b/` | B 代批量 | → `fuga-b/<pack>/` |
| `build/_fmd_tmp/fgsel_*` | FMD5 | → `fuga5/<pack>/` |
| `build/_fmd_tmp/`、`build/ama4_single/` | 调试产物 | → `_scratch/` |
| `build/bmidi*`、`build/mdt/`、`build/out/`、`build/mdrv4/` | 其他驱动 | 保持，但补 `<pack>/_report.csv` |

## 四、参照目录的维护

- `D:\music\90S Galgame music\` 只放**外部来源**（WIN 版 MIDI、HOOT 抓取、实机录音）；
- 审计脚本必须先做 **sha1 自查**：参照文件的 sha1 若等于 `build/` 下任一产物 → 判 `ref_indep=0`；
- 已知污染：`[PC-9801] Amaranth II(GS)`、`[PC-9801] Amaranth II(MT-32)` 两个目录
  曾存放我们自己的导出（现为空）。**这两个目录不能当参照。**

## 五、新会话开工模板

```
1. 产物目录：build/hootcap/<driver>/<pack>/
2. 报表：每包一份 _report.csv（字段见 drivers/fugam/docs/AUDIT.md）
3. 临时文件：build/_scratch/<session>/
4. 绝不往 D:\music 写任何东西
```

## 六、扫描这些目录时注意

作品目录名含 `[ ]`（如 `[PC-9801] Amaranth II(GS)`）：

- Python：用 `Path.rglob()` 或 `os.walk`，**不要用 `glob.glob`**（方括号会被当字符类，静默返回空）；
- PowerShell：用 `-LiteralPath`，不要用 `-Path`；
- 详见 内部审查清单（不随库发布）「路径与文件名里的坑」。

