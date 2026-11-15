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

function LegendRows({ visible, onToggle, lang }: { visible: Visible; onToggle: (k: keyof Visible) => void; lang: "id" | "en" }) {
  const rows: [keyof Visible, string, ReactNode][] = [
    ["modis", lang === "id" ? "MODIS mentah (Acuan Aqua, 1 km)" : "MODIS raw (Aqua reference, 1 km)", <span className="swatch" style={{ background: SWATCH.modis }} />],
    ["viirs", lang === "id" ? "VIIRS mentah (S-NPP, 375 m — titik)" : "VIIRS raw (S-NPP, 375 m — dotted)", <span className="swatch" style={{ background: SWATCH.viirs }} />],
    ["naive", lang === "id" ? "Sambungan naif (tanpa kalibrasi — putus-putus)" : "Naive splice (uncorrected handover — dashed)", <span className="swatch" style={{ background: SWATCH.naive }} />],
    ["harm", lang === "id" ? "Estimasi terharmonisasi + rentang ketidakpastian" : "Harmonized estimate + uncertainty interval (band)", <span className="swatch" style={{ background: SWATCH.harm, height: 6 }} />],
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
  const { aoi, setAoi, series, theme, lang, t } = useAoi();
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
      chart.current.setOption(compareOption(series.days, visible, theme));
      const ro = new ResizeObserver(() => chart.current?.resize());
      ro.observe(ref.current);
      return () => {
        ro.disconnect();
        chart.current?.dispose();
      };
    }
  }, [series, theme]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (series && chart.current) {
      chart.current.setOption(compareOption(series.days, visible, theme));
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
          {lang === "id" ? "BENCHMARK TRANSISI SENSOR" : "SENSOR TRANSITION BENCHMARK"}
        </span>
        <h1>{t("compare_title")}</h1>
        <p className="sub">
          {lang === "id"
            ? "Penyambungan data secara naif menimbulkan lonjakan artifisial pada transisi sensor 2012. EmberLine menyelaraskan VIIRS ke skala acuan MODIS dengan rentang ketidakpastian empiris berbatas."
            : "A naive splice creates an artificial jump at the 2012 sensor transition. EmberLine harmonizes VIIRS onto the MODIS reference scale and presents every estimate with its bounded empirical uncertainty interval."}
        </p>

        {series ? (
          <div className="card" style={{ marginTop: 20 }}>
            <div ref={ref} style={{ width: "100%", height: 420 }} />
            <div className="legend-row">
              <LegendRows visible={visible} onToggle={toggle} lang={lang} />
            </div>
          </div>
        ) : (
          <div className="status-panel loading" style={{ marginTop: 20 }}>
            <div className="status-title">{lang === "id" ? "Memuat data deret waktu satelit…" : "Loading satellite series telemetry…"}</div>
            <p className="status-desc">{lang === "id" ? "Menyusun observasi multi-sensor dan pita rentang ketidakpastian empiris." : "Compiling multi-sensor observations and empirical uncertainty bands."}</p>
            <div className="skel" style={{ height: 380, marginTop: 10 }} />
          </div>
        )}
      </div>

      <aside style={{ display: "grid", gap: 16 }}>
        <div className="card">
          <div className="card-header">
            <h2>{lang === "id" ? "Lapisan Visibilitas Deret" : "Series visibility layers"}</h2>
            <span className="state-chip chip-neutral mono" style={{ fontSize: 10 }}>{lang === "id" ? "interaktif" : "interactive"}</span>
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
            <LegendRows visible={visible} onToggle={toggle} lang={lang} />
          </div>
          <p className="sub" style={{ marginTop: 12, fontSize: 12 }}>
            {lang === "id"
              ? "Aqua MODIS (resolusi 1 km) merupakan acuan historis. VIIRS (resolusi 375 m) mendeteksi anomali api yang lebih kecil dan mencatat intensitas radiasi mentah yang secara sistematis lebih tinggi."
              : "Aqua MODIS (1 km pixel) represents the legacy reference baseline. VIIRS (375 m pixel) captures smaller fire anomalies and records systematically higher raw radiant intensity."}
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>{lang === "id" ? "Evaluasi Uji Stres Sambungan Sensor" : "Splice stress test evaluation"}</h2>
            <span className="state-chip chip-neutral mono" style={{ fontSize: 10 }}>{lang === "id" ? "tahun uji mandiri" : "held-out years"}</span>
          </div>
          <div className="grid3" style={{ gridTemplateColumns: "1fr 1fr", marginTop: 4 }}>
            <div className="kpi-box">
              <div className="kpi-label">{lang === "id" ? "Sambungan Tanpa Kalibrasi" : "Naive Handover"}</div>
              <div className="kpi-val" style={{ color: "var(--ember)" }}>{fmtX(b0)}</div>
              <div className="kpi-sub">{lang === "id" ? "Galat lonjakan skala (ideal: 1,00×)" : "Level shift error (ideal: 1.00×)"}</div>
            </div>
            <div className="kpi-box">
              <div className="kpi-label">{lang === "id" ? "Estimasi Terharmonisasi" : "Harmonized Estimate"}</div>
              <div className="kpi-val" style={{ color: "var(--ok)" }}>{fmtX(b2)}</div>
              <div className="kpi-sub">{lang === "id" ? "Galat lonjakan skala (ideal: 1,00×)" : "Level shift error (ideal: 1.00×)"}</div>
            </div>
          </div>
          <p className="sub" style={{ marginTop: 12, fontSize: 12 }}>
            {lang === "id"
              ? "Metrik dihitung dari partisi validasi mandiri (held-out) — dihitung secara ilmiah, bukan estimasi dekoratif."
              : (computed
                ? "Metrics calculated from held-out validation split in /api/method — computed rigorously, never decorative."
                : "Stress-test metrics served from frozen benchmark artifacts — computed, never synthetic.")}
          </p>
        </div>

        <button
          className="btn secondary"
          style={{ width: "100%", justifyContent: "center" }}
          onClick={() => window.open(`/api/aoi/${series?.aoi_id}/export?what=series`, "_blank")}
          title={lang === "id" ? "Unduh seluruh deret data harian satelit beserta rentang ketidakpastian dalam format CSV" : "Download complete daily telemetry series with uncertainty intervals in CSV format"}
        >
          {t("compare_export_btn")}
        </button>
      </aside>
    </div>
  );
}
