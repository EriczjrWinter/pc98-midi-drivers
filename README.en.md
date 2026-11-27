# Archaeology of PC-98 Private MIDI Drivers

[中文](README.md) | **English** | [日本語](README.ja.md)

Much of the game music on the PC-98 uses a "**data + driver**" structure:
the data is just an event script, and the real format specification lives
inside a resident driver of a few hundred bytes to a few KB.

The problem: **the drivers have no documentation. Only their runtime behaviour is the spec.**

What this repository does is dig up these drivers one by one, run them,
and get the music out.

> Core technique: **don't parse the data — let the driver run and capture its output.**
> When the format is already documented we parse it statically instead.
> Whichever is less work, not whichever is more orthodox.

---

## Completed

| Driver | Company | Method | Titles | Output |
|---|---|---|---|---|
| [**MMDR**](companies/leaf/) | LEAF | Run driver | Shizuku / Kizuato | ✅ **51 tracks**, cross-verified |
| [**MS.COM**](drivers/mscom/) | LEAF | Run driver | Night Janki / Filsnown | ✅ **61 tracks** |
| [**MMD**](drivers/mmd/) | KAJA (23 companies) | Static parse | 36 titles / 40 packs | ✅ **756 tracks** (GAL 460 / non-GAL 296) |
| [**MDRV98**](drivers/dofmdx/) | D.O. / ZyX | Run driver + capture | 6 standalone packs + 11 B-route packs + 4 C-route titles | ✅ **117 tracks** (GS / MT-32) + **678** (B route) + **50** (C-route `.MUS`) + **507** (.MDT transcriptions) |
| [**MSDRV4**](drivers/msdrv/) | Black Package | Run driver + capture | 7 packs (of 9) | ✅ **129 MIDIs** (82 tracks × GS / SC-88) |
| [**FMP**](drivers/fmp/) | TGL / GIGA / Mugen | Run driver + capture | 21 packs (19 Onchikun + 2 FFMP ver1) | ✅ **573 MIDIs** (443 tracks, GS/SC-88/MT-32/SC-55) |
| [**FUGA / FMD**](drivers/fugam/) | Fuga System et al. | Run driver + static sequencing | 34 packs / 8 branches | ✅ **420 tracks** (A 72 + B 263 + FMD13 34 + FMD5 32 + FMD5248 10 + FMD7 9) |
| [**Alice Soft**](companies/alicesoft/) | Alice Soft | Run engine | AmbivalenZ | ✅ 21 tracks (Windows side) |

**1,913 full tracks + 678 B-route excerpts + 50 C-route excerpts + 507 .MDT transcriptions**
(51 + 61 + 756 + 117 + 21 + 82 + 405 + 420), plus the driver analysis documents.

> **MDRV98 family coverage.** The same driver family ships in four forms:
> standalone driver (`DOFMD_98.BIN` + `MDRV98`/`ZYXMD`) in **6 packs** — solved, 117 tracks;
> `DOFMDX98.COM` + game EXE (**32 titles**) — solved for 11 packs (766 files / 678 tracks;
> the rest are FM-only, MMD, or missing); `MDRV98.COM` / `BGMDRV.COM` + tiny shell (**28 packs**):
> of the `.MUS` titles, the 4 tagged GS/GM in HOOT are exported (64 files / 50 tracks); the rest
> are pure-FM `BGM.COM` packs (OPNA only, passed on); `MV2x` (DOR series, 23 titles)
> is FM-only, no MIDI. The 19 `.MDT` packs are also FM/SSG performance data and have been
> transcribed statically into 507 MIDI tracks ([`src/mdt/`](drivers/dofmdx/src/mdt/)).
> See [drivers/dofmdx](drivers/dofmdx/).

> The Alice Soft entry is not a PC-98 driver — its MIDI output lives in the Windows
> executable, and the PC-98 `MAKO` is FM-only. See that directory for details.

## Should this driver be cracked at all?

**"PC-98 has MIDI" does not mean "the driver must be reverse-engineered."**
Some titles are the other way round: the Windows port has the MIDI.

| Class | PC-98 | Win | Action |
|---|---|---|---|
| **A** | yes | no | crack the driver |
| **B** | no | yes | use the Windows version (usually standard MIDI) |
| **C** | yes | yes | pick whichever is easier |
| **D** | no | no | CD-DA / WAV / FM, skip |

Catalog in [catalog/](catalog/), rationale in [docs/CATALOG.md](docs/CATALOG.md).

## Where the material comes from

This repository contains **no game data whatsoever**. Bring your own,
see [docs/MATERIALS.md](docs/MATERIALS.md).

Key point: the whole HOOT pc98 library is only 122 MB (music data only),
so it can be fetched in one go.

```bash
python tools/hoot_download.py --go --jobs 8
```

## Scale

| Item | Count |
|---|---|
| HOOT pc98 packs | 1777 |
| Packs with MIDI | 405 |
| **Distinct MIDI drivers** | **246** (deduplicated by content hash) |
| Drivers shared by multiple titles | 42 |

Full list: [docs/DRIVER-INVENTORY.md](docs/DRIVER-INVENTORY.md)

### Reuse ranking

| Driver | Titles | Companies |
|---|---|---|
| `MMD.COM` | 94 | 23 |
| `MMP_HOOT.COM` | 91 | 23 |
| **`DOFMDX98.COM`** | **79** | 3 |
| `FUGAM_98.COM` | 53 | 4 |
| `TGLFMP2.COM` | 35 | 3 |
| `MUSIC.COM` | 27 | 5 |
| `ARTDI_98.COM` | 26 | 1 |

## General method

Whatever the company, the steps are the same:

