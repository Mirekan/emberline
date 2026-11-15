import { useAoi } from "../App";

// Anomalies — unusual-activity markers. OPTIONAL – BACKLOG (O-01, owner C; needs approval A).
// Honest placeholder: states what it will show, never fabricates flagged days.
export default function Anomalies() {
  const { series } = useAoi();
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            CLIMATOLOGICAL DEVIATION MONITOR
          </span>
          <h1>Anomalies — statistical unusual-activity markers</h1>
        </div>
        <span className="state-chip chip-neutral mono" style={{ fontSize: 11 }}>
          OPTIONAL – BACKLOG (P1 · requires approval A)
        </span>
      </div>

      <p className="sub" style={{ marginTop: 6 }}>
        Preview of module O-01: flags observation days where |z| ≥ 2.5 against the day-of-year (DOY 1–366) climatological baseline (robust median / Median Absolute Deviation). Marked as unusual historical deviations — descriptive statistics only, never predictive alerts or danger warnings.
      </p>

      <div className="card" style={{ marginTop: 20, padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)" }}>
          <h2 style={{ margin: 0 }}>Planned anomaly telemetry telemetry structure</h2>
          <p className="sub" style={{ fontSize: 12, marginTop: 4 }}>
            Strictly contract-honest: all columns will derive from computed baseline artifacts without synthetic interpolation.
          </p>
        </div>
        <table>
          <thead>
            <tr>
              <th>Telemetry Column</th>
              <th>Measurement Unit / Standard</th>
              <th>Scientific Definition &amp; Meaning</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 600 }}>Observation Date</td>
              <td className="mono">YYYY-MM-DD (UTC)</td>
              <td>UTC calendar day of the aggregated satellite detection overpass.</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>Robust z-score</td>
              <td className="mono">z = (FRP - Median) / (1.4826 × MAD)</td>
              <td>Standardized statistical distance from DOY climatology, preserving directional sign (±).</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>Deviation Direction</td>
              <td className="mono">above_normal | below_normal</td>
              <td>Suppressed burning and elevated burning are both significant climatological anomalies.</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>Observed vs Climatology</td>
              <td className="mono">FRP-sum (MW)</td>
              <td>Daily observed harmonized FRP-sum compared directly with climatological DOY median (MW).</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>Baseline Sample Size</td>
              <td className="mono">years_active / years_eligible</td>
              <td>Frozen reference climatology window with explicit eligible-year denominator count.</td>
            </tr>
          </tbody>
        </table>
        <div style={{ padding: "12px 18px", borderTop: "1px solid var(--line)", fontSize: 12, color: "var(--ink2)", background: "var(--sunken)" }}>
          Rows will link directly to the corresponding fire calendar day and time-series analytical views. Under sparse baseline conditions, days are labeled <span className="mono">insufficient_support</span> rather than assumed nominal.
        </div>
      </div>

      <div className="boundary" style={{ marginTop: 18 }}>
        <b>Mandatory Guardrail Notice: Anomaly flags are descriptive statistics — not warning alerts, not forecasts.</b>
        <p className="sub" style={{ marginTop: 4 }}>
          Telemetry implementation scheduled for module O-01 (FR-CAL-5 / FR-UI-8). Until formal deployment, this honest status disclosure ensures zero fabricated or synthetic anomaly flags.
        </p>
      </div>

      {series && (
        <p className="sub mono" style={{ fontSize: 11, marginTop: 14 }}>
          Artifact context: {series.fixture ?? "real production artifacts"} · run ID {series.run_id.slice(-14)}
        </p>
      )}
    </div>
  );
}
