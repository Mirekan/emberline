import { useAoi } from "../App";

// Anomalies — unusual-activity markers. OPTIONAL – BACKLOG (O-01, owner C; needs approval A).
// Honest placeholder: states what it will show, never fabricates flagged days.
export default function Anomalies() {
  const { series } = useAoi();
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 24 }}>
        <h1>Anomalies — unusual-activity markers</h1>
        <span className="state-chip chip-neutral">OPTIONAL – BACKLOG (P1 · needs approval A)</span>
      </div>
      <p className="sub">Preview of O-01: days flagged when |z| ≥ 2.5 against the day-of-year climatology
        (robust median/MAD). Labeled unusual — descriptive statistics, never alerts or forecasts.</p>

      <div className="card" style={{ marginTop: 20 }}>
        <h2>What this screen will show</h2>
        <table style={{ marginTop: 12 }}>
          <thead><tr><th>Column</th><th>Meaning</th></tr></thead>
          <tbody>
            <tr><td>Date</td><td>UTC day of the flagged detection aggregate</td></tr>
            <tr><td>z-score (robust MAD)</td><td>Distance from the day-of-year climatology, ± direction shown</td></tr>
            <tr><td>Direction</td><td>Above season / below season — both are anomalies, both are reported</td></tr>
            <tr><td>vs climatology</td><td>Observed FRP-sum vs climatological median, in MW</td></tr>
            <tr><td>Baseline years</td><td>The frozen climatology window + eligible-year count</td></tr>
          </tbody>
        </table>
        <p className="sub" style={{ marginTop: 12 }}>
          Rows will link to the calendar day and the Compare view. Unfavorable or sparse-baseline
          results are reported as-is; nothing is flagged that the frozen baseline cannot support.
        </p>
      </div>

      <div className="boundary" style={{ marginTop: 20 }}>
        <b>Anomaly flags are descriptive statistics — not alerts, not forecasts.</b>
        <p className="sub" style={{ marginTop: 4 }}>
          Built when owner C has capacity (FR-CAL-5 / FR-UI-8); until then this backlog card is the honest status.
        </p>
      </div>
      {series && <p className="sub mono" style={{ fontSize: 11 }}>{series.fixture ?? "real artifacts"} · run {series.run_id.slice(-14)}</p>}
    </div>
  );
}