1. **Find the driver**: `.COM` / `.SYS` / `.BIN`, hundreds of bytes to tens of KB
2. **See what it hooks**: resident drivers hook a hardware interrupt + a call interrupt
3. **Find the output port**
   - MIDI → interface board data port (PC-98 usually `0xE0D0`)
   - FM → OPNA registers (`0x188` / `0x388`)
4. **Take over the timer** ← this is what makes it fast instead of real-time
   - some drivers hook the hardware timer themselves (MDRV98 does: sound-board
     Timer B, one interrupt = **4.908 ms**, solved from two Win95 references)
5. **Collect bytes → build the MIDI**

### Pitfalls hit repeatedly

| Pitfall | Symptom | Fix |
|---|---|---|
| Unicorn doesn't dispatch real-mode IVT | `UC_ERR_EXCEPTION` | hook each `CD xx` address, `IP += 2` manually |
| `IN` hook doesn't return a value | `'NoneType' cannot be interpreted` | `return value` from the callback |
| Driver rewrites the timer | wrong speed, **different per track** | log `out 0x77/0x71`, convert per tick |
| Wrong clock frequency | 20–30% fast/slow, no error | PC-98's 8253 runs at **2.4576 MHz** |
| Looping tracks | exported several times over | periodic detection on the byte stream — but **repeated sections ≠ a whole-track loop**; with a reference, use its fixed length |
| **Same name, different build** | crashes on another game | **distinguish by content hash**, not filename |
| Interrupt hooking that never uses `INT 21h/25h` | searching `INT 21h` / IVT writes finds nothing | old drivers write the IVT directly with `mov ds,0` + absolute address (that's how MDRV98 was missed) |

### One lesson worth stating

**A file format is not the full definition of the music.**

`.MS` / `.FMD` / `.MMD` contain no "wait this many beats" — only opcodes and
operands. The real semantics (how long a delay unit is, what an unknown
command does) **exist only in the driver's runtime behaviour**.

So static analysis recovers the *structure*; it does not recover the *timing
semantics*. That's why MMDR, MS.COM and MSDRV4 all ended up at the same answer:
**let it speak for itself.**

## Layout

```
companies/
  leaf/          LEAF: MMDR (Shizuku / Kizuato) + notes on the FM side
  alicesoft/     Alice Soft: System3 engine AMUS (Windows side)
drivers/
  mmd/           KAJA's MMD — static parser, 23 companies
  mscom/         LEAF's MS.COM — run the driver
  msdrv/         Black Package MSDRV4 — format analysis + run-driver export
  dofmdx/        D.O. MDRV98 — reverse-engineering notes + mdrvcap (capture / export)
docs/
  handoff notes (not in public release)             starting guide for the next session (status + next steps + review list)
  DRIVER-INVENTORY.md    full list of 246 drivers
  CATALOG.md             A/B/C/D classification scheme
  MATERIALS.md           where to get the material
  progress log (not in public release)                current status and next steps
  pipeline notes (not in public release)            pipeline plan (one core + per-driver profile)
catalog/
  games.json     4411 titles (all platforms)
  win95.json     414 PC-98 MIDI titles + VNDB platform info
  WIN95.md       98 with a Windows port, with confidence
  CROSS.md       cross-reference against the local collection
tools/           download, triage, clustering, cross-reference, conversion
```

## Tools

| Tool | Purpose |
|---|---|
| `hoot_download.py` | fetch missing HOOT packs (incremental) |
| `driver_clusters.py` | cluster drivers by content hash |
| `dump_all.py` | safety-net export: archive files of every MIDI title |
| `build_catalog.py` | build the title catalog |
| `vndb_win95.py` | query VNDB for Windows ports |
| `scan_collection.py` | inventory a local collection |
| `triage2.py` | find the real driver in each pack |
| `mdrv98_routes.py` | MDRV98 family route stats + 32-byte signature scan |
| `make_upload.py` | build an upload copy with no game data (git-tracked only) |
| `drivers/dofmdx/src/mdrvcap/` | MDRV98 capture & export (table B + Timer B → SMF) |

## Next

- [x] The `DOFMDX98.COM` route (32 titles) — 11 packs / 766 files (678 tracks); FM-only 4 skipped, MMD 8 separate, 7 packs missing
- [x] **MMD batch** — 36 titles / 756 tracks, archived by title (GAL 460 / non-GAL 296)
- [x] The `MDRV98.COM` / `BGMDRV.COM` shell route — closed: 4 GS/GM `.MUS` titles exported (64 files / 50 tracks), FM packs passed on; `.MDT` already statically parsed (19 packs / 507 tracks)
- [x] `MV2x` (DOR series, 23 titles) — confirmed FM-only, no MIDI output
- [x] `MSDRV4` — driver runs; 7 packs / 129 MIDIs exported (GS / SC-88, calibrated on the OPNA Timer B). The `stjan2` (`.BM2`) and `rekiai` (`.MF` tail) containers are resolved; 23 tracks await loop detection ([MS-FORMAT.md](drivers/msdrv/docs/MS-FORMAT.md))
- [ ] The long tail: 204 one-off drivers

## References

- [HOOT](https://hoot.joshw.info/) — runs the real drivers; the best reference for
  verification, and its `xml/*.xml` is the best index of "which game uses which driver"
- [VNDB](https://vndb.org/) — platform information, has an API
- [VGMRips · PC-98 Sound Drivers](https://vgmrips.net/w/index.php?title=PC-98_Sound_Drivers)
- [PMD source](https://github.com/d2mirrors/pmd) — the standard FM driver

## Copyright

Game data, drivers and music remain the property of their respective owners.
This repository contains only **analysis and conversion code** and
**format documentation derived from the data**.
