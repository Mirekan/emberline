import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api, Method } from "../api";
import { useAoi } from "../App";

export default function MethodScreen() {
  const { aoi, setAoi, lang } = useAoi();
  const [m, setM] = useState<Method | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    api.method(aoi)
      .then(res => {
        setM(res);
        setLoading(false);
      })
      .catch(e => {
        setErr(e.message);
        setLoading(false);
      });
  }, [aoi]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(o => !o);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const fmt = (v: number | string | undefined | null) => {
    if (v == null) return <span style={{ color: "var(--ink3)" }}>N/A</span>;
    if (typeof v === "string") return <span style={{ color: "var(--ink2)" }}>{v}</span>;
    return <span className="mono">{v}</span>;
  };

  return (
    <div className="grid2">
      <div>
        <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
          {lang === "id" ? "STANDAR VALIDASI KETAT" : "RIGOROUS VALIDATION STANDARD"}
        </span>
        <h1>{lang === "id" ? "Metodologi — Validasi Mandiri Lintas Sensor" : "Methodology — held-out cross-sensor validation"}</h1>
        <p className="sub">
          {lang === "id"
            ? `Partisi pelatihan model: ${m?.split.train_years[0] ?? "2012"}–${m?.split.train_years[m.split.train_years.length - 1] ?? "2020"}, partisi evaluasi mandiri: ${m?.split.test_years[0] ?? "2020"}–${m?.split.test_years[m.split.test_years.length - 1] ?? "2026"}. Semua metode dinilai terhadap partisi uji independen yang identik. Di mana harmonisasi tidak menunjukkan peningkatan metrik, EmberLine menyatakannya secara terbuka dan jujur.`
            : `Model training partition: ${m?.split.train_years[0] ?? "2012"}–${m?.split.train_years[m.split.train_years.length - 1] ?? "2020"}, independent evaluation partition: ${m?.split.test_years[0] ?? "2020"}–${m?.split.test_years[m.split.test_years.length - 1] ?? "2026"}. All competing baselines are scored against the identical held-out test partition. Where harmonization does not improve upon raw metrics, EmberLine discloses this honestly.`}
        </p>

        {loading && (
          <div className="status-panel loading" style={{ marginTop: 20 }}>
            <div className="status-title">{lang === "id" ? "Memuat data validasi metodologi…" : "Loading methodology validation data…"}</div>
            <p className="status-desc">{lang === "id" ? "Mengevaluasi metrik transisi sensor dan sebaran galat." : "Evaluating sensor transition metrics and error distributions."}</p>
            <div className="skel" style={{ height: 260, marginTop: 10 }} />
          </div>
        )}

        {err && (
          <div className="status-panel failed" style={{ marginTop: 20 }}>
            <div className="status-title">{lang === "id" ? "Data Metodologi Belum Tersedia" : "Methodology Data Not Available"}</div>
            <p className="status-desc">{lang === "id" ? "Data evaluasi metodologi untuk wilayah ini sedang dalam tahap pemrosesan." : "Methodology evaluation data for this region is currently being processed."}</p>
            {aoi !== "riau" && (
              <div style={{ marginTop: 12 }}>
                <button className="btn secondary" onClick={() => setAoi("riau")}>
                  {lang === "id" ? "Buka Riau (Data Siap)" : "Open Riau (Data Ready)"}
                </button>
              </div>
            )}
          </div>
        )}

        {!loading && m && (
          <>
            <div className="card" style={{ marginTop: 20, padding: 0, overflow: "hidden" }}>
              <table>
                <thead>
                  <tr>
                    <th>{lang === "id" ? "Metrik Statistik & Standar Galat" : "Statistical Metric & Error Standard"}</th>
                    <th>{lang === "id" ? "Sambungan Mentah (Tanpa Kalibrasi)" : "Naive Handover (Uncalibrated)"}</th>
                    <th>{lang === "id" ? "Rasio Terkalibrasi (Metode Terpilih)" : "Calibrated Ratio (Accepted)"}</th>
                    <th>{lang === "id" ? "Model Non-linear (Uji Regresi)" : "Non-linear Model (Mapping Test)"}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Rasio galat lonjakan skala (ideal: 1,00×)" : "Level shift error ratio (ideal: 1.00×)"}</td>
                    <td className="mono">{fmt(m.metrics.b0_naive_splice_level_shift ?? "N/A:not_computed")}</td>
                    <td className="mono" style={{ color: "var(--ok)", fontWeight: 700 }}>{fmt(m.metrics.b1_naive_splice_level_shift ?? "N/A:not_computed")}</td>
                    <td className="mono">{fmt(m.metrics.b2_naive_splice_level_shift ?? "N/A:not_computed")}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Bias rerata rasio logaritmik (Mean log-ratio bias)" : "Mean log-ratio bias"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.mean_log_ratio_bias)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Persentase galat mutlak simetris (sMAPE %)" : "Symmetric Mean Absolute Percentage Error (sMAPE %)"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.smape)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Koefisien korelasi Pearson (harian / mingguan)" : "Pearson correlation coefficient (daily / weekly)"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.pearson_daily)} / {fmt(m.metrics.pearson_weekly)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Korelasi peringkat Spearman (harian / mingguan)" : "Spearman rank correlation (daily / weekly)"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.spearman_daily)} / {fmt(m.metrics.spearman_weekly)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Koefisien determinasi ruang-log (R²)" : "Log-space coefficient of determination (R²)"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.log_space_r2)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Statistik Kolmogorov-Smirnov (KS) / Jarak Wasserstein" : "Kolmogorov-Smirnov (KS) statistic / Wasserstein distance"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.ks_statistic)} / {fmt(m.metrics.wasserstein_distance)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Korelasi pola musiman kalender tahunan" : "Calendar seasonality pattern correlation"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.calendar_pattern_correlation)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{lang === "id" ? "Cakupan interval empiris (keyakinan nominal 80%)" : "Empirical interval coverage (nominal 80% confidence)"}</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.interval_coverage_empirical)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="grid2" style={{ marginTop: 18, gridTemplateColumns: "1fr 1fr" }}>
              <div className="card">
                <h2>{lang === "id" ? "Batasan Metodologi" : "Methodological limitations"}</h2>
                <ul style={{ listStyle: "none", padding: 0, marginTop: 12 }}>
                  {(lang === "id" ? [
                    "Nilai terharmonisasi adalah estimasi model — bukan kebenaran mutlak; setiap nilai selalu disertai rentang ketidakpastian empiris.",
                    "Metode rasio terkalibrasi diterima sebagai standar resmi; model pemetaan non-linear dicatat secara transparan sebagai hasil uji negatif.",
                    "Deteksi titik panas tidak pernah dijumlahkan menjadi hitungan fisik kebakaran lintas sensor.",
                    "Celah pengamatan satelit ditandai secara eksplisit, tidak pernah diinterpolasi atau diasumsikan bernilai nol.",
                    "Kalibrasi acuan sensor Aqua MODIS membatasi klaim hanya pada bukti yang didukung data satelit."
                  ] : m.limitations.map(l => l.replace(/^DEC-6:\s*/, ""))).map((l, i) => (
                    <li
                      key={i}
                      style={{
                        marginBottom: 10,
                        color: "var(--ink2)",
                        fontSize: 12.5,
                        lineHeight: 1.5,
                        paddingLeft: 14,
                        position: "relative",
                      }}
                    >
                      <span style={{ position: "absolute", left: 0, color: "var(--ember)" }}>•</span>
                      {l}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="card">
                <h2>{lang === "id" ? "Sumber Data Satelit & Sitasi" : "Satellite data sources & citations"}</h2>
                <p className="sub mono" style={{ marginTop: 8, fontSize: 11.5 }}>
                  NASA FIRMS — MODIS C6.1 (Giglio et al. 2016)<br />
                  VIIRS 375 m VNP14IMG (Schroeder et al. 2014)
                </p>
                <p className="sub" style={{ marginTop: 8, fontSize: 12 }}>
                  {lang === "id"
                    ? "“Kami mengakui penggunaan data dan/atau citra dari Fire Information for Resource Management System (FIRMS) NASA, bagian dari ESDIS NASA.”"
                    : "“We acknowledge the use of data and/or imagery from NASA’s Fire Information for Resource Management System (FIRMS), part of NASA’s ESDIS.”"}
                </p>
                <div style={{ display: "flex", gap: 10, marginTop: 16, flexWrap: "wrap" }}>
                  <button
                    className="btn secondary"
                    onClick={() => window.open(`/api/aoi/${aoi}/export?what=series`, "_blank")}
                    title={lang === "id" ? "Ekspor deret waktu harian ke CSV" : "Export daily harmonized time series to CSV"}
                  >
                    {lang === "id" ? "Ekspor deret harian (CSV)" : "Export daily series (CSV)"}
                  </button>
                  <button
                    className="btn secondary"
                    onClick={() => window.open(`/api/aoi/${aoi}/export?what=windows`, "_blank")}
                    title={lang === "id" ? "Ekspor jendela kebakaran musiman ke CSV" : "Export seasonal burning windows to CSV"}
                  >
                    {lang === "id" ? "Ekspor jendela musiman (CSV)" : "Export seasonal windows (CSV)"}
                  </button>
                </div>
              </div>
            </div>

            <div className="boundary" style={{ marginTop: 18 }}>
              <b>{lang === "id" ? "Pengungkapan Ilmiah Wajib: Bersifat historis & deskriptif — bukan prediktif." : "Mandatory Scientific Disclosure: Historical & descriptive — not predictive."}</b>
              <p className="sub" style={{ marginTop: 2 }}>
                {lang === "id"
                  ? "EmberLine mengalibrasi observasi satelit retrospektif untuk memastikan kesinambungan rekam ilmiah tanpa putus. EmberLine tidak memprediksi kebakaran di masa depan atau menilai risiko darurat waktu nyata."
                  : "EmberLine calibrates retrospective satellite observations to ensure unbroken scientific record continuity. It does not predict future fire ignitions or assess real-time emergency risks."}
              </p>
            </div>
          </>
        )}
      </div>

      <aside>
        <div className="card drawer">
          <button
            onClick={() => setOpen(o => !o)}
            aria-expanded={open}
            style={{
              display: "flex",
              width: "100%",
              justifyContent: "space-between",
              alignItems: "center",
              background: "none",
              border: "none",
              padding: 0,
              cursor: "pointer",
            }}
          >
            <h2 style={{ fontSize: 15, margin: 0 }}>{lang === "id" ? "Glosarium Telemetri & Definisi" : "Telemetry glossary & definitions"}</h2>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <span className="mono" style={{ fontSize: 10, color: "var(--ink3)" }}>Esc</span>
              <motion.span
                animate={{ rotate: open ? 180 : 0 }}
                transition={{ type: "spring", stiffness: 320, damping: 28 }}
                style={{ display: "inline-block", color: "var(--ink2)", fontSize: 11 }}
                aria-hidden
              >
                ▼
              </motion.span>
            </span>
          </button>

          <AnimatePresence initial={false}>
            {open && (
              <motion.div
                key="body"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ type: "spring", stiffness: 320, damping: 28 }}
                style={{ overflow: "hidden" }}
              >
                <p className="sub" style={{ fontSize: 12 }}>
                  {lang === "id"
                    ? "Definisi ilmiah terstandarisasi untuk setiap satuan pengukuran dan status dalam konsol ini."
                    : "Standardized scientific definitions for every measurement unit and state in this console."}
                </p>
                <dl style={{ marginTop: 8 }}>
                  <dt>{lang === "id" ? "Titik Panas (Hotspot)" : "Hotspot"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Piksel observasi satelit yang terdeteksi memiliki anomali termal. Merupakan pengukuran radiometrik observasional, belum tentu kebakaran fisik di daratan."
                      : "A satellite pixel flagged as thermally anomalous. An observational radiometric measurement, not necessarily a verified physical fire."}
                  </dd>

                  <dt>{lang === "id" ? "Daya Radiasi Api (FRP, MW)" : "FRP (MW)"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Fire Radiative Power (Megawatt) — laju sesaat pancaran energi radiasi termal yang diukur selama satelit melintas."
                      : "Fire Radiative Power (Megawatts) — the instantaneous rate of emitted thermal radiative energy measured during a satellite overpass."}
                  </dd>

                  <dt>{lang === "id" ? "Hari dalam Setahun (DOY 1–366)" : "DOY (Day of Year 1–366)"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Urutan posisi hari kalender dalam tahun matahari. Dibuat 366 posisi untuk mengakomodasi tahun kabisat secara konsisten."
                      : "Ordinal position of the calendar day within the solar year. Standardized to 366 positions to accommodate leap-year telemetry."}
                  </dd>

                  <dt>{lang === "id" ? "Terharmonisasi" : "Harmonized"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Observasi dari sensor VIIRS yang dipetakan ke skala pengukuran standar MODIS, selalu disertai rentang ketidakpastian empiris berbatas."
                      : "A VIIRS-derived observation mapped onto the MODIS measurement scale, always accompanied by its bounded empirical uncertainty interval."}
                  </dd>

                  <dt>{lang === "id" ? "Setara MODIS (MW)" : "MODIS-equivalent (MW)"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Standar kalibrasi lintas sensor terpadu yang memastikan kesinambungan deret waktu melintasi transisi sensor 2012."
                      : "The unified cross-sensor calibration standard that ensures unbroken time series continuity across the 2012 sensor transition."}
                  </dd>

                  <dt>{lang === "id" ? "Celah Pengamatan (Retrieval Gap)" : "Retrieval Gap"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Hari di mana satelit tidak melintas atau terjadi kegagalan data. Wajib dipertahankan sebagai celah pengamatan dan tidak pernah diganti dengan 0 MW."
                      : "A day where satellite orbit coverage was missing or invalid telemetry occurred. Strictly preserved as a gap and never substituted with 0 MW."}
                  </dd>

                  <dt>{lang === "id" ? "Tahun Memenuhi Syarat (Penyebut)" : "Eligible Years (Denominator)"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Dalam perbandingan tahun aktif / tahun eligible, penyebut hanya menghitung tahun dengan cakupan observasi aktif. Tahun tanpa data tidak pernah diasumsikan normal."
                      : "In years_active / years_eligible, the denominator counts only years with active observation coverage. Missing years are never assumed inactive."}
                  </dd>

                  <dt>{lang === "id" ? "Tingkat Keyakinan (Confidence)" : "Confidence"}</dt>
                  <dd>
                    {lang === "id"
                      ? "Tingkat kepastian anomali termal radiometrik (rendah / nominal / tinggi) yang dipetakan secara sistematis dari algoritma klasifikasi sensor."
                      : "Low / nominal / high radiometric anomaly certainty, mapped systematically from each sensor’s internal classification algorithm."}
                  </dd>
                </dl>

                <div style={{ borderTop: "1px solid var(--line)", marginTop: 12, paddingTop: 10, fontSize: 11.5, color: "var(--ink2)" }}>
                  {lang === "id" ? "Bersifat historis & deskriptif — bukan prediktif." : "Historical & descriptive — not predictive."}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </aside>
    </div>
  );
}
