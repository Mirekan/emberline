import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, Method } from "../api";
import { compareOption, init } from "../echarts";
import { useAoi } from "../App";

const SWATCH = {
  modis: "var(--modis)",
  viirs: "repeating-linear-gradient(90deg,var(--viirs) 0 3px,transparent 3px 6px)",
  naive: "repeating-linear-gradient(90deg,var(--naive) 0 6px,transparent 6px 10px)",
  harm: "var(--harm)",
} as const;

type Visible = { modis: boolean; viirs: boolean; naive: boolean; harm: boolean };

function LegendRows({ visible, onToggle }: { visible: Visible; onToggle: (k: keyof Visible) => void }) {
  const rows: [keyof Visible, string, ReactNode][] = [
    ["modis", "MODIS raw (Aqua reference, 1 km)", <span className="swatch" style={{ background: SWATCH.modis }} />],
    ["viirs", "VIIRS raw (S-NPP, 375 m — dotted)", <span className="swatch" style={{ background: SWATCH.viirs }} />],
    ["naive", "Naive splice (uncorrected handover — dashed)", <span className="swatch" style={{ background: SWATCH.naive }} />],
    ["harm", "Harmonized estimate + uncertainty interval (band)", <span className="swatch" style={{ background: SWATCH.harm, height: 6 }} />],
  ];

  return (
    <>
      {rows.map(([k, label, sw]) => (
        <button
          key={k}
          className={"legend-toggle" + (visible[k] ? "" : " off")}
          onClick={() => onToggle(k)}
          aria-pressed={visible[k]}
          aria-label={`Toggle series visibility: ${label}`}
          title={`Click to toggle ${label}`}
        >
          {sw}
          <span>{label}</span>
        </button>
      ))}
    </>
  );
}

export default function Compare() {
  const { aoi, setAoi, series } = useAoi();
  const [method, setMethod] = useState<Method | null>(null);
  const [visible, setVisible] = useState<Visible>({ modis: true, viirs: true, naive: true, harm: true });
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof init> | null>(null);

  useEffect(() => {
    api.method(aoi).then(setMethod).catch(() => setMethod(null));
  }, [aoi]);

  useEffect(() => {
    if (series && ref.current) {
      chart.current?.dispose();
      chart.current = init(ref.current);
      chart.current.setOption(compareOption(series.days, visible));
      const ro = new ResizeObserver(() => chart.current?.resize());
      ro.observe(ref.current);
      return () => {
        ro.disconnect();
        chart.current?.dispose();
      };
    }
  }, [series]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (series && chart.current) {
      chart.current.setOption(compareOption(series.days, visible));
    }
  }, [visible]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (k: keyof Visible) => setVisible(v => ({ ...v, [k]: !v[k] }));

  const b0 = method?.metrics.b0_naive_splice_level_shift;
  const b2 = method?.metrics.b2_naive_splice_level_shift;
  const fmtX = (v: number | string | null | undefined) =>
    typeof v === "number" ? `${v.toFixed(2)}×` : "N/A:evaluating";

  const computed = series?.fixture == null;

  return (
    <div className="grid2">
      <div>
        <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
          SENSOR TRANSITION BENCHMARK
        </span>
        <h1>Analytics — raw satellite records vs harmonized series</h1>
        <p className="sub">
          A naive splice creates an artificial jump at the 2012 sensor transition. EmberLine harmonizes VIIRS onto the MODIS reference scale and presents every estimate with its bounded empirical uncertainty interval.
        </p>

        {series ? (
          <div className="card" style={{ marginTop: 20 }}>
            <div ref={ref} style={{ width: "100%", height: 420 }} />
            <div className="legend-row">
              <LegendRows visible={visible} onToggle={toggle} />
            </div>
          </div>
        ) : (
          <div className="status-panel loading" style={{ marginTop: 20 }}>
            <div className="status-title">Memuat data deret waktu satelit…</div>
            <p className="status-desc">Menyusun observasi multi-sensor dan pita rentang ketidakpastian empiris.</p>
            <div className="skel" style={{ height: 380, marginTop: 10 }} />
          </div>
        )}
      </div>

      <aside style={{ display: "grid", gap: 16 }}>
        <div className="card">
          <div className="card-header">
            <h2>Series visibility layers</h2>
            <span className="state-chip chip-neutral mono" style={{ fontSize: 10 }}>interactive</span>
          </div>
          <div
            className="legend-row"
            style={{
              borderTop: "none",
              paddingTop: 0,
              flexDirection: "column",
              alignItems: "stretch",
              gap: 8,
            }}
          >
            <LegendRows visible={visible} onToggle={toggle} />
          </div>
          <p className="sub" style={{ marginTop: 12, fontSize: 12 }}>
            Aqua MODIS (1 km pixel) represents the legacy reference baseline. VIIRS (375 m pixel) captures smaller fire anomalies and records systematically higher raw radiant intensity.
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Splice stress test evaluation</h2>
            <span className="state-chip chip-neutral mono" style={{ fontSize: 10 }}>held-out years</span>
          </div>
          <div className="grid3" style={{ gridTemplateColumns: "1fr 1fr", marginTop: 4 }}>
            <div className="kpi-box">
              <div className="kpi-label">B0 · Naive splice</div>
              <div className="kpi-val" style={{ color: "var(--ember)" }}>{fmtX(b0)}</div>
              <div className="kpi-sub">Level shift error (ideal: 1.00×)</div>
            </div>
            <div className="kpi-box">
              <div className="kpi-label">B2 · Harmonized</div>
              <div className="kpi-val" style={{ color: "var(--ok)" }}>{fmtX(b2)}</div>
              <div className="kpi-sub">Level shift error (ideal: 1.00×)</div>
            </div>
          </div>
          <p className="sub" style={{ marginTop: 12, fontSize: 12 }}>
            {computed
              ? "Metrics calculated from held-out validation split in /api/method — computed rigorously, never decorative."
              : "Stress-test metrics served from frozen benchmark artifacts — computed, never synthetic."}
          </p>
        </div>

        <button
          className="btn secondary"
          style={{ width: "100%", justifyContent: "center" }}
          onClick={() => window.open(`/api/aoi/${series?.aoi_id}/export?what=series`, "_blank")}
          title="Download complete daily telemetry series with uncertainty intervals in CSV format"
        >
          Export daily telemetry series (CSV)
        </button>
      </aside>
    </div>
  );
}
