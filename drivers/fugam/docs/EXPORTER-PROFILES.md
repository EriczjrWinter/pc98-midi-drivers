# 风雅导出器能力档案（Exporter Profiles）

> **为什么不用"两代导出器"**：A/B 是按历史分的，不是按行为分的。
> 同一代里有 7 个 build，行为不通用——`marple98` 就是用 A/B 判据导坏的。
>
> **本表的作用**：新 build 来了，加一行，不是加一个脚本。
> 每验证一个 build，就把 `?` 填实一格。

---

## 一、字段定义

| 字段 | 含义 | 取值 |
|---|---|---|
| `driver` / `size` | 唯一标识（名字 + 字节数） | `FMD9.EXE` / 4774 |
| `load` | 装载/调用方式 | `INT D3: 0100/0300` |
| `cmds` | 板卡命令集 | 见各包日志 |
| `df` | 是否用 `$DF` 长消息 | `Y` / `N` |
| `tempo` | tempo 来源 | `$E0` / `$E0+$E1` |
| `end` | 适用的结束判据 | `fe,pass,loop,cycle,idle` 的子集 |
| `src` | 源变体规则 | `.GMD`=GS / `.MMD`=MT-32 |
| `verified` | 验收状态 | ✅ / ❌ / 🔄 / `?` |

---

## 二、档案表（2026-11-27 收口）

轨道表地址均为**实测 dump**（线性地址见备注：`fix_table_base()` 返回的就是线性地址，不要再加 `CB`）。

| driver | size | 轨道表 | 包 | 曲数 | end 判据 | 状态 |
|---|---|---|---|---|---|---|
| `FMD9.EXE` | 4774 | `0x0E64` | ama2_98 / ama2s_98 | 72 | `fe,pass` | ✅ |
| `FMD7.EXE` | 4998 | `0x0E09` | marple98 | 9 | `fe,pass,loop` | ✅ |
| `FMD13.EXE` | 5301 | `0x0F0F` | ama2m_98 | 34 | `fe,pass,loop` | ✅ |
| `FMD.EXE` | 4773 | `0x0C9E` | ama3_98 / ama3s_98 | 48 | `fe,pass,loop` | ✅ GS+MT-32 |
| `FMD.EXE` | 4969 | `0x0EBC` | ama4_98 / amakh_98 / deadfc98 | 56 | `fe,pass,loop` | ✅ |
| `FMD.EXE` | 4857 | `0x0EBC` | farce / hiragi / momoko / papa / reno / tlove12 / yumecol | 89 | 同 4969 | ✅（引擎与 4969 逐字节相同） |
| `FMD.EXE` | 5248 | `0x0E70` | image1_98 / image2_98 / p_club_98 | 24 | `fe,pass` + 全轨向量周期 | ✅ |
| `FMD.EXE` | 5365 | `0xD18`（mug-r） | bonnou3_98 / mug-r_98 | 18 | `fe,pass,loop` | ✅ |
| `FMD.EXE` | 4601 | `0x0CB8` | venus_98 | 17 | `fe,pass,loop` | ✅ |
| `FMD.EXE` | 4341 | `0x0CD0` | oerstd98 | 21 | `fe,pass,cycle` | ✅ |
| `FMD14.EXE` | 4341 | `0x0CD2` | sanina_98 | 12 | `fe,pass,loop` | ✅（与 FMD.EXE 4341 同大小、不同 build） |
| `FMD5.EXE` | 4485 | `0x0D1A` | fgsel1c / fgsel1m | 32 | `fe,pass,loop` | ✅ |

**合计 420 首**（与仓库 README 的完成清单一致）。

> `image2_98` / `venus_98` 曾在 A、B 两个静态管线里各出一份（音乐一致、编码细节不同）；
> 现只保留 B 分支那一份，A 的副本已删除。

---

## 三、收口记录

```text
2026-11-26  按 build 建档，标记各 build 的 df/tempo/end/src 待查项
2026-11-27  逐 build 实测轨道表地址；FMD7/FMD13/FMD5/FMD5248 全部跑通
            FC 链掩码差异：A/B 代 & 0xFFFC，5248 为 0x00FC
            周期口径最终改为「全轨状态向量连续三段一致」（见 FMD-LOOP-F8F9 §35）
```

新增 build 时只需：测一次轨道表地址 → 填一行 → 用 §四 的四条规则验一遍。

