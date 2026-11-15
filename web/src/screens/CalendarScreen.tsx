import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api, Calendar, Preset } from "../api";
import { yearTiles, monthTiles, yearTilesFromDays, monthTilesFromDays, Tile, MONTH_ABBR, RawField } from "../calendarTiles";
import { useAoi } from "../App";
import Seasons from "./Seasons";

const RAMP6 = [0, 8, 14, 20, 26, 32];

const PRESET_NAMES: Record<string, string> = {
  riau: "Riau (Lahan Gambut Sumatera)",
  central_kalimantan: "Kalimantan Tengah (Eks-PLG)",
  south_sumatra: "Sumatera Selatan (Ogan Komering Ilir)",
  jambi: "Jambi (Gambut & Perkebunan)",
  merauke: "Merauke (Savana Musiman Papua)",
};

export default function CalendarScreen({ goMap }: { goMap: () => void }) {
  const { aoi, setAoi, setCalFilter, series, lang, t } = useAoi();
  const [cal, setCal] = useState<Calendar | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [view, setView] = useState<"yearly" | "monthly">("yearly");
  const [yearSel, setYearSel] = useState("all");
  const [monthSel, setMonthSel] = useState("all");
  const [sensor, setSensor] = useState<"harm" | "modis" | "viirs">("harm");
  const [sel, setSel] = useState<{ key: string; title: string; sub: string; value: string; notes: string[] } | null>(null);

  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    setSel(null); // stale selection from previous AOI must not survive
    api.calendar(aoi)
      .then(c => {
        setCal(c);
        setLoading(false);
      })
      .catch(e => {
        setErr(e.message);
        setLoading(false);
      });
  }, [aoi]);

  const yearsAll = cal?.years ?? [];
  const rawField: RawField = sensor === "modis" ? "raw_modis_frp_mw" : "raw_viirs_frp_mw";
  const days = series?.days ?? [];

  const tiles = useMemo<Tile[]>(
    () => (sensor === "harm"
      ? (view === "yearly" ? yearTiles(yearsAll, monthSel) : monthTiles(yearsAll, yearSel))
      : (view === "yearly" ? yearTilesFromDays(days, monthSel, rawField) : monthTilesFromDays(days, yearSel, rawField))),
    [sensor, view, yearsAll, yearSel, monthSel, days, rawField]
  );

  const sensorLabel = sensor === "harm"
    ? t("cal_sensor_harm")
    : sensor === "modis"
    ? t("cal_sensor_modis")
    : t("cal_sensor_viirs");

  const readyPresets = presets.filter(p => p.artifact_status === "available");

  const summary = useMemo(() => {
    if (!tiles.length) return null;
    const peak = tiles.reduce((p, t) => (t.total > p.total ? t : p), tiles[0]);
    return {
      total: tiles.reduce((a, t) => a + t.total, 0),
      peak,
      active: tiles.filter(t => !t.isGap && t.total > 0).length,
      gaps: tiles.reduce((a, t) => a + t.gapDays, 0),
      unit: view === "yearly" ? "tahun aktif" : "bulan aktif",
      peakUnit: view === "yearly" ? "tahun" : "bulan",
      valueLabel: sensor === "harm"
        ? "Total Energi Terharmonisasi FRP (MW)"
        : `Total Mentah ${sensor === "modis" ? "MODIS" : "VIIRS"} FRP (MW)`,
      span: view === "yearly"
        ? (monthSel === "all" ? "siklus tahunan penuh" : `hanya bulan ${MONTH_ABBR[Number(monthSel) - 1]}`)
        : (yearSel === "all" ? `seluruh ${yearsAll.length} tahun pengamatan` : `tahun ${yearSel}`),
    };
  }, [tiles, view, monthSel, yearSel, yearsAll.length, sensor]);

  const onTile = (t: Tile) => {
    const notes: string[] = [];
    notes.push(`${t.activeDays} hari aktif dengan deteksi FRP > 0 (dari ${t.days} hari pengamatan)`);
    if (t.isGap) {
      notes.push("Seluruh periode ini merupakan celah pengamatan satelit (tidak ada data, bukan nilai nol).");
    } else if (t.gapDays > 0) {
      notes.push(`${t.gapDays} hari celah pengamatan satelit (dilewati dari rata-rata, tidak diasumsikan nol).`);
    }
    if (view === "yearly" && monthSel !== "all") {
      notes.push(`Dibatasi untuk musim bulan: ${MONTH_ABBR[Number(monthSel) - 1]}`);
    }
    if (view === "monthly" && yearSel === "all") {
      notes.push(`Komposit klimatologis sepanjang ${yearsAll.length} tahun pengamatan (${yearsAll[0]?.year}–${yearsAll[yearsAll.length - 1]?.year})`);
    }
    if (view === "monthly" && yearSel !== "all") {
      notes.push(`Tahun Kalender: ${yearSel}`);
    }

    setSel({
      key: t.key,
      title: view === "yearly" ? `Tahun ${t.label}` : `Bulan ${t.label} · ${yearSel === "all" ? "Rata-rata semua tahun" : `Tahun ${yearSel}`}`,
      sub: sensor === "harm"
        ? "Total Energi FRP Terharmonisasi (Skala setara MODIS Aqua)"
        : `${sensorLabel} — data instrumen mentah tanpa kalibrasi lintas sensor`,
      value: `${t.total.toLocaleString("id-ID")} MW`,
      notes,
    });
  };

  const calFilterDesc = view === "yearly"
    ? `Tahunan · ${monthSel === "all" ? "semua bulan" : `bulan ${MONTH_ABBR[Number(monthSel) - 1]}`}`
    : `Bulanan · ${yearSel === "all" ? "semua tahun" : yearSel}`;

  const goMapWithFilter = () => {
    setCalFilter(calFilterDesc);
    goMap();
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
        <div style={{ maxWidth: 640 }}>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            ANALISIS TREN TEMPORAL
          </span>
          <h1>Kalender Riwayat &amp; Tren Kebakaran</h1>
          <p className="sub">
            Setiap kotak menunjukkan akumulasi energi kebakaran (Fire Radiative Power / FRP dalam Megawatt) per {view === "yearly" ? "tahun" : "bulan"}. Warna yang semakin pekat menandakan aktivitas kebakaran yang lebih tinggi. Hari tanpa pengamatan satelit (celah data) dipisahkan dari hari tanpa titik api.
          </p>
          <button
            className="btn secondary"
            style={{ marginTop: 12, padding: "7px 15px", fontSize: 12.5 }}
            onClick={goMapWithFilter}
            title="Lihat persebaran titik panas di Peta Titik Api dengan filter waktu ini"
          >
            Lihat di Peta Titik Api — {calFilterDesc} →
          </button>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>Wilayah Pengamatan</span>
            <select
              className="glass-select"
              value={aoi}
              onChange={e => { setAoi(e.target.value); setSel(null); }}
            >
              {presets.map(p => (
                <option key={p.id} value={p.id}>
                  {PRESET_NAMES[p.id] ?? p.name}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>{lang === "id" ? "Pilihan Sensor" : "Sensor Selection"}</span>
            <select
              className="glass-select"
              value={sensor}
              onChange={e => { setSensor(e.target.value as any); setSel(null); }}
            >
              <option value="harm">{lang === "id" ? "Terharmonisasi (Standar MODIS Aqua, MW)" : "Harmonized (MODIS Aqua Standard, MW)"}</option>
              <option value="modis">{lang === "id" ? "Mentah MODIS (Resolusi 1 km Aqua, MW)" : "Raw MODIS (1 km Aqua resolution, MW)"}</option>
              <option value="viirs">{lang === "id" ? "Mentah VIIRS (Resolusi 375 m S-NPP, MW)" : "Raw VIIRS (375 m S-NPP resolution, MW)"}</option>
            </select>
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>{lang === "id" ? "Periode Tampilan" : "View Mode"}</span>
            <select
              className="glass-select"
              value={view}
              onChange={e => { setView(e.target.value as any); setSel(null); }}
            >
              <option value="yearly">{t("cal_view_yearly")}</option>
              <option value="monthly">{t("cal_view_monthly")}</option>
            </select>
          </label>

          {view === "monthly" && (
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span>{t("cal_year_choice")}</span>
              <select
                className="glass-select"
                value={yearSel}
                onChange={e => { setYearSel(e.target.value); setSel(null); }}
              >
                <option value="all">{t("cal_all_years")}</option>
                {yearsAll.map(y => (
                  <option key={y.year} value={String(y.year)}>{lang === "id" ? `Tahun ${y.year}` : `Year ${y.year}`}</option>
                ))}
              </select>
            </label>
          )}

          {view === "yearly" && (
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span>{t("cal_month_choice")}</span>
              <select
                className="glass-select"
                value={monthSel}
                onChange={e => { setMonthSel(e.target.value); setSel(null); }}
              >
                <option value="all">{t("cal_all_months")}</option>
                {MONTH_ABBR.map((m, i) => (
                  <option key={m} value={String(i + 1).padStart(2, "0")}>{lang === "id" ? `Bulan ${m}` : `Month ${m}`}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </div>

      {sensor !== "harm" && cal && (
        <div className="boundary" style={{ marginTop: 18 }}>
          <b>{lang === "id" ? `Catatan Skala Sensor: Data Mentah ${sensor === "modis" ? "MODIS" : "VIIRS"}.` : `Sensor Scale Note: Raw ${sensor === "modis" ? "MODIS" : "VIIRS"} Data.`}</b>
          <p className="sub" style={{ marginTop: 2 }}>
            {lang === "id"
              ? "Sensor satelit MODIS (1 km) dan VIIRS (375 m) memiliki resolusi spasial dan sensitivitas deteksi yang berbeda. Nilai mentah tidak dapat dibandingkan secara langsung antar tahun transisi 2012 tanpa proses harmonisasi EmberLine."
              : "MODIS (1 km) and VIIRS (375 m) satellite sensors differ in spatial resolution and detection sensitivity. Raw values cannot be directly compared across the 2012 transition without EmberLine cross-sensor harmonization."}
          </p>
        </div>
      )}

      {loading && (
        <div className="status-panel loading" style={{ marginTop: 20 }}>
          <div className="status-title">{lang === "id" ? "Memuat data kalender kebakaran…" : "Loading fire calendar telemetry…"}</div>
          <p className="status-desc">{lang === "id" ? "Menyusun matriks observasi satelit multi-tahun untuk wilayah terpilih." : "Compiling multi-year satellite observation matrix for selected region."}</p>
          <div className="skel" style={{ height: 28, marginTop: 8 }} />
        </div>
      )}

      {err && (
        <div className="status-panel failed" style={{ marginTop: 20, padding: "18px 22px", borderRadius: 12 }}>
          <div className="status-title" style={{ fontSize: 16, fontWeight: 700 }}>
            {t("err_not_available")}
          </div>
          <p className="status-desc" style={{ marginTop: 6, fontSize: 13.5, color: "var(--ink2)", lineHeight: 1.6 }}>
            {t("err_not_available_desc")}
            {" "}
            {lang === "id" ? "Silakan pilih salah satu wilayah Nusantara yang datanya sudah siap dipantau:" : "Please choose one of the ready Indonesian regions:"}
          </p>
          {readyPresets.length > 0 && (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 14 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)" }}>{t("cal_ready_regions")}</span>
              {readyPresets.map(p => (
                <button
                  key={p.id}
                  className="btn secondary"
                  style={{ padding: "6px 14px", fontSize: 12.5, borderRadius: 8, fontWeight: 600 }}
                  onClick={() => setAoi(p.id)}
                >
                  {t("cal_open_region")} {PRESET_NAMES[p.id] ?? p.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!loading && !err && cal && (
        <div className="grid2" style={{ marginTop: 18, gridTemplateColumns: "3fr 2fr" }}>
          <div className="card">
            {summary && (
              <div className="cal-summary">
                <span className="big">{summary.total.toLocaleString("id-ID")}</span>
                <span className="unit">{summary.valueLabel}</span>
                <span className="stat">
                  Puncak {summary.peakUnit}: <b>{summary.peak.label}</b> ({summary.peak.total.toLocaleString("id-ID")} MW)
                </span>
                <span className="stat">
                  <b>{summary.active}</b> {summary.unit}
                </span>
                <span className="stat">
                  <b>{summary.gaps}</b> hari celah pengamatan satelit
                </span>
              </div>
            )}

            <div className="tiles">
              {tiles.map(t => {
                const isSelected = sel?.key === t.key;
                return (
                  <button
                    key={t.key}
                    className={"tile" + (t.isGap ? " gap" : "") + (isSelected ? " selected" : "")}
                    style={{ background: t.isGap ? undefined : t.fill }}
                    onClick={() => onTile(t)}
                    aria-label={`Pemeriksaan ${t.label}: ${t.isGap ? "celah data satelit" : `${t.total.toLocaleString("id-ID")} MW FRP`}`}
                  >
                    <span className="tile-label">{t.label}</span>
                    <span className="tile-value">
                      {t.isGap ? "Celah Data" : `${t.total.toLocaleString("id-ID")} MW`}
                    </span>
                    {t.gapDays > 0 && !t.isGap && (
                      <span className="tile-flags">
                        {t.gapDays} hari celah
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="legend-row">
              <span className="item">
                <span className="ramp">
                  {RAMP6.map((intensity, i) => (
                    <i
                      key={i}
                      style={{
                        background: intensity === 0
                          ? "var(--surface)"
                          : `color-mix(in srgb, var(--ember) ${intensity}%, var(--surface))`,
                      }}
                    />
                  ))}
                </span>
                <span>Gradien energi FRP (rendah → tinggi relatif terhadap puncak)</span>
              </span>
              <span className="item">
                <i className="sw-gap" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>Celah data (satelit tidak melintas)</span>
              </span>
              <span className="item">
                <i className="sw-zero" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>Valid 0 MW (nihil titik panas)</span>
              </span>
            </div>
          </div>

          <div className="card">
            <h2>Pemeriksaan {view === "yearly" ? "Tahun" : "Bulan"} Terpilih</h2>
            <AnimatePresence initial={false} mode="wait">
              {sel ? (
                <motion.div
                  key={sel.key}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ type: "spring", stiffness: 320, damping: 30 }}
                >
                  <div style={{ marginTop: 12 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{sel.title}</span>
                    <p className="sub" style={{ marginTop: 2 }}>{sel.sub}</p>
                  </div>

                  <div className="kpi-box" style={{ marginTop: 14 }}>
                    <span className="kpi-label">Akumulasi Energi Panas (FRP)</span>
                    <span className="kpi-val">{sel.value}</span>
                    <span className="kpi-sub">
                      {sensor === "harm" ? "Energi terkalibrasi setara MODIS Aqua" : "Total deteksi instrumen mentah"}
                    </span>
                  </div>

                  <div style={{ marginTop: 12, display: "grid", gap: 6 }}>
                    {sel.notes.map((n, i) => (
                      <div
                        key={i}
                        style={{
                          fontSize: 12.5,
                          color: "var(--ink2)",
                          background: "var(--sunken)",
                          padding: "6px 10px",
                          borderRadius: 6,
                          border: "1px solid var(--line)",
                        }}
                      >
                        {n}
                      </div>
                    ))}
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="status-panel loading"
                  style={{ marginTop: 12 }}
                >
                  <div className="status-title">Belum Ada Periode Terpilih</div>
                  <p className="status-desc">
                    Klik salah satu kotak {view === "yearly" ? "tahun" : "bulan"} pada kalender untuk memeriksa rincian energi, hari aktif, dan kelengkapan data satelit.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {!loading && !err && cal && (
        <div style={{ marginTop: 32, borderTop: "1px solid var(--line)", paddingTop: 28 }}>
          <Seasons />
        </div>
      )}
    </div>
  );
}
