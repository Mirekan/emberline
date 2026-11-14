import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { seasonsOption, init } from "../echarts";
import { useAoi } from "../App";

export default function Seasons() {
  const { aoi } = useAoi();
  const [cal, setCal] = useState<Awaited<ReturnType<typeof api.calendar>> | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof init> | null>(null);

  useEffect(() => {
    setErr(null);
    api.calendar(aoi).then(setCal).catch(e => setErr(e.message));
  }, [aoi]);

  useEffect(() => {
    if (cal && ref.current) {
      chart.current?.dispose();
      chart.current = init(ref.current);
      chart.current.setOption(seasonsOption(cal.climatology, cal.climatology_smoothed_median_mw, cal.critical_windows));
      const onResize = () => chart.current?.resize();
      window.addEventListener("resize", onResize);
      return () => { window.removeEventListener("resize", onResize); chart.current?.dispose(); };
    }
  }, [cal]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 24 }}>
        <div>
          <h1>Seasonal profile — day of year climatology</h1>
          <p className="sub">Median with interquartile range over eligible years, smoothed ±7 days. The shaded band is the critical burning window at the 75th percentile — historical, not a forecast.</p>
        </div>
        <div className="state-chip chip-warn" style={{ fontWeight: 600 }}>75th percentile</div>
      </div>

      {err && <div className="card" style={{ marginTop: 24 }}><h2>Could not load climatology</h2><p className="sub">{err}</p></div>}
      {cal && <div className="card" style={{ marginTop: 24 }}>
        <div ref={ref} style={{ width: "100%", height: 360 }} />
      </div>}

      {cal && <div className="card" style={{ marginTop: 20, padding: 0, overflow: "hidden" }}>
        <table>
          <thead><tr>
            <th>Critical burning windows — 75th percentile</th><th>Years active</th><th>Years eligible</th><th>Median intensity</th>
          </tr></thead>
          <tbody>
            {cal.critical_windows.map((w, i) => (
              <tr key={i}>
                <td>{w.start_md} – {w.end_md}{w.wraps_new_year ? " (wraps New Year)" : ""}</td>
                <td>{w.years_active ?? "—"} of {w.years_eligible ?? "—"} eligible</td>
                <td>—</td>
                <td className="mono">{w.median_intensity_mw ?? "—"} MW</td>
              </tr>
            ))}
            {cal.critical_windows.length === 0 && <tr><td colSpan={4}>No window met the min-run-3-day rule at this threshold.</td></tr>}
          </tbody>
        </table>
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--line)", fontSize: 12, color: "var(--ink2)" }}>
          Missing years are not inactive years — denominators count eligible years only. Sparse records are labeled insufficient, never “normal”.
        </div>
      </div>}

      {cal && <div className="boundary" style={{ marginTop: 20 }}>
        <b>Critical window is not a safe-to-burn recommendation.</b>
        <p className="sub" style={{ marginTop: 4 }}>This page answers “when is fire historically active here”, with its denominators. It says nothing about whether any date is safe to burn.</p>
      </div>}
    </div>
  );
}
