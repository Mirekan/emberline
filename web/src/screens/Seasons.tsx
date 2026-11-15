import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { seasonsOption, init } from "../echarts";
import { useAoi } from "../App";

export default function Seasons() {
  const { aoi } = useAoi();
  const [cal, setCal] = useState<Awaited<ReturnType<typeof api.calendar>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof init> | null>(null);

  useEffect(() => {
    setLoading(true);
    setErr(null);
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

  useEffect(() => {
    if (cal && ref.current) {
      chart.current?.dispose();
      chart.current = init(ref.current);
      chart.current.setOption(seasonsOption(cal.climatology, cal.climatology_smoothed_median_mw, cal.critical_windows));
      const ro = new ResizeObserver(() => chart.current?.resize());
      ro.observe(ref.current);
      return () => {
        ro.disconnect();
        chart.current?.dispose();
      };
    }
  }, [cal]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            CLIMATOLOGICAL BASELINE
          </span>
          <h1>Seasonal profile — Day of Year (DOY 1–366) climatology</h1>
          <p className="sub">
            Median daily FRP with interquartile range (IQR) over eligible observation years, smoothed ±7 days. The shaded band indicates the critical burning window at the 75th percentile threshold — historical record, not a predictive forecast.
          </p>
        </div>
        <div className="state-chip chip-warn" style={{ fontWeight: 600 }}>
          75th percentile threshold
        </div>
      </div>

      {loading && (
        <div className="status-panel loading" style={{ marginTop: 20 }}>
          <div className="status-title">Loading seasonal climatology telemetry…</div>
          <p className="status-desc">Calculating Day of Year (DOY 1–366) median and interquartile distribution across eligible years.</p>
          <div className="skel" style={{ height: 320, marginTop: 10 }} />
        </div>
      )}

      {err && (
        <div className="status-panel failed" style={{ marginTop: 20 }}>
          <div className="status-title">Could not load seasonal climatology</div>
          <p className="status-desc">{err}</p>
        </div>
      )}

      {!loading && !err && cal && (
        <div className="card" style={{ marginTop: 20 }}>
          <div ref={ref} style={{ width: "100%", height: 360 }} />
        </div>
      )}

      {!loading && !err && cal && (
        <div className="card" style={{ marginTop: 18, padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr>
                <th>Critical burning window span (DOY / Dates)</th>
                <th>Active / eligible years (denominator)</th>
                <th>Median intensity (FRP MW)</th>
              </tr>
            </thead>
            <tbody>
              {cal.critical_windows.map((w, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>
                    {w.start_md} – {w.end_md}
                    {w.wraps_new_year ? " (wraps calendar year-end)" : ""}
                  </td>
                  <td className="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
                    {w.years_active ?? "—"} / {w.years_eligible ?? "—"} years active
                  </td>
                  <td className="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
                    {w.median_intensity_mw != null ? `${w.median_intensity_mw.toLocaleString("en-US")} MW` : "—"}
                  </td>
                </tr>
              ))}
              {cal.critical_windows.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ padding: "18px 14px", color: "var(--ink2)", textAlign: "center" }}>
                    No seasonal window met the minimum 3-consecutive-day threshold at this quantile.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          <div
            style={{
              padding: "10px 16px",
              borderTop: "1px solid var(--line)",
              fontSize: 11.5,
              color: "var(--ink2)",
              background: "var(--sunken)",
            }}
          >
            Missing observation years are not inactive fire years — denominators count eligible satellite years only. Sparse records are labeled insufficient, never assumed normal.
          </div>
        </div>
      )}

      {!loading && !err && cal && (
        <div className="boundary" style={{ marginTop: 18 }}>
          <b>Mandatory Climatological Boundary:</b> Critical window is descriptive climatology, NOT a safe-to-burn recommendation.
          <p className="sub" style={{ marginTop: 3 }}>
            This evaluation identifies when fire radiative activity has historically clustered in this region. It provides no forecast or endorsement regarding whether any date is safe for controlled agricultural burning.
          </p>
        </div>
      )}
    </div>
  );
}
