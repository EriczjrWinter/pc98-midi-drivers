# FMP2 / FMP3 —— 戯画「音痴君」v3.04

PC-98 上 TGL / 戯画 / 夢幻 三家共用的 MIDI 驱动。运行时自报：

```
ＦＭ＆ＭＩＤＩ音源バスター　音痴君。version 3.04月 (C)戯画
```

- 驱动：`FMP3.COM` / `FMP2.COM`（COM，`-m` 常驻）
- 壳：`tglfmp2.com` / `tglfmp.com`（HOOT 侧，`INT 0xD2` 协议）
- 数据：`.MGS`(GS) / `.MG2`(SC-88) / `.MD`·`.MMT`(MT-32/SC-55)；FM 的 `.MF2`/`.MFM` 不处理

## 现状

戯画 5 包已导出 **184 个 MIDI**（约 109 首，GS + SC-88 双版本），
曲名取自 HOOT `<titlelist>`，节拍按 `tick = (256 − TimerB) × 0.2991 ms`。

TGL 12 包、夢幻 2 包待跑（同驱动同格式）。

详见 [docs/FMP.md](docs/FMP.md)。
