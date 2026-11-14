/* Tile-comparison builder (user directive: "ada perbandingan tahun ada perbandingan bulan,
   bukan matrix tahun × tanggal") — one tile = one year, or one tile = one month.
   Color: white → orange (ramp 01 Foundations), normalized to the peak in view.
   Honesty states preserved: retrieval-gap tiles are hatched and never zero-filled. */
import type { Calendar } from "./api";

type CalYearT = Calendar["years"][0];

const RAMP = ["#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A"]; // low → peak
const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

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
  if (val <= 0 || max <= 0) return "#FFFFFF"; // valid zero / empty → white
  const t = val / max;
  if (t <= 0.25) return RAMP[0];
  if (t <= 0.5) return RAMP[1];
  if (t <= 0.75) return RAMP[2];
  if (t < 1) return RAMP[3];
  return RAMP[4];
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
