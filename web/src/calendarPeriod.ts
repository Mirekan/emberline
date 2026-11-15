/* Period-driven calendar builder (Year / Month / Weekly-Monthly-Daily dropdowns).
   Self-contained: own ramp + colors, no circular imports. */
import type { Calendar } from "./api";

const RAMP = ["#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A"];
const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

type CalPos = Calendar["years"][0]["positions"][0];
type CalYearT = Calendar["years"][0];
export type CalPeriod = "weekly" | "monthly" | "daily";
export type ColMeta = { kind: "day" | "week" | "month"; label: string; sublabel: string; year: number; pos: CalPos | null; start?: string; end?: string; total?: number };
export type CalSummary = {
  totalMw: number; peakLabel: string; peakYear: number | null; peakValue: number;
  activeCount: number; gapCount: number; countLabel: string;
};

function chunkFill(val: number, thresholds: number[]): string {
  if (val <= 0) return "#F7F5F1";
  for (let i = 0; i < thresholds.length; i++) if (val <= thresholds[i]) return RAMP[i];
  return RAMP[RAMP.length - 1];
}

const LIGHT = {
  axis: "rgba(33,32,28,0.18)", gapB: "rgba(33,32,28,0.30)", gapH: "rgba(33,32,28,0.45)",
  insB: "rgba(33,32,28,0.35)", zero: "#F7F5F1", zeroDot: "rgba(33,32,28,0.55)",
  na: "#DCDAD4", cellBorder: "#FFFFFF", dot: "#21201C",
};

