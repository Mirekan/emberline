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
          RIGOROUS VALIDATION STANDARD
        </span>
        <h1>Methodology — held-out cross-sensor validation</h1>
        <p className="sub">
          Model training partition: {m?.split.train_years[0]}–{m?.split.train_years[m.split.train_years.length - 1]},
          independent evaluation partition: {m?.split.test_years[0]}–{m?.split.test_years[m.split.test_years.length - 1]}.
          All competing baselines are scored against the identical held-out test partition. Where harmonization does not improve upon raw metrics, EmberLine discloses this honestly.
        </p>

        {loading && (
          <div className="status-panel loading" style={{ marginTop: 20 }}>
            <div className="status-title">Memuat data validasi metodologi…</div>
            <p className="status-desc">Mengevaluasi metrik transisi sensor dan sebaran galat.</p>
            <div className="skel" style={{ height: 260, marginTop: 10 }} />
          </div>
        )}

        {err && (
          <div className="status-panel failed" style={{ marginTop: 20 }}>
            <div className="status-title">Data Metodologi Belum Tersedia</div>
            <p className="status-desc">Data evaluasi metodologi untuk wilayah ini sedang dalam tahap pemrosesan.</p>
            {aoi !== "riau" && (
              <div style={{ marginTop: 12 }}>
                <button className="btn secondary" onClick={() => setAoi("riau")}>
                  Buka Riau (Data Siap)
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
                    <td style={{ fontWeight: 600 }}>Mean log-ratio bias</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.mean_log_ratio_bias)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Symmetric Mean Absolute Percentage Error (sMAPE %)</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.smape)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Pearson correlation coefficient (daily / weekly)</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.pearson_daily)} / {fmt(m.metrics.pearson_weekly)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Spearman rank correlation (daily / weekly)</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.spearman_daily)} / {fmt(m.metrics.spearman_weekly)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Log-space coefficient of determination (R²)</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.log_space_r2)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Kolmogorov-Smirnov (KS) statistic / Wasserstein distance</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.ks_statistic)} / {fmt(m.metrics.wasserstein_distance)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Calendar seasonality pattern correlation</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.calendar_pattern_correlation)}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Empirical interval coverage (nominal 80% confidence)</td>
                    <td colSpan={3} className="mono">{fmt(m.metrics.interval_coverage_empirical)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="grid2" style={{ marginTop: 18, gridTemplateColumns: "1fr 1fr" }}>
              <div className="card">
                <h2>Methodological limitations</h2>
                <ul style={{ listStyle: "none", padding: 0, marginTop: 12 }}>
                  {m.limitations.map((l, i) => (
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
                <h2>Satellite data sources &amp; citations</h2>
                <p className="sub mono" style={{ marginTop: 8, fontSize: 11.5 }}>
                  NASA FIRMS — MODIS C6.1 (Giglio et al. 2016)<br />
                  VIIRS 375 m VNP14IMG (Schroeder et al. 2014)
                </p>
                <p className="sub" style={{ marginTop: 8, fontSize: 12 }}>
                  “We acknowledge the use of data and/or imagery from NASA’s Fire Information for Resource Management System (FIRMS), part of NASA’s ESDIS.”
                </p>
                <div style={{ display: "flex", gap: 10, marginTop: 16, flexWrap: "wrap" }}>
                  <button
                    className="btn secondary"
                    onClick={() => window.open(`/api/aoi/${aoi}/export?what=series`, "_blank")}
                    title="Export daily harmonized time series to CSV"
                  >
                    Export daily series (CSV)
                  </button>
                  <button
                    className="btn secondary"
                    onClick={() => window.open(`/api/aoi/${aoi}/export?what=windows`, "_blank")}
                    title="Export seasonal burning windows to CSV"
                  >
                    Export seasonal windows (CSV)
                  </button>
                </div>
              </div>
            </div>

            <div className="boundary" style={{ marginTop: 18 }}>
              <b>Mandatory Scientific Disclosure: Historical &amp; descriptive — not predictive.</b>
              <p className="sub" style={{ marginTop: 2 }}>
                EmberLine calibrates retrospective satellite observations to ensure unbroken scientific record continuity. It does not predict future fire ignitions or assess real-time emergency risks.
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
            <h2 style={{ fontSize: 15, margin: 0 }}>Telemetry glossary &amp; definitions</h2>
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
                  Standardized scientific definitions for every measurement unit and state in this console.
                </p>
                <dl style={{ marginTop: 8 }}>
                  <dt>Hotspot</dt>
                  <dd>A satellite pixel flagged as thermally anomalous. An observational radiometric measurement, not necessarily a verified physical fire.</dd>

                  <dt>FRP (MW)</dt>
                  <dd>Fire Radiative Power (Megawatts) — the instantaneous rate of emitted thermal radiative energy measured during a satellite overpass.</dd>

                  <dt>DOY (Day of Year 1–366)</dt>
                  <dd>Ordinal position of the calendar day within the solar year. Standardized to 366 positions to accommodate leap-year telemetry.</dd>

                  <dt>Harmonized</dt>
                  <dd>A VIIRS-derived observation mapped onto the MODIS measurement scale, always accompanied by its bounded empirical uncertainty interval.</dd>

                  <dt>MODIS-equivalent (MW)</dt>
                  <dd>The unified cross-sensor calibration standard that ensures unbroken time series continuity across the 2012 sensor transition.</dd>

                  <dt>Retrieval Gap</dt>
                  <dd>A day where satellite orbit coverage was missing or invalid telemetry occurred. Strictly preserved as a gap and never substituted with 0 MW.</dd>

                  <dt>Eligible Years (Denominator)</dt>
                  <dd>In <span className="mono">years_active / years_eligible</span>, the denominator counts only years with active observation coverage. Missing years are never assumed inactive.</dd>

                  <dt>Confidence</dt>
                  <dd>Low / nominal / high radiometric anomaly certainty, mapped systematically from each sensor’s internal classification algorithm.</dd>
                </dl>

                <div style={{ borderTop: "1px solid var(--line)", marginTop: 12, paddingTop: 10, fontSize: 11.5, color: "var(--ink2)" }}>
                  Historical &amp; descriptive — not predictive.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </aside>
    </div>
  );
}
