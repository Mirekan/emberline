import { useEffect, useRef } from "react";
import { compareOption, init } from "../echarts";
import { useAoi } from "../App";

export default function Compare() {
  const { series } = useAoi();
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<ReturnType<typeof init> | null>(null);

  useEffect(() => {
    if (series && ref.current) {
      chart.current?.dispose();
      chart.current = init(ref.current);
      chart.current.setOption(compareOption(series.days));
      const onResize = () => chart.current?.resize();
      window.addEventListener("resize", onResize);
      return () => { window.removeEventListener("resize", onResize); chart.current?.dispose(); };
    }
  }, [series]);

  const computed = series?.fixture == null;

  return (
    <div className="grid2">
      <div>
        <h1>Analytics — raw records vs harmonized</h1>
        <p className="sub">The naive splice jumps where MODIS hands over to VIIRS. The harmonized series keeps the level consistent and always travels with its interval.</p>
        {series && <div className="card" style={{ marginTop: 24 }}>
          <div ref={ref} style={{ width: "100%", height: 420 }} />
          <div className="legend-row">
            <span className="item"><span className="swatch" style={{ background: "var(--modis)" }} />MODIS raw (reference)</span>
            <span className="item"><span className="swatch" style={{ background: "repeating-linear-gradient(90deg,var(--viirs) 0 3px,transparent 3px 6px)" }} />VIIRS raw</span>
            <span className="item"><span className="swatch" style={{ background: "repeating-linear-gradient(90deg,var(--naive) 0 6px,transparent 6px 10px)" }} />Naive splice (uncorrected)</span>
            <span className="item"><span className="swatch" style={{ background: "var(--harm)", height: 5 }} />Harmonized + interval</span>
          </div>
        </div>}
      </div>
      <aside>
        <div className="card">
          <h2>Series — dash pattern + color</h2>
          <div className="legend-row" style={{ borderTop: "none", paddingTop: 0, flexDirection: "column", alignItems: "stretch", gap: 14 }}>
            <span className="item"><span className="swatch" style={{ background: "var(--modis)" }} />MODIS raw (reference)</span>
            <span className="item"><span className="swatch" style={{ background: "repeating-linear-gradient(90deg,var(--viirs) 0 3px,transparent 3px 6px)" }} />VIIRS raw — dotted</span>
            <span className="item"><span className="swatch" style={{ background: "repeating-linear-gradient(90deg,var(--naive) 0 6px,transparent 6px 10px)" }} />Naive splice — dashed, uncorrected</span>
            <span className="item"><span className="swatch" style={{ background: "var(--harm)", height: 5 }} />Harmonized — solid, with interval</span>
          </div>
        </div>
        <div className="card">
          <h2>Splice Stress Test</h2>
          {computed
            ? <p className="sub">Computed numbers live in /api/method — served from held-out artifacts, never decorative.</p>
            : <p className="sub">Stress-test numbers are served from held-out artifacts — computed, never decorative.</p>}
        </div>
        <button className="btn secondary" style={{ width: "100%", justifyContent: "center" }}
          onClick={() => window.open(`/api/aoi/${series?.aoi_id}/export?what=series`, "_blank")}>
          Export CSV — daily series
        </button>
      </aside>
    </div>
  );
}
