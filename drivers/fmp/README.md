# FMP2 / FMP3 —— 戯画「音痴君」v3.04

PC-98 上 TGL / 戯画 / 夢幻 三家共用的 MIDI 驱动。运行时自报：

```
ＦＭ＆ＭＩＤＩ音源バスター　音痴君。version 3.04月 (C)戯画
```

- 驱动：`FMP3.COM` / `FMP2.COM`（COM，`-m` 常驻）
- 壳：`tglfmp2.com` / `tglfmp.com`（HOOT 侧，`INT 0xD2` 协议）
- 数据：`.MGS`(GS) / `.MG2`(SC-88) / `.MD`·`.MMT`(MT-32/SC-55)；FM 的 `.MF2`/`.MFM` 不处理

## 现状

**21 个包全部跑通：573 个 MIDI（443 首不重复）**（GS / SC-88 / MT-32 / SC-55 变体），
曲名取自 HOOT `<titlelist>`。节拍按驱动分两套：

- 音痴君 19 包 522 个：`tick = (256 − TimerB) × 0.2991 ms`（INT 14h）；
- **FFMP ver1** 2 包 51 个（EDGE 25 首、SWORD DANCER 増刊号'93 13 首 × GS/MT-32）：
  `tick = 2 × [0x6EF] × [0x6F3] / 2457.6 ms`（**INT 08h + 8253 ch0**），
  见 [docs/TGL-FFMP-HANDOFF.md](docs/TGL-FFMP-HANDOFF.md)。

FM 版（`.M` / `.MFM`）按政策 PASS。

详见 [docs/FMP.md](docs/FMP.md)。
