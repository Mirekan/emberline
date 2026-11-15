/* Tile-comparison builder (user directive: "ada perbandingan tahun ada perbandingan bulan,
   bukan matrix tahun × tanggal") — one tile = one year, or one tile = one month.
   Color: theme-aware surface → warm glowing incandescent fire gradient.
   Honesty states preserved: retrieval-gap tiles are hatched and never zero-filled. */
import type { Calendar } from "./api";

type CalYearT = Calendar["years"][0];

export const MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
export const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const MONTH_ABBR = MONTHS_ID;

export type Tile = {
  key: string;
  label: string;
  total: number;       // harmonized FRP-sum (MW), nulls excluded — never zero-filled
  activeDays: number;  // days with FRP > 0
  gapDays: number;     // retrieval-gap days
  days: number;        // positions in scope
  isGap: boolean;      // entire scope is retrieval gap
  fill: string;        // tile background
  tier: number;        // -1 (gap), 0 (zero), 1..5 (intensity)
  isPeak: boolean;
};

function assignTiers(raw: Omit<Tile, "tier" | "isPeak" | "fill">[]): Tile[] {
  const nonGaps = raw.filter(t => !t.isGap && t.total > 0);
  if (nonGaps.length === 0) {
    return raw.map(t => ({
      ...t,
      fill: t.isGap ? "#DCDAD4" : "var(--surface)",
      tier: t.isGap ? -1 : 0,
      isPeak: false,
    }));
  }

  const max = Math.max(...nonGaps.map(t => t.total));
  const sortedValues = [...nonGaps.map(t => t.total)].sort((a, b) => a - b);

  return raw.map(t => {
    if (t.isGap) {
      return { ...t, fill: "#DCDAD4", tier: -1, isPeak: false };
    }
    if (t.total <= 0) {
      return { ...t, fill: "var(--surface)", tier: 0, isPeak: false };
    }
    if (t.total === max) {
      return { ...t, fill: "", tier: 5, isPeak: true };
    }

    // Rank-based relative percentile among positive tiles for distinct visual contrast
    const rank = sortedValues.indexOf(t.total);
    const ratio = rank / Math.max(1, sortedValues.length - 1);
    let tier = 1;
    if (ratio >= 0.72) tier = 4;
    else if (ratio >= 0.45) tier = 3;
    else if (ratio >= 0.20) tier = 2;
    else tier = 1;

    return { ...t, fill: "", tier, isPeak: false };
  });
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
  return assignTiers(raw);
}

/** One tile per month. yearSel ("all" | year) scopes which years aggregate in. */
export function monthTiles(years: CalYearT[], yearSel: string, lang: "id" | "en" = "id"): Tile[] {
  const months = lang === "en" ? MONTHS_EN : MONTHS_ID;
  const src = yearSel === "all" ? years : years.filter(y => String(y.year) === yearSel);
  const raw = Array.from({ length: 12 }, (_, m) => {
    const mm = String(m + 1).padStart(2, "0");
    const ps = src.map(y => y.positions.filter(p => p.month_day.slice(0, 2) === mm));
    return { key: mm, label: months[m], ...summarize(ps) };
  });
  return assignTiers(raw);
}

/* ---- Raw-sensor tiles ----
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
  return assignTiers(raw);
}

/** One tile per year, summed from the RAW sensor column (no harmonization). */
export function yearTilesFromDays(days: Day[], monthSel: string, field: RawField): Tile[] {
  return tilesFromDays(
    days.filter(d => monthSel === "all" || d.date.slice(5, 7) === monthSel),
    d => d.date.slice(0, 4), k => k, field);
}

/** One tile per month, summed from the RAW sensor column (no harmonization). */
export function monthTilesFromDays(days: Day[], yearSel: string, field: RawField, lang: "id" | "en" = "id"): Tile[] {
  const months = lang === "en" ? MONTHS_EN : MONTHS_ID;
  return tilesFromDays(
    days.filter(d => yearSel === "all" || d.date.slice(0, 4) === yearSel),
    d => d.date.slice(5, 7), k => months[Number(k) - 1], field);
}
