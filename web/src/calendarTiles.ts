/* Tile-comparison builder (user directive: "ada perbandingan tahun ada perbandingan bulan,
   bukan matrix tahun × tanggal") — one tile = one year, or one tile = one month.
   Color: theme-aware surface → ember, normalized to the peak in view.
   Honesty states preserved: retrieval-gap tiles are hatched and never zero-filled. */
import type { Calendar } from "./api";

type CalYearT = Calendar["years"][0];

const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

export type Tile = {
  key: string;
  label: string;
  total: number;       // harmonized FRP-sum (MW), nulls excluded — never zero-filled
  activeDays: number;  // days with FRP > 0
  gapDays: number;     // retrieval-gap days
  days: number;        // positions in scope
  isGap: boolean;      // entire scope is retrieval gap
  fill: string;        // tile background
};

function fillFor(val: number, max: number): string {
  if (val <= 0 || max <= 0) return "var(--surface)";
  const t = val / max;
  const intensity = t <= 0.25 ? 8 : t <= 0.5 ? 14 : t <= 0.75 ? 20 : t < 1 ? 26 : 32;
  return `color-mix(in srgb, var(--ember) ${intensity}%, var(--surface))`;
}

function summarize(ps: CalYearT["positions"][]) {
  const flat = ps.flat();
  const vals = flat.filter(p => p.value_mw != null).map(p => p.value_mw as number);
  const gapDays = flat.filter(p => p.state === "retrieval_gap").length;
  return {
    total: Math.round(vals.reduce((a, b) => a + b, 0)),
    activeDays: vals.filter(v => v > 0).length,
    gapDays,
    days: flat.length,
    isGap: flat.length > 0 && gapDays === flat.length,
  };
}

/** One tile per year. monthSel ("01".."12"|"all") scopes which months count. */
export function yearTiles(years: CalYearT[], monthSel: string): Tile[] {
  const raw = years.map(y => {
    const ps = y.positions.filter(p => monthSel === "all" || p.month_day.slice(0, 2) === monthSel);
    return { key: String(y.year), label: String(y.year), ...summarize([ps]) };
  });
  const max = Math.max(0, ...raw.map(t => t.total));
  return raw.map(t => ({ ...t, fill: t.isGap ? "#DCDAD4" : fillFor(t.total, max) }));
}

/** One tile per month. yearSel ("all" | year) scopes which years aggregate in. */
export function monthTiles(years: CalYearT[], yearSel: string): Tile[] {
  const src = yearSel === "all" ? years : years.filter(y => String(y.year) === yearSel);
  const raw = Array.from({ length: 12 }, (_, m) => {
    const mm = String(m + 1).padStart(2, "0");
    const ps = src.map(y => y.positions.filter(p => p.month_day.slice(0, 2) === mm));
    return { key: mm, label: MONTH_ABBR[m], ...summarize(ps) };
  });
  const max = Math.max(0, ...raw.map(t => t.total));
  return raw.map(t => ({ ...t, fill: t.isGap ? "#DCDAD4" : fillFor(t.total, max) }));
}

export { MONTH_ABBR };

/* ---- Raw-sensor tiles (user: "belom ada konteks atau milih buat viirs atau modis") ----
   Built client-side from series.days — raw instrument scale, NOT MODIS-equivalent. */

export type RawField = "raw_modis_frp_mw" | "raw_viirs_frp_mw";
type Day = { date: string; raw_modis_frp_mw: number | null; raw_viirs_frp_mw: number | null };

function tilesFromDays(days: Day[], keyOf: (d: Day) => string, labelOf: (k: string) => string, field: RawField): Tile[] {
  const groups = new Map<string, { vals: number[]; gaps: number; count: number }>();
  for (const d of days) {
    const k = keyOf(d);
    const g = groups.get(k) ?? { vals: [], gaps: 0, count: 0 };
    g.count++;
    const v = d[field];
    if (v == null) g.gaps++;
    else g.vals.push(v);
    groups.set(k, g);
  }
  const raw = [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([k, g]) => ({
    key: k, label: labelOf(k),
    total: Math.round(g.vals.reduce((a, b) => a + b, 0)),
    activeDays: g.vals.filter(v => v > 0).length,
    gapDays: g.gaps, days: g.count,
    isGap: g.count > 0 && g.gaps === g.count,
  }));
  const max = Math.max(0, ...raw.map(t => t.total));
  return raw.map(t => ({ ...t, fill: t.isGap ? "#DCDAD4" : fillFor(t.total, max) }));
}

/** One tile per year, summed from the RAW sensor column (no harmonization). */
export function yearTilesFromDays(days: Day[], monthSel: string, field: RawField): Tile[] {
  return tilesFromDays(
    days.filter(d => monthSel === "all" || d.date.slice(5, 7) === monthSel),
    d => d.date.slice(0, 4), k => k, field);
}

/** One tile per month, summed from the RAW sensor column (no harmonization). */
export function monthTilesFromDays(days: Day[], yearSel: string, field: RawField): Tile[] {
  return tilesFromDays(
    days.filter(d => yearSel === "all" || d.date.slice(0, 4) === yearSel),
    d => d.date.slice(5, 7), k => MONTH_ABBR[Number(k) - 1], field);
}