---

## 四、判定规则（每个 build 都必须满足）

```
① 默认参数导出（不加 --no-loop / --cutoff-ticks / --fixed-bpm），
   时长差 < 2%、音符差 < 5%（对 HOOT）
② end ∈ {fe, pass, loop, cycle, idle}，不能是 cap / timeout
③ 鼓音高集合与 HOOT 一致
④ 多入口包各出一套（GS→.GMD / MT-32→.MMD）
   禁止 cand[0]、按字母序、按文件大小选源
```

---

## 五、和现有两套导出器的关系

现有 `A 类导出器` / `B 类导出器` 不必立刻合并。建议：

```
短期：把本表当"配置文档"，两套导出器各自查表决定分支
中期：两套合并成一个引擎，差异全部下沉到 profile
```

**先文档、后代码**——避免为了"统一"再推翻一次已经能跑的导出器。

## 六、每个 build 对应的包与作品

| driver | size | 包 | 作品 |
|---|---|---|---|
| `FMD.EXE` | 4341 | `oerstd98` | [PC-9801] Oerstedia(MT-32) |
| `FMD.EXE` | 4601 | `venus_98` | [PC-9801] VENUS(GS) |
| `FMD.EXE` | 4773 | `ama3_98` | [PC-9801] Amaranth III(MT-32) |
| `FMD.EXE` | 4857 | `farce_98`<br>`hiragi_98`<br>`momoko_98`<br>`papa_98`<br>`reno_98`<br>`tlove12_98`<br>`yumecol_98` | [PC-9801] ファルス 誘惑白書(GS)<br>[PC-9801] 柊坂の旧館(GS)<br>[PC-98] Momoko-chan for Me (����������� for me �`���K���Ō�w�ҁ`) (SC-55)<br>[PC-9801] パパラッチ(GS)<br>[PC-9801] RE-NO STAYIN' ALIVE(GS)<br>[PC-9801] TRUE LOVE 純愛物語 Ver1.2(GS)<br>[PC-98] Yumemizaka &amp; Collections (������R���N�V�����Y) (SC-55) |
| `FMD.EXE` | 4969 | `ama4_98`<br>`amakh_98`<br>`deadfc98` | [PC-9801] Amaranth IV(GS)<br>[PC-9801] Amaranth KH ～シュテラール王国建国譚～(GS)<br>[PC-9801] 新世紀興亡史 デッドフォース(MT-32) |
| `FMD.EXE` | 5248 | `image1_98`<br>`image2_98`<br>`p_club_98` | [PC-9801] イマージュ(MT-32)<br>[PC-9801] イマージュ2(MT-32)<br>[PC-9801] パノラマ倶楽部(GS) |
| `FMD.EXE` | 5365 | `bonnou3_98`<br>`mug-r_98` | [PC-9801] 煩悩予備校3(MT-32)<br>[PC-9801] Mug-R(GS) |
| `FMD13.EXE` | 5301 | `ama2m_98` | [PC-9801] Amaranth II ミュージックディスク(MT-32) |
| `FMD14.EXE` | 4341 | `sanina_98` | [PC-9801] サニーナの伝説(MT-32) |
| `FMD5.EXE` | 4485 | `fgsel1c`<br>`fgsel1m` | [PC-9801] 風雅セレクション① ～カルカッタ～(MT-32)<br>[PC-9801] 風雅セレクション① ～メイズクエスト～(MT-32) |
| `FMD7.EXE` | 4998 | `marple98` | [PC-9801] ま～ぷる・まぢっく(MT-32) |
| `FMD9.EXE` | 4774 | `ama2_98`<br>`ama2s_98` | [PC-9801] Amaranth II(MT-32)<br>[PC-9801] Amaranth II(GS) |

## 备注：表地址返回值

- `find_track_table()` / `fix_table_base()` 返回的是**线性地址**（如 `0x10F70`），
  不要再加 `CSBASE`；再加一次会读到全零表。
- FMD.EXE 5248 的 FC 目标掩码是 `0x00FC`（低 8 位对齐 4）；
  A/B 代是 `0xFFFC`。当前 6 首实测两种掩码结果相同，掩码不是这 6 首的差异原因。
- 旧动态版不是正确性真值；自相似会把半周期/整周期混在一起。正确性仍按
  `|runtime−static| ≤ 1`、end 分类、循环接缝。
