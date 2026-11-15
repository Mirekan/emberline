import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api, Calendar, Preset } from "../api";
import { yearTiles, monthTiles, yearTilesFromDays, monthTilesFromDays, Tile, MONTH_ABBR, RawField } from "../calendarTiles";
import { useAoi } from "../App";
import Seasons from "./Seasons";

const RAMP6 = ["#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A", "#9B4C12"];

export default function CalendarScreen({ goMap }: { goMap: () => void }) {
  const { aoi, setAoi, setCalFilter, series } = useAoi();
  const [cal, setCal] = useState<Calendar | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [view, setView] = useState<"yearly" | "monthly">("yearly");
  const [yearSel, setYearSel] = useState("all");
  const [monthSel, setMonthSel] = useState("all");
  const [sensor, setSensor] = useState<"harm" | "modis" | "viirs">("harm");
  const [sel, setSel] = useState<{ key: string; title: string; sub: string; value: string; notes: string[] } | null>(null);

  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    setSel(null); // stale selection from previous AOI must not survive
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

  const yearsAll = cal?.years ?? [];
  const rawField: RawField = sensor === "modis" ? "raw_modis_frp_mw" : "raw_viirs_frp_mw";
  const days = series?.days ?? [];

  const tiles = useMemo<Tile[]>(
    () => (sensor === "harm"
      ? (view === "yearly" ? yearTiles(yearsAll, monthSel) : monthTiles(yearsAll, yearSel))
      : (view === "yearly" ? yearTilesFromDays(days, monthSel, rawField) : monthTilesFromDays(days, yearSel, rawField))),
    [sensor, view, yearsAll, yearSel, monthSel, days, rawField]
  );

  const sensorLabel = sensor === "harm"
    ? "Harmonized FRP-sum (MODIS-equivalent, MW)"
    : sensor === "modis"
    ? "Raw MODIS FRP-sum (1 km scale, MW)"
    : "Raw VIIRS FRP-sum (375 m scale, MW)";

  const readyPresets = presets.filter(p => p.artifact_status === "available");

  const summary = useMemo(() => {
    if (!tiles.length) return null;
    const peak = tiles.reduce((p, t) => (t.total > p.total ? t : p), tiles[0]);
    return {
      total: tiles.reduce((a, t) => a + t.total, 0),
      peak,
      active: tiles.filter(t => !t.isGap && t.total > 0).length,
      gaps: tiles.reduce((a, t) => a + t.gapDays, 0),
      unit: view === "yearly" ? "active years" : "active months",
      peakUnit: view === "yearly" ? "year" : "month",
      valueLabel: sensor === "harm"
        ? "Total Harmonized FRP-sum (MW)"
        : `Total Raw ${sensor === "modis" ? "MODIS" : "VIIRS"} FRP-sum (MW)`,
      span: view === "yearly"
        ? (monthSel === "all" ? "full annual cycle" : `${MONTH_ABBR[Number(monthSel) - 1]} only`)
        : (yearSel === "all" ? `all ${yearsAll.length} observation years` : `year ${yearSel}`),
    };
  }, [tiles, view, monthSel, yearSel, yearsAll.length, sensor]);

  const onTile = (t: Tile) => {
    const notes: string[] = [];
    notes.push(`${t.activeDays} active day${t.activeDays === 1 ? "" : "s"} with FRP > 0 (out of ${t.days} observation positions)`);
    if (t.isGap) {
      notes.push("Entire interval is a satellite retrieval gap — no valid observations; never zero-filled.");
    } else if (t.gapDays > 0) {
      notes.push(`${t.gapDays} satellite retrieval-gap day${t.gapDays === 1 ? "" : "s"} — omitted from mean, never assumed zero.`);
    }
    if (view === "yearly" && monthSel !== "all") {
      notes.push(`Restricted to seasonal month: ${MONTH_ABBR[Number(monthSel) - 1]}`);
    }
    if (view === "monthly" && yearSel === "all") {
      notes.push(`Climatological composite across ${yearsAll.length} observation years (${yearsAll[0]?.year}–${yearsAll[yearsAll.length - 1]?.year})`);
    }
    if (view === "monthly" && yearSel !== "all") {
      notes.push(`Calendar Year: ${yearSel}`);
    }

    setSel({
      key: t.key,
      title: view === "yearly" ? `Year ${t.label}` : `${t.label} · ${yearSel === "all" ? "All years composite" : yearSel}`,
      sub: sensor === "harm"
        ? "Harmonized FRP-sum (MODIS-equivalent scale)"
        : `${sensorLabel} — native sensor aperture, not cross-sensor adjusted`,
      value: `${t.total.toLocaleString("en-US")} MW`,
      notes,
    });
  };

  const calFilterDesc = view === "yearly"
    ? `Yearly · ${monthSel === "all" ? "all months" : `${MONTH_ABBR[Number(monthSel) - 1]} only`}`
    : `Monthly · ${yearSel === "all" ? "all years" : yearSel}`;

  const goMapWithFilter = () => {
    setCalFilter(calFilterDesc);
    goMap();
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            TEMPORAL COMPARISON MATRIX
          </span>
          <h1>Fire activity temporal comparison</h1>
          <p className="sub">
            Each tile displays aggregated Fire Radiative Power (MW) per {view === "yearly" ? "calendar year" : "calendar month"}. Brighter intensity indicates elevated FRP-sum. Retrieval gaps are strictly distinguished from zero detections.
          </p>
          <button
            className="btn secondary"
            style={{ marginTop: 12, padding: "7px 15px", fontSize: 12.5 }}
            onClick={goMapWithFilter}
            title="Inspect spatial hotspot distribution on the Fire Map with this temporal filter"
          >
            Inspect on Fire Map — {calFilterDesc} →
          </button>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>Observation series</span>
            <select
              className="glass-select"
              value={sensor}
              onChange={e => { setSensor(e.target.value as any); setSel(null); }}
            >
              <option value="harm">Harmonized (MODIS-equivalent, MW)</option>
              <option value="modis">MODIS raw (1 km Aqua, MW)</option>
              <option value="viirs">VIIRS raw (375 m S-NPP, MW)</option>
            </select>
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>Aggregation interval</span>
            <select
              className="glass-select"
              value={view}
              onChange={e => { setView(e.target.value as any); setSel(null); }}
            >
              <option value="yearly">Yearly comparison</option>
              <option value="monthly">Monthly comparison</option>
            </select>
          </label>

          {view === "monthly" && (
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span>Target year</span>
              <select
                className="glass-select"
                value={yearSel}
                onChange={e => { setYearSel(e.target.value); setSel(null); }}
              >
                <option value="all">All observation years</option>
                {yearsAll.map(y => (
                  <option key={y.year} value={String(y.year)}>{y.year}</option>
                ))}
              </select>
            </label>
          )}

          {view === "yearly" && (
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span>Seasonal scope</span>
              <select
                className="glass-select"
                value={monthSel}
                onChange={e => { setMonthSel(e.target.value); setSel(null); }}
              >
                <option value="all">All 12 months</option>
                {MONTH_ABBR.map((m, i) => (
                  <option key={m} value={String(i + 1).padStart(2, "0")}>{m}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </div>

      {sensor !== "harm" && cal && (
        <div className="boundary" style={{ marginTop: 18 }}>
          <b>Sensor scale notice: Raw {sensor === "modis" ? "MODIS" : "VIIRS"} observations.</b>
          <p className="sub" style={{ marginTop: 2 }}>
            Satellite sensor spatial apertures and detection thresholds differ fundamentally (MODIS 1 km vs VIIRS 375 m). Raw counts are NOT directly comparable across the 2012 handover without EmberLine harmonization.
          </p>
        </div>
      )}

      {loading && (
        <div className="status-panel loading" style={{ marginTop: 20 }}>
          <div className="status-title">Loading fire calendar telemetry…</div>
          <p className="status-desc">Compiling multi-year observation matrix from satellite artifacts.</p>
          <div className="skel" style={{ height: 28, marginTop: 8 }} />
        </div>
      )}

      {err && (
        <div className="status-panel failed" style={{ marginTop: 20 }}>
          <div className="status-title">Could not load fire calendar telemetry</div>
          <p className="status-desc">{err}</p>
          {readyPresets.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginTop: 10 }}>
              <span style={{ fontSize: 12, color: "var(--ink2)" }}>Switch to region with generated artifacts:</span>
              {readyPresets.map(p => (
                <button
                  key={p.id}
                  className="btn secondary"
                  style={{ padding: "5px 12px", fontSize: 12 }}
                  onClick={() => setAoi(p.id)}
                >
                  Inspect {p.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!loading && !err && cal && (
        <div className="grid2" style={{ marginTop: 18, gridTemplateColumns: "3fr 2fr" }}>
          <div className="card">
            {summary && (
              <div className="cal-summary">
                <span className="big">{summary.total.toLocaleString("en-US")}</span>
                <span className="unit">{summary.valueLabel}</span>
                <span className="stat">
                  Peak {summary.peakUnit}: <b>{summary.peak.label}</b> ({summary.peak.total.toLocaleString("en-US")} MW)
                </span>
                <span className="stat">
                  <b>{summary.active}</b> {summary.unit} active
                </span>
                <span className="stat">
                  <b>{summary.gaps}</b> retrieval-gap days (never zero-filled)
                </span>
              </div>
            )}

            <div className="tiles">
              {tiles.map(t => {
                const isSelected = sel?.key === t.key;
                return (
                  <button
                    key={t.key}
                    className={"tile" + (t.isGap ? " gap" : "") + (isSelected ? " selected" : "")}
                    style={{ background: t.isGap ? undefined : t.fill }}
                    onClick={() => onTile(t)}
                    aria-label={`Inspect ${t.label}: ${t.isGap ? "satellite retrieval gap" : `${t.total} MW FRP-sum`}`}
                  >
                    <span className="tile-label">{t.label}</span>
                    <span className="tile-value">
                      {t.isGap ? "Gap (no data)" : `${t.total.toLocaleString("en-US")} MW`}
                    </span>
                    {t.gapDays > 0 && !t.isGap && (
                      <span className="tile-flags">
                        {t.gapDays} gap day{t.gapDays === 1 ? "" : "s"}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="legend-row">
              <span className="item">
                <span className="ramp">
                  {RAMP6.map((c, i) => (
                    <i key={i} style={{ background: c }} />
                  ))}
                </span>
                <span>FRP-sum gradient (low → high relative to view peak)</span>
              </span>
              <span className="item">
                <i className="sw-gap" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>Retrieval gap (no overpass)</span>
              </span>
              <span className="item">
                <i className="sw-zero" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>Valid 0 MW</span>
              </span>
            </div>
          </div>

          <div className="card">
            <h2>Selected {view === "yearly" ? "calendar year" : "calendar month"} inspection</h2>
            <AnimatePresence initial={false} mode="wait">
              {sel ? (
                <motion.div
                  key={sel.key}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ type: "spring", stiffness: 320, damping: 30 }}
                >
                  <div style={{ marginTop: 12 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{sel.title}</span>
                    <p className="sub" style={{ marginTop: 2 }}>{sel.sub}</p>
                  </div>

                  <div className="kpi-box" style={{ marginTop: 14 }}>
                    <span className="kpi-label">FRP-sum aggregate</span>
                    <span className="kpi-val">{sel.value}</span>
                    <span className="kpi-sub">
                      {sensor === "harm" ? "MODIS-equivalent calibrated energy" : "Raw instrument detection sum"}
                    </span>
                  </div>

                  <div style={{ marginTop: 12, display: "grid", gap: 6 }}>
                    {sel.notes.map((n, i) => (
                      <div
                        key={i}
                        style={{
                          fontSize: 12.5,
                          color: "var(--ink2)",
                          background: "var(--sunken)",
                          padding: "6px 10px",
                          borderRadius: 6,
                          border: "1px solid var(--line)",
                        }}
                      >
                        {n}
                      </div>
                    ))}
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="status-panel loading"
                  style={{ marginTop: 12 }}
                >
                  <div className="status-title">No period selected</div>
                  <p className="status-desc">
                    Click any {view === "yearly" ? "year" : "month"} tile in the matrix to inspect its full telemetry profile, active detection days, and retrieval gap audit.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {!loading && !err && cal && (
        <div style={{ marginTop: 32, borderTop: "1px solid var(--line)", paddingTop: 28 }}>
          <Seasons />
        </div>
      )}
    </div>
  );
}
