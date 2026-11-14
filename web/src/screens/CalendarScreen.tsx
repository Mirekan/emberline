import { useEffect, useMemo, useState } from "react";
import { api, Calendar, Preset } from "../api";
import { yearTiles, monthTiles, Tile, MONTH_ABBR } from "../calendarTiles";
import { useAoi } from "../App";

const RAMP6 = ["#FFFFFF", "#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A"];

export default function CalendarScreen({ goMap }: { goMap: () => void }) {
  const { aoi, setAoi, setCalFilter } = useAoi();
  const [cal, setCal] = useState<Calendar | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [view, setView] = useState<"yearly" | "monthly">("yearly");
  const [yearSel, setYearSel] = useState("all");
  const [monthSel, setMonthSel] = useState("all");
  const [sel, setSel] = useState<{ title: string; sub: string; value: string; notes: string[] } | null>(null);

  useEffect(() => { api.presets().then(r => setPresets(r.presets)).catch(() => {}); }, []);

  useEffect(() => {
    setErr(null);
    setSel(null); // stale selection from another AOI must not survive
    api.calendar(aoi).then(setCal).catch(e => setErr(e.message));
  }, [aoi]);

  const yearsAll = cal?.years ?? [];
  const tiles = useMemo<Tile[]>(
    () => (view === "yearly" ? yearTiles(yearsAll, monthSel) : monthTiles(yearsAll, yearSel)),
    [view, yearsAll, yearSel, monthSel]);
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
      span: view === "yearly"
        ? (monthSel === "all" ? "full years" : `${MONTH_ABBR[Number(monthSel) - 1]} only`)
        : (yearSel === "all" ? `all ${yearsAll.length} years` : String(yearSel)),
    };
  }, [tiles, view, monthSel, yearSel, yearsAll.length]);

  const onTile = (t: Tile) => {
    const notes: string[] = [];
    notes.push(`${t.activeDays} active day${t.activeDays === 1 ? "" : "s"} with FRP > 0 (of ${t.days} positions)`);
    if (t.isGap) notes.push("Entire scope is a retrieval gap — no observations; never zero-filled");
    else if (t.gapDays > 0) notes.push(`${t.gapDays} retrieval-gap day${t.gapDays === 1 ? "" : "s"} — gaps are never zero-filled`);
    if (view === "yearly" && monthSel !== "all") notes.push(`Scoped to ${MONTH_ABBR[Number(monthSel) - 1]} only`);
    if (view === "monthly" && yearSel === "all") notes.push(`Aggregated across ${yearsAll.length} years (${yearsAll[0]?.year}–${yearsAll[yearsAll.length - 1]?.year})`);
    if (view === "monthly" && yearSel !== "all") notes.push(`Year ${yearSel}`);
    setSel({
      title: view === "yearly" ? `Year ${t.label}` : `${t.label} · ${yearSel === "all" ? "all years" : yearSel}`,
      sub: "Harmonized FRP-sum (MODIS-equivalent)",
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 24, flexWrap: "wrap" }}>
        <div>
          <h1>Burning-activity comparison</h1>
          <p className="sub">One box per {view === "yearly" ? "year" : "month"} — brighter orange = higher FRP-sum. Comparison of periods, not a day-by-day matrix.</p>
          <button className="btn secondary" style={{ marginTop: 12, padding: "8px 16px", fontSize: 13 }}
            onClick={goMapWithFilter}
            title="Open the Fire Map on this AOI, carrying the calendar filter">
            View on Fire Map — {calFilterDesc} →
          </button>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
          <label><span style={{ display: "block", fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>Granularity</span>
            <select className="glass-select" value={view} onChange={e => { setView(e.target.value as any); setSel(null); }}>
              <option value="yearly">Yearly</option>
              <option value="monthly">Monthly</option>
            </select>
          </label>
          {view === "monthly" && <label><span style={{ display: "block", fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>Year</span>
            <select className="glass-select" value={yearSel} onChange={e => { setYearSel(e.target.value); setSel(null); }}>
              <option value="all">All years</option>
              {yearsAll.map(y => <option key={y.year} value={String(y.year)}>{y.year}</option>)}
            </select>
          </label>}
          {view === "yearly" && <label><span style={{ display: "block", fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>Month scope</span>
            <select className="glass-select" value={monthSel} onChange={e => { setMonthSel(e.target.value); setSel(null); }}>
              <option value="all">All months</option>
              {MONTH_ABBR.map((m, i) => <option key={m} value={String(i + 1).padStart(2, "0")}>{m}</option>)}
            </select>
          </label>}
        </div>
      </div>

      {err && <div className="card" style={{ marginTop: 24 }}>
        <h2>Could not load calendar</h2>
        <p className="sub">{err}</p>
        {readyPresets.length > 0 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginTop: 14 }}>
            <span style={{ fontSize: 12, color: "var(--ink2)" }}>Jump to a region with artifacts:</span>
            {readyPresets.map(p => (
              <button key={p.id} className="btn secondary" style={{ padding: "6px 14px", fontSize: 13 }}
                onClick={() => setAoi(p.id)}>
                {p.name}
              </button>
            ))}
          </div>
        )}
      </div>}

      {cal && <div className="grid2" style={{ marginTop: 20, gridTemplateColumns: "3fr 2fr" }}>
        <div className="card">
          {summary && (
            <div className="cal-summary">
              <span className="big">{summary.total.toLocaleString("en-US")}</span>
              <span className="unit">MW harmonized FRP-sum in view</span>
              <span className="stat">Peak {summary.peakUnit}:<b> {summary.peak.label}</b> ({summary.peak.total.toLocaleString("en-US")} MW)</span>
              <span className="stat"><b>{summary.active}</b> {summary.unit}</span>
              <span className="stat"><b>{summary.gaps}</b> retrieval-gap days — never zero-filled</span>
            </div>
          )}
          <div className="tiles">
            {tiles.map(t => (
              <button key={t.key} className={"tile" + (t.isGap ? " gap" : "")}
                style={{ background: t.isGap ? undefined : t.fill }}
                onClick={() => onTile(t)}>
                <span className="tile-label">{t.label}</span>
                <span className="tile-value">{t.isGap ? "no data" : `${t.total.toLocaleString("en-US")} MW`}</span>
                {t.gapDays > 0 && !t.isGap && <span className="tile-flags">{t.gapDays} gap day{t.gapDays === 1 ? "" : "s"}</span>}
              </button>
            ))}
          </div>
          <div className="legend-row">
            <span className="item"><span className="ramp">{RAMP6.map((c, i) => <i key={i} style={{ background: c }} />)}</span>low → high · relative to peak in view</span>
            <span className="item"><i className="sw-gap" style={{ width: 14, height: 14, borderRadius: 3 }} />Retrieval gap “—”</span>
          </div>
        </div>

        <div className="card">
          <h2>Selected {view === "yearly" ? "year" : "month"}</h2>
          {sel ? <>
            <div style={{ marginTop: 12 }}>
              <span style={{ fontSize: 20, fontWeight: 600 }}>{sel.title}</span>
              <p className="sub" style={{ marginTop: 2 }}>{sel.sub}</p>
            </div>
            <span className="mono" style={{ fontSize: 16, display: "inline-block", marginTop: 10 }}>{sel.value}</span>
            {sel.notes.map((n, i) => <p className="sub" key={i}>{n}</p>)}
          </> : <p className="sub">Click a {view === "yearly" ? "year" : "month"} box to inspect it here.</p>}
        </div>
      </div>}
    </div>
  );
}
