# STATUS & PLAN — EmberLine

> Diperbarui: Sabtu 14 Nov 2026 malam · **Deadline: Minggu 15 Nov 2026, 23:59 WIB (≈ besok malam)**
> Sumber: `DECISIONS.md`, `docs/method.md`, audit `git status`, hasil build/test aktual.

---

## 0) Jawaban cepat: "numpuk / berantakan kah?"

**Kode: TIDAK berantakan.** Build hijau di 2 salinan, tests 64/64 (protocol) + 17/17 (ingestion) lolos,
artefak regenerable (seed fix), API 12+ endpoint terverifikasi, kedua salinan (review-tmp + Desktop) sinkron.

**Git: YA, numpuk** — 3 gelombang perubahan belum di-commit (23 file) menumpuk di atas 4 commit lokal yang
belum di-push. Ini risiko terbesar menjelang deadline: **commit + push hari ini juga** (lihat §4 langkah 1).

**Peta: default-nya sekarang titik per deteksi pada tahun teraktif** (bukan selimut 37k titik all-years
yang jelek itu). Kalau mau lihat "selimut", pilih All years manual — memang padat karena itu 14,5 tahun data.

---

## 1) ✅ SUDAH SELESAI (dengan bukti)

### Data & backend (Role B — dari repo tim)
- `fetch_firms.py` resumable ledger + SHA-256/window; `validate.py` 4-state missingness + quarantine
- **G1 evidence**: Riau MODIS 83.318 + VIIRS 346.804 baris, 2012-01-20 → 2026-07-31, 0 gagal, 0 hash mismatch
- Tests ingestion 17/17

### Science pipeline (Role C) — PROTO-C01-v0.9
- `grid.py` (sel 0.1°), `match.py` (Aqua-only ref, confidence filters) — **kini juga menulis `detections.json`**
- `harmonize.py` (B1 ratio + B2 OLS + monotone + Duan + bootstrap B=400), `metrics.py` (12 metrik),
  `calendar.py` (366 posisi), `stress_test.py`, `run.py` (orkestrator 9+2 artefak)
- `grid_export.py` (baru): per-sel per-tahun → `grid.json` (1.175 sel × 15 thn)
- Tests protocol **64/64**; smoke run fixture hijau (run_id terbaru `…T1411Z…`)

### Kontrak (Role D-02)
- `series / calendar / climatology / windows / method / jobs` example — + **`grid.example.json`**

### API (Role D-03) — `api/app.py`
- 12+ endpoint: health, presets, series, calendar, climatology, windows, stress, method, export,
  analyze, jobs — + **`/api/aoi/{aoi}/grid`** dan **`/api/aoi/{aoi}/detections`** (baru)
- Tidak pernah import pipeline; artefak versioned; error sanitized; bounded jobs

### Web (Role E) — React + Vite + TS + ECharts + Leaflet + framer-motion
- 6 layar sesuai frame model user: Overview / Fire Map / Fire Calendar / Anomalies / Analytics / Methodology
- **Telemetry console upgrade**: frosted topbar, sliding pill `layoutId="activeTab"` (spring 300/30),
  drawer "How to read" animasi + tombol Esc, KPI mono tabular-nums, chart resize ResizeObserver (360px ok)
- **Fire Calendar**: tile perbandingan (Yearly/Monthly), ringkasan ala GitHub, **pilih Series:
  Harmonized / MODIS raw / VIIRS raw** + konteks skala sensor, klik tile → panel detail animasi
- **Analytics**: legend toggle show/hide per seri (MODIS/VIIRS/naive/harmonized) + Stress Test KPI (X× vs Y×)
- **Fire Map (O-02 → implemented)**: **titik per deteksi asli** (37.127 deteksi tervalidasi),
  warna = satelit, ukuran = FRP, filter tahun/satelit, default = tahun teraktif, `preferCanvas`
  — gaya referensi siagaapi.my.id ("one dot ≠ one fire")
- Branding baru: logo api gradient user (SVG + favicon), font Poppins, wordmark gradient
- Landing: CTA verb-first + chip konteks ("Opens: Riau · 2012–2026 · data ready")

### Desain & docs
- Figma boards 01–08 (Foundations, Components, Wireframes, Hi-fi, States, Preset Map, Logo) di file user
- `docs/ux/`: user_journey.md, design_spec.md, logo_spec.md (logo baru dicatat), flow board + hi-fi HTML,
  wireframe.png
- `DECISIONS.md`: DEV-S01..S06 + DEV-UI1 + INT-1/2 tercatat

---

## 2) 🟡 SUDAH DIKERJAKAN TAPI **BELUM DI-COMMIT** (3 gelombang, 23 file)

