# FMD 构建 / 包名 / 表地址对照（2026-11-27）

> 所有地址都按 **build** 区分；同名 `FMD.EXE` 不代表同一驱动。
> 表地址是加载后 `CSBASE + offset` 的 offset。

## 一、总表

| 驱动 | 大小 | SHA256 前缀 | HOOT 包 | 日文原名 / 标题 | 表 offset | 状态/说明 |
|---|---:|---|---|---|---:|---|
| `FMD9.EXE` | 4774 | `ba05444e` | `ama2_98` | Amaranth II(MT-32 / Emulation) | `0x0E64` | A；OPENING 335/9461 |
| `FMD9.EXE` | 4774 | `ba05444e` | `ama2s_98` | Amaranth II(GS) | `0x0E64` | A；MT/GS 两套 |
| `FMD13.EXE` | 5301 | `91904cc5` | `ama2m_98` | Amaranth II ミュージックディスク(MT-32 / Emulation / GS) | `0x0F0F` | A；34 首 loop29/pass5 |
| `FMD9G.EXE` | 5301 | `91904cc5` | `ama2_98` | 与 FMD13 同 hash 的别名 | `0x0F0F` | 同 FMD13，不单独算 build |
| `FMD.EXE` | 4341 | `beea535a` | `oerstd98` | Oerstedia(GS / MT-32 / Emulation) | `0x0CD0` | B；OERS_018 cycle |
| `FMD.EXE` | 4601 | `c9ce5a6a` | `venus_98` | VENUS(GS) | `0x0CB8` | A/B 都通过 |
| `FMD.EXE` | 4773 | `b3902511` | `ama3_98` | Amaranth III(GS / MT-32 / Emulation) | `0x0C9E` | B；MT 24 + GS 24 |
| `FMD.EXE` | 4857 | `f6e72c26` | `farce_98` | ファルス 誘惑白書(GS) | `0x0EBC` | B 1.72 组 |
| `FMD.EXE` | 4857 | `f6e72c26` | `hiragi_98` | 柊坂の旧館(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4857 | `f6e72c26` | `momoko_98` | ももこちゃん for Me 見習い看護婦編(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4857 | `f6e72c26` | `papa_98` | パパラッチ(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4857 | `f6e72c26` | `reno_98` | RE-NO STAYIN' ALIVE(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4857 | `f6e72c26` | `tlove12_98` | TRUE LOVE 純愛物語 Ver1.2(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4857 | `f6e72c26` | `yumecol_98` | 夢見坂コレクションズ(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4969 | `77ebe2d1` | `ama4_98` | Amaranth IV(GS) | `0x0EBC` | B 1.71；TLOVE_08 197/19006 |
| `FMD.EXE` | 4969 | `77ebe2d1` | `amakh_98` | Amaranth KH ～シュテラール王国建国譚～(GS) | `0x0EBC` | 同上 |
| `FMD.EXE` | 4969 | `77ebe2d1` | `deadfc98` | 新世紀興亡史 デッドフォース(GS / MT-32 / Emulation) | `0x0EBC` | 同上 |
| `FMD.EXE` | 5248 | `93552bfd` | `image1_98` | イマージュ(MT-32 / Emulation) | `0x0E70` | 7 首，`.MDI` |
| `FMD.EXE` | 5248 | `93552bfd` | `image2_98` | イマージュ2(MT-32 / Emulation) | `0x0E70` | 14 首，A/B |
| `FMD.EXE` | 5248 | `93552bfd` | `p_club_98` | パノラマ倶楽部(GS) | `0x0E70` | 3 首，`.MI`；TITLE loop |
| `FMD.EXE` | 5365 | `6903b7ea` | `bonnou3_98` | 煩悩予備校3(MT-32 / Emulation) | 未单独 dump | 与 mug-r 不同 hash |
| `FMD.EXE` | 5365 | `b676d587` | `mug-r_98` | Mug-R(GS) | `0x0D18` | B；hash 独立 |
| `FMD14.EXE` | 4341 | `75277fa9` | `sanina_98` | サニーナの伝説(GS / MT-32 / Emulation) | `0x0CD2` | **不是 FMD 4341** |
| `FMD5.EXE` | 4485 | `8d4f8913` | `fgsel1m` | 風雅セレクション① ～メイズクエスト～(MT-32 / Emulation) | `0x0D1A` | 18 首，`/e` |
| `FMD5.EXE` | 4485 | `cdb4af30` | `fgsel1c` | 風雅セレクション① ～カルカッタ～(MT-32 / Emulation) | `0x0D1A` | 11 首，`/e` |
| `FMD7.EXE` | 4998 | `f6c5709f` | `marple98` | ま～ぷる・まぢっく(MT-32 / Emulation) | `0x0E09` | 9 首 |
| `FMD.EXE` | 7051 | `f20427a9` | `ayayo2_98` | はっちゃけあやよさんII 「いけないホリディ」 | — | **已移出风雅** → `drivers/emd98` |
| `FMD.EXE` | 22392 | `69a97135` | `sematte_98` | せまってみたい | — | **已移出风雅** → `drivers/abiko98` |

## 二、真正的同一/近似 build

| 对比 | 差异 | 结论 |
|---|---:|---|
| FMD13 / FMD9G 5301 | 0 | 完全同 hash `91904cc5` |
| FMD5 `fgsel1m` / `fgsel1c` | 5 字节 | 同族，仍按两包记录 |
| FMD.EXE 4341 / FMD14 4341 | 3443 | **不同代码**，表 `0xCD0` vs `0xCD2` |
| FMD.EXE 4857 / 4969 | 4783 | 不能按大小合并 |
| FMD.EXE 5365 bonnou3 / mug-r | 4421 | 不能合并；mug-r 表 `0xD18` |
| FMD7 4998 / FMD9 4774 | 4692 | 不同分支 |

## 三、地址不能通用的实例

```text
FMD9/FMD13 A 系     0x0E64 / 0x0F0F
FMD.EXE 常规 B       0x0EBC
FMD.EXE 5248        0x0E70
FMD.EXE 4601 venus  0x0CB8
FMD.EXE 4341 oerstd 0x0CD0
FMD14 4341 sanina   0x0CD2
FMD.EXE 5365 mug-r  0x0D18
FMD5                0x0D1A
FMD7                0x0E09
```

同名 `FMD.EXE` 的 0xEBC / 0xE70 / 0xCB8 / 0xCD0 / 0xD18 都是不同 build 的结果，
不能按文件名复用。

## 四、源文件/入口差异

```text
ama2/ama3: .GMD 与 .MMD 可能是不同机种/编排
image1:    .MD 是数据，入口 .MDI
p_club:    .MD 是数据，入口 .MI
sanina:    .GS / .FM / .LA
FMD5:      .MMD + /e
FMD7:      .MMD
ayayo2:    .EMI + EMD_98.COM（移出）
sematte:   .MUS/.ONS + ABIKO_98.COM（移出）
```

## 五、当前总状态

```text
A 100 / B 263 / FMD5 32 / FMD13 34 / FMD7 9 / FMD5248 10 = 448
358 回归：358 不变；5 首预期修正
交付：build/hootcap/fmd-collection/
```

## 六、FMD5248 入口与静态收口

`FMD.EXE` 5248 的 `.MD` 不是 `.GMD/.MMD` 那种直接歌曲流：

```text
image1_98  .MDI = 入口；.MD = 数据
p_club_98  .MI  = 入口；.MD = 数据
```

已按 `0201(.MD) → 0100(.MDI/.MI) → 0300` 处理，表 `0x0E70`。
静态周期改用**全轨状态向量** `(seg,cur,anchor,depth,en)` 连续三段一致，
不再按 depth 选层。

10 首已并入 `fmd5248/`；TITLE SHA 保持 `1fc94d30d249`。
