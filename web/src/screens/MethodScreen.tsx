import { useEffect, useState } from "react";
import { api, Method } from "../api";
import { useAoi } from "../App";

export default function MethodScreen() {
  const { aoi } = useAoi();
  const [m, setM] = useState<Method | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.method(aoi).then(setM).catch(e => setErr(e.message));
  }, [aoi]);

  const fmt = (v: number | string) =>
    typeof v === "string" ? <span style={{ color: "var(--ink3)" }}>{v}</span> : <span className="mono">{v}</span>;

  return (
    <div className="grid2">
      <div>
        <h1>Methodology — validation, held-out years only</h1>
        <p className="sub">Train {m?.split.train_years[0]}–{m?.split.train_years[m.split.train_years.length - 1]},
          test {m?.split.test_years[0]}–{m?.split.test_years[m.split.test_years.length - 1]}.
          Baselines share the same test set. Where harmonization does not improve on the baselines, this page says so.</p>

        {err && <div className="card" style={{ marginTop: 24 }}><h2>Could not load method</h2><p className="sub">{err}</p></div>}

        {m && <>
          <div className="card" style={{ marginTop: 24, padding: 0, overflow: "hidden" }}>
            <table>
              <thead><tr><th>Metric</th><th>B0 · naive splice</th><th>B1 · global ratio</th><th>B2 · harmonized</th></tr></thead>
              <tbody>
                <tr><td>Level shift error (×)</td><td className="mono">{fmt(m.metrics.b0_naive_splice_level_shift ?? "N/A:not_computed")}</td><td className="mono">{fmt(m.metrics.b1_naive_splice_level_shift ?? "N/A:not_computed")}</td><td className="mono">{fmt(m.metrics.b2_naive_splice_level_shift ?? "N/A:not_computed")}</td></tr>
                <tr><td>Mean log-ratio bias</td><td colSpan={3} className="mono">{fmt(m.metrics.mean_log_ratio_bias)}</td></tr>
                <tr><td>sMAPE</td><td colSpan={3} className="mono">{fmt(m.metrics.smape)}</td></tr>
                <tr><td>Pearson daily / weekly</td><td colSpan={3} className="mono">{fmt(m.metrics.pearson_daily)} / {fmt(m.metrics.pearson_weekly)}</td></tr>
                <tr><td>Spearman daily / weekly</td><td colSpan={3} className="mono">{fmt(m.metrics.spearman_daily)} / {fmt(m.metrics.spearman_weekly)}</td></tr>
                <tr><td>log-space R²</td><td colSpan={3} className="mono">{fmt(m.metrics.log_space_r2)}</td></tr>
                <tr><td>KS statistic / Wasserstein</td><td colSpan={3} className="mono">{fmt(m.metrics.ks_statistic)} / {fmt(m.metrics.wasserstein_distance)}</td></tr>
                <tr><td>Calendar pattern correlation</td><td colSpan={3} className="mono">{fmt(m.metrics.calendar_pattern_correlation)}</td></tr>
                <tr><td>Interval coverage (nominal 80%)</td><td colSpan={3} className="mono">{fmt(m.metrics.interval_coverage_empirical)}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="grid2" style={{ marginTop: 20, gridTemplateColumns: "1fr 1fr" }}>
            <div className="card">
              <h2>Limitations</h2>
              <ul style={{ listStyle: "none", padding: 0, marginTop: 12 }}>
                {m.limitations.map((l, i) => <li key={i} style={{ marginBottom: 10, color: "var(--ink2)", fontSize: 13 }}>{l}</li>)}
              </ul>
            </div>
            <div className="card">
              <h2>Data &amp; citations</h2>
              <p className="sub mono" style={{ marginTop: 10 }}>NASA FIRMS — MODIS C6.1 (Giglio et al. 2016)<br />VIIRS 375 m VNP14IMG (Schroeder et al. 2014)</p>
              <p className="sub" style={{ marginTop: 10 }}>“We acknowledge the use of data and/or imagery from NASA’s Fire Information for Resource Management System (FIRMS), part of NASA’s ESDIS.”</p>
              <div style={{ display: "flex", gap: 12, marginTop: 14 }}>
                <button className="btn secondary" onClick={() => window.open(`/api/aoi/${aoi}/export?what=series`, "_blank")}>Export CSV — series</button>
                <button className="btn secondary" onClick={() => window.open(`/api/aoi/${aoi}/export?what=windows`, "_blank")}>Export CSV — windows</button>
              </div>
            </div>
          </div>

          {!m.mock && <div className="boundary" style={{ marginTop: 20 }}>
            <b>Historical &amp; descriptive — not predictive.</b>
          </div>}
        </>}
      </div>

      <aside>
        <div className="card drawer">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: 16 }}>How to read this</h2>
            <span className="mono" style={{ fontSize: 10, color: "var(--ink3)" }}>Esc</span>
          </div>
          <p className="sub">Plain-language definitions for every term in this app.</p>
          <dl className="drawer" style={{ marginTop: 4 }}>
            <dt>Hotspot</dt><dd>A satellite pixel flagged as thermally anomalous. An observation, not necessarily a fire.</dd>
            <dt>FRP</dt><dd>Fire Radiative Power (MW) — the instantaneous radiative energy rate of a detection.</dd>
            <dt>Harmonized</dt><dd>A VIIRS-derived estimate mapped onto the MODIS measurement scale, always shown with its uncertainty interval.</dd>
            <dt>MODIS-equivalent</dt><dd>The shared unit that keeps the record consistent across the 2012 sensor transition.</dd>
            <dt>Confidence</dt><dd>Low / nominal / high, mapped from each sensor’s original confidence column.</dd>
          </dl>
          <div style={{ borderTop: "1px solid var(--line)", marginTop: 14, paddingTop: 12, fontSize: 12, color: "var(--ink2)" }}>
            Historical &amp; descriptive — not predictive.
          </div>
        </div>
      </aside>
    </div>
  );
}