| Gelombang | Isi | Commit yang disarankan |
|---|---|---|
| [E-02] | Telemetry console: styles.css, App.tsx, echarts.ts, 5 screens, api.ts, calendarTiles.ts | `[E-02] visual console: frosted header, sliding nav pill, animated panels, KPI mono, responsive charts` |
| [O-02a] | Sensor selector (calendarTiles, CalendarScreen, Compare, echarts) | bisa digabung [E-02] |
| [O-02b] | Hotspot detections + grid: match.py, run.py, grid_export.py (baru), api/app.py, contracts/grid.example.json, artifacts (detections.json, grid.json, artefak re-run) | `[O-02] hotspot detections + grid artifacts, API endpoints, map dot layer` |

⚠️ `.agent/` (untracked) = artefak tool, **jangan di-commit** → tambahkan ke `.gitignore`.

---

## 3) ❌ BELUM DIKERJAKAN (dari PRD / DECISIONS.md / plan tim)

| # | Item | Sumber | Prioritas |
|---|---|---|---|
| 1 | **Commit 2 gelombang baru + PUSH semua ke GitHub** (4 commit lama juga belum push) | INT-2 | 🔴 hari ini |
| 2 | `.agent/` → `.gitignore` | housekeeping | 🔴 hari ini |
| 3 | **Real-data run (G2)**: butuh MAP_KEY → `make data` → `pipeline/run.py` pada data asli; saat ini semua angka di UI = FIXTURE_SYNTHETIC | DEC-1, gates | 🔴 jika MAP_KEY ada |
| 4 | **DEV-UI1**: badge MOCK disembunyikan (permintaan user) — **wajib restore sebelum demo eksternal yang mengklaim data real**, atau revisi barisnya jika data sudah real | DECISIONS.md | 🔴 sebelum demo |
| 5 | DEV-S01..S06 masih **PENDING** (butuh approval A) | DECISIONS.md | 🟠 |
| 6 | DEC-3 definisi `years_active`; DEC-4 re-baseline di-approve; DEC-1/2/5 | DECISIONS.md | 🟠 |
| 7 | Layar **Anomalies (O-01)** masih stub jujur (bukan backlog lain yang disepakati) | PRD | 🟡 jika sempat |
| 8 | README.md belum menc fitur baru (map dots, sensor selector, cara run) | docs | 🟡 |
| 9 | Gate records G2/G3/G4 masih kosong di DECISIONS.md | gates | 🟠 |
| 10 | Paste `logo_flame.svg` → Figma board 08 (manual, bridge tidak bisa bezier) — catatan: logo resmi kini versi baru user | logo_spec | 🟢 |
| 11 | E-03..E-06 polish lanjutan (mobile pass <400px, audit a11y penuh) | plan E | 🟢 opsional |
| 12 | Commit review-tmp copy = mirror; pastikan hanya SATU sumber kebenaran yang di-push (Desktop) | housekeeping | 🟠 |

---

## 4) 🗓️ RENCANA MENUJU DEADLINE (15 Nov 23:59 WIB)

**Hari ini (Sabtu malam):**
1. `.agent/` → `.gitignore` — 1 menit
2. Commit `[E-02]` (web) dan `[O-02]` (detections+grid) → git bersih — 5 menit
3. **PUSH `origin main`** (login browser sekali) — semua 6 commit masuk — 5 menit
4. Kalau MAP_KEY sudah ada: `make data` → `pipeline/run.py` pada data asli → artefak real → G2 terisi
5. Update README (fitur + cara run + screenshot) — 20 menit

**Besok (Minggu):**
6. Pagi: feature freeze (G3) — kunci lingkup, berhenti tambah fitur
7. Siang: demo rehearsal + isi Gate records + DEV-UI1 diputuskan (restore badge ATAU data sudah real)
8. Sore: QA akhir (2 salinan build hijau, endpoint smoke), freeze
9. 23:59 WIB: DEADLINE — repo final ter-push

**Fallback kalau MAP_KEY tidak kunjung ada:** demo tetap jalan dengan FIXTURE_SYNTHETIC, asalkan
badge MOCK/SYNTHETIC di-restore (DEV-UI1) supaya jujur — kejujuran > tampilan.

---

## 5) Keputusan yang butuh tim (ringkas)
- A: approve DEV-S01..S06 + DEC-4 re-baseline
- B: konfirmasi MAP_KEY & jadwal `make data` (DEC-1)
- C: DEC-3 definisi `years_active` (usulan: tahun dengan ≥1 hari `state=data` di jendela kritis)
- Semua: INT-2 disiplin commit prefix — sudah dipraktikkan, tinggal konsisten