/** Builds the ECharts option for the selected period + filters, plus click meta + summary. */
export function calendarPeriodOption(
  yearsIn: CalYearT[], mode: CalPeriod, monthSel: string
): { option: any; meta: ColMeta[] | null; summary: CalSummary | null } {
  const mdList = yearsIn[0]?.positions.map(p => p.month_day) ?? [];
  const yLabels = yearsIn.map(y => String(y.year));
  const dailyAll = mode === "daily" && monthSel === "all";
  const thresholds = mode === "weekly" ? [42, 98, 196, 320] : mode === "monthly" ? [120, 270, 450, 720] : [6, 12, 20, 32];

  type Col = { label: string; sublabel: string; cells: { yi: number; val: number | null; state: string; pos: CalPos | null }[] };
  const cols: Col[] = [];

  if (mode === "daily") {
    for (let i = 0; i < 366; i++) {
      const md = mdList[i];
      if (monthSel !== "all" && md.slice(0, 2) !== monthSel) continue;
      cols.push({
        label: md, sublabel: MONTH_ABBR[Number(md.slice(0, 2)) - 1],
        cells: yearsIn.map((y, yi) => {
          const p = y.positions[i];
          return { yi, val: p?.value_mw ?? null, state: p?.state ?? "retrieval_gap", pos: p ?? null };
        }),
      });
    }
  } else if (mode === "monthly") {
    for (let m = 1; m <= 12; m++) {
      const mm = String(m).padStart(2, "0");
      if (monthSel !== "all" && mm !== monthSel) continue;
      cols.push({
        label: mm, sublabel: MONTH_ABBR[m - 1],
        cells: yearsIn.map((y, yi) => {
          const sl = y.positions.filter(p => p.month_day.slice(0, 2) === mm);
          const vals = sl.filter(p => p.value_mw != null).map(p => p.value_mw as number);
          const gaps = sl.filter(p => p.state === "retrieval_gap").length;
          const val = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) * 10) / 10 : null;
          const state = gaps === sl.length ? "retrieval_gap" : val === 0 ? "valid_zero" : "data";
          return { yi, val, state, pos: null };
        }),
      });
    }
  } else {
    for (let wk = 0; wk < 52; wk++) {
      const idx = Array.from({ length: 7 }, (_, k) => wk * 7 + k).filter(i => i < 366);
      if (monthSel !== "all") {
        const monthsIn = idx.map(i => mdList[i]?.slice(0, 2));
        if (!monthsIn.includes(monthSel)) continue;
      }
      cols.push({
        label: mdList[idx[0]] ?? "", sublabel: `${mdList[idx[0]]} – ${mdList[idx[idx.length - 1]]}`,
        cells: yearsIn.map((y, yi) => {
          const sl = idx.map(i => y.positions[i]).filter(Boolean) as CalPos[];
          const vals = sl.filter(p => p.value_mw != null).map(p => p.value_mw as number);
          const gaps = sl.filter(p => p.state === "retrieval_gap").length;
          const val = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) * 10) / 10 : null;
          const state = gaps === sl.length ? "retrieval_gap" : vals.every(v => v === 0) && vals.length ? "valid_zero" : "data";
          return { yi, val, state, pos: sl[0] ?? null };
        }),
      });
    }
  }

  const colLabels = cols.map(c => c.label);
  const heatData: [number, number, number][] = [];
  const special: { value: [number, number]; style: string }[] = [];

  if (dailyAll) {
    yearsIn.forEach((y, yi) => y.positions.forEach((p, xi) => {
      if (p.state === "not_applicable") special.push({ value: [xi, yi], style: "na" });
      else if (p.state === "retrieval_gap") special.push({ value: [xi, yi], style: "gap" });
      else if (p.state === "insufficient_support") special.push({ value: [xi, yi], style: "ins" });
      else if (p.state === "valid_zero") special.push({ value: [xi, yi], style: "zero" });
      else if (p.value_mw != null) heatData.push([xi, yi, p.value_mw]);
    }));
  } else {
    cols.forEach((c, xi) => c.cells.forEach(cell => {
      if (cell.state === "retrieval_gap") special.push({ value: [xi, cell.yi], style: "gap" });
      else if (cell.state === "valid_zero") special.push({ value: [xi, cell.yi], style: "zero" });
      else if (cell.val != null) heatData.push([xi, cell.yi, cell.val]);
    }));
  }

  const chunky = !dailyAll;

  // GitHub-style summary strip for the current filter
  const countLabel = mode === "weekly" ? "active weeks" : mode === "monthly" ? "active months" : "active days";
  let totalMw = 0, peakValue = -1, peakLabel = "—", peakYear: number | null = null, activeCount = 0, gapCount = 0;
  if (dailyAll) {
    yearsIn.forEach(y => y.positions.forEach(p => {
      if (p.state === "retrieval_gap") gapCount++;
      else if (p.value_mw != null) {
        totalMw += p.value_mw;
        if (p.value_mw > 0) activeCount++;
        if (p.value_mw > peakValue) { peakValue = p.value_mw; peakLabel = p.month_day; peakYear = y.year; }
      }
    }));
  } else {
    cols.forEach(c => c.cells.forEach(cell => {
      if (cell.state === "retrieval_gap") gapCount++;
      else if (cell.val != null) {
        totalMw += cell.val;
        if (cell.val > 0) activeCount++;
        if (cell.val > peakValue) { peakValue = cell.val; peakLabel = c.sublabel; peakYear = Number(yLabels[cell.yi]); }
      }
    }));
  }
  const summary: CalSummary = { totalMw: Math.round(totalMw), peakLabel, peakYear,
    peakValue: peakValue < 0 ? 0 : Math.round(peakValue * 10) / 10, activeCount, gapCount, countLabel };
  const meta: ColMeta[] = cols.map((c, xi) => ({
    kind: (mode === "daily" ? "day" : mode === "weekly" ? "week" : "month") as ColMeta["kind"],
    label: mode === "monthly" ? c.sublabel : c.label,
    sublabel: c.sublabel, year: Number(yLabels[0]), pos: null,
    start: mode === "weekly" ? c.sublabel.split(" – ")[0] : undefined,
    end: mode === "weekly" ? c.sublabel.split(" – ")[1] : undefined,
    total: c.cells.reduce((a, cell) => a + (cell.val ?? 0), 0),
  }));
  if (mode === "daily") {
    cols.forEach((c, xi) => c.cells.forEach(cell => {
      meta[xi] = { kind: "day", label: c.label, sublabel: c.sublabel, year: Number(yLabels[cell.yi]), pos: cell.pos };
    }));
  }

  const base = {
    animation: !reduced, progressive: 0, textStyle: { fontFamily: "Inter", color: "#5C5A54" },
    grid: { left: 64, right: 16, top: 12, bottom: dailyAll ? 40 : 30 },
    xAxis: { type: "category", data: colLabels.length ? colLabels : mdList.slice(0, 1),
      axisLine: { lineStyle: { color: LIGHT.axis } }, axisTick: { show: false },
      axisLabel: { color: "#5C5A54", fontSize: 10,
        interval: dailyAll ? (i: number) => mdList[i].endsWith("-01") : true,
        formatter: dailyAll ? (v: string) => MONTH_ABBR[Number(v.slice(0, 2)) - 1] : (v: string) => v } },
    yAxis: { type: "category", data: yLabels, inverse: true,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "#5C5A54", fontSize: 11, fontFamily: "IBM Plex Mono" } },
    visualMap: { type: "piecewise", show: false, pieces: dailyAll
      ? [{ min: 0, max: 0, color: "#F7F5F1" },
         { gt: 0, lte: 6, color: RAMP[0] }, { gt: 6, lte: 12, color: RAMP[1] },
         { gt: 12, lte: 20, color: RAMP[2] }, { gt: 20, lte: 32, color: RAMP[3] },
         { gt: 32, color: RAMP[4] }]
      : [{ min: 0, max: 0, color: "#F7F5F1" },
         ...thresholds.map((t, i) => ({ gt: i === 0 ? 0 : thresholds[i - 1], lte: t, color: RAMP[i] })),
         { gt: thresholds[thresholds.length - 1], color: RAMP[RAMP.length - 1] }] },
    tooltip: { show: false },
  };

  if (!chunky) {
    return { option: { ...base, series: [
      { type: "heatmap", data: heatData, animation: !reduced, progressive: 0,
        itemStyle: { borderColor: LIGHT.cellBorder, borderWidth: 0.5 },
        emphasis: { itemStyle: { borderColor: "#21201C", borderWidth: 1 } } },
      { type: "custom", animation: false, progressive: 20000, silent: true, z: 5, data: special,
        renderItem: (params: any, api: any) => {
          const pt = api.coord([api.value(0), api.value(1)]);
          const w = api.size([1, 0])[0], h = api.size([0, 1])[1];
          const x = pt[0] - w / 2, y = pt[1] - h / 2;
          const st = special[params.dataIndex]?.style ?? "zero";
          if (st === "na") return { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: LIGHT.na } };
          if (st === "gap") return { type: "group", children: [
            { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: "transparent", stroke: LIGHT.gapB, lineWidth: 0.5 } },
            { type: "line", shape: { x1: x, y1: y + h, x2: x + w, y2: y }, style: { stroke: LIGHT.gapH, lineWidth: 0.8 } }] };
          if (st === "ins") return { type: "rect", shape: { x, y, width: w, height: h },
            style: { fill: "transparent", stroke: LIGHT.insB, lineWidth: 0.6, lineDash: [1.5, 1.5] } };
          return { type: "group", children: [
            { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: LIGHT.zero } },
            { type: "circle", shape: { cx: pt[0], cy: pt[1], r: Math.min(1.4, h / 5) }, style: { fill: LIGHT.zeroDot } }] };
        } },
      { type: "scatter", data: [], symbolSize: 2, silent: true, z: 6 },
    ] }, meta: null, summary };
  }

  const gap = mode === "daily" ? 2 : 4;
  const vgap = mode === "daily" ? 6 : 10;
  const pillData = dailyAll ? [] : heatData;
  const pillSpecial = dailyAll ? [] : special;
  return { option: { ...base, series: [
    { type: "custom", animation: !reduced, progressive: 0, data: pillData,
      renderItem: (params: any, api: any) => {
        const pt = api.coord([api.value(0), api.value(1)]);
        const cw = api.size([1, 0])[0], ch = api.size([0, 1])[1];
        const w = Math.max(cw - gap, 4), h = Math.max(ch - vgap, 8);
        const val = (api.value(2) as number) || 0;
        return { type: "rect", shape: { x: pt[0] - w / 2, y: pt[1] - h / 2, width: w, height: h, r: Math.min(4, w / 2) },
          style: { fill: chunkFill(val, thresholds) },
          emphasis: { style: { stroke: "#21201C", lineWidth: 1 } } };
      } },
    { type: "custom", animation: false, progressive: 20000, silent: true, z: 5, data: pillSpecial,
      renderItem: (params: any, api: any) => {
        const pt = api.coord([api.value(0), api.value(1)]);
        const cw = api.size([1, 0])[0], ch = api.size([0, 1])[1];
        const w = Math.max(cw - gap, 4), h = Math.max(ch - vgap, 8);
        const x = pt[0] - w / 2, y = pt[1] - h / 2;
        const st = pillSpecial[params.dataIndex]?.style ?? "zero";
        if (st === "na") return { type: "rect", shape: { x, y, width: w, height: h, r: 3 }, style: { fill: LIGHT.na } };
        if (st === "gap") return { type: "group", children: [
          { type: "rect", shape: { x, y, width: w, height: h, r: 3 }, style: { fill: "transparent", stroke: LIGHT.gapB, lineWidth: 0.5 } },
          { type: "line", shape: { x1: x, y1: y + h, x2: x + w, y2: y }, style: { stroke: LIGHT.gapH, lineWidth: 0.8 } }] };
          return { type: "rect", shape: { x, y, width: w, height: h, r: 3 }, style: { fill: LIGHT.zero } };
        } },
  ] }, meta, summary };
}
