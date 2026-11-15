import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { seasonsOption, init } from "../echarts";
import { useAoi } from "../App";

export default function Seasons() {
  const { aoi, theme, lang, t } = useAoi();
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
      chart.current.setOption(seasonsOption(cal.climatology, cal.climatology_smoothed_median_mw, cal.critical_windows, theme));
      const ro = new ResizeObserver(() => chart.current?.resize());
      ro.observe(ref.current);
      return () => {
        ro.disconnect();
        chart.current?.dispose();
      };
    }
  }, [cal, theme]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            {t("seasons_chip")}
          </span>
          <h1>{t("seasons_title")}</h1>
          <p className="sub">
            {t("seasons_desc")}
          </p>
        </div>
        <div className="state-chip chip-warn" style={{ fontWeight: 600 }}>
          {t("seasons_chip_thresh")}
        </div>
      </div>

      {loading && (
        <div className="status-panel loading" style={{ marginTop: 20 }}>
          <div className="status-title">{t("seasons_loading_title")}</div>
          <p className="status-desc">{t("seasons_loading_desc")}</p>
          <div className="skel" style={{ height: 320, marginTop: 10 }} />
        </div>
      )}

      {err && (
        <div className="status-panel failed" style={{ marginTop: 20 }}>
          <div className="status-title">{t("seasons_err_title")}</div>
          <p className="status-desc">{t("seasons_err_desc")}</p>
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
                <th>{t("seasons_col_window")}</th>
                <th>{t("seasons_col_years")}</th>
                <th>{t("seasons_col_median")}</th>
              </tr>
            </thead>
            <tbody>
              {cal.critical_windows.map((w, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>
                    {w.start_md} – {w.end_md}
                    {w.wraps_new_year ? t("seasons_wraps_nye") : ""}
                  </td>
                  <td className="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
                    {t("seasons_years_active", { active: w.years_active ?? "—", eligible: w.years_eligible ?? "—" })}
                  </td>
                  <td className="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
                    {w.median_intensity_mw != null ? `${w.median_intensity_mw.toLocaleString(lang === "id" ? "id-ID" : "en-US")} MW` : "—"}
                  </td>
                </tr>
              ))}
              {cal.critical_windows.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ padding: "18px 14px", color: "var(--ink2)", textAlign: "center" }}>
                    {t("seasons_no_window")}
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
            {t("seasons_footer_note")}
          </div>
        </div>
      )}

      {!loading && !err && cal && (
        <div className="boundary" style={{ marginTop: 18 }}>
          <b>{t("seasons_boundary_title")}</b> {t("seasons_boundary_lead")}
          <p className="sub" style={{ marginTop: 3 }}>
            {t("seasons_boundary_body")}
          </p>
        </div>
      )}
    </div>
  );
}
