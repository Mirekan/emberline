import * as echarts from "echarts";
import type { CalYear } from "./api";

export const RAMP = ["#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A"];

const FONT = { fontFamily: "Inter", color: "#5C5A54" };
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function init(el: HTMLElement) {
  return echarts.init(el, null, { renderer: "canvas", devicePixelRatio: 1 });
}

/* Calendar heatmap — 366 month/day columns × year rows; 5 states via pattern+text. */
export function calendarOption(years: CalYear[], denom: number) {
  const mdList = years[0]?.positions.map(p => p.month_day) ?? [];
  const yLabels = years.map(y => String(y.year));
  const heatData: [number, number, number][] = [];
  const special: { value: [number, number]; style: string; reason?: string }[] = [];
  const unc: [number, number][] = [];
  years.forEach((y, yi) => {
    y.positions.forEach((p, xi) => {
      if (p.state === "not_applicable") special.push({ value: [xi, yi], style: "na" });
      else if (p.state === "retrieval_gap") special.push({ value: [xi, yi], style: "gap", reason: p.reason ?? "" });
      else if (p.state === "insufficient_support") special.push({ value: [xi, yi], style: "ins" });
      else if (p.state === "valid_zero") special.push({ value: [xi, yi], style: "zero" });
      else if (p.value_mw != null) heatData.push([xi, yi, p.value_mw]);
      if ((p.flags ?? []).includes("high_uncertainty")) unc.push([xi, yi]);
    });
  });
  return {
    animation: !reduced, progressive: 0, textStyle: FONT,
    grid: { left: 64, right: 16, top: 8, bottom: 40 },
    xAxis: { type: "category", data: mdList, axisLine: { lineStyle: { color: "rgba(33,32,28,0.18)" } },
      axisTick: { show: false }, axisLabel: { color: "#5C5A54", fontSize: 10, interval: (i: number) => mdList[i].endsWith("-01") } },
    yAxis: { type: "category", data: yLabels, inverse: true, axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "#5C5A54", fontSize: 11, fontFamily: "IBM Plex Mono" } },
    visualMap: { type: "piecewise", show: false, pieces: [
      { min: 0, max: 0, color: "#F7F5F1" },
      { gt: 0, lte: 6, color: RAMP[0] }, { gt: 6, lte: 12, color: RAMP[1] },
      { gt: 12, lte: 20, color: RAMP[2] }, { gt: 20, lte: 32, color: RAMP[3] },
      { gt: 32, color: RAMP[4] }] },
    tooltip: { show: false },
    series: [
      { type: "heatmap", data: heatData, animation: false, progressive: 0,
        itemStyle: { borderColor: "#FFFFFF", borderWidth: 0.5 },
        emphasis: { itemStyle: { borderColor: "#21201C", borderWidth: 1 } } },
      { type: "custom", animation: false, progressive: 20000, silent: true, z: 5,
        data: special,
        renderItem: (params: any, api: any) => {
          const pt = api.coord([api.value(0), api.value(1)]);
          const w = api.size([1, 0])[0], h = api.size([0, 1])[1];
          const st = special[params.dataIndex].style;
          const x = pt[0] - w / 2, y = pt[1] - h / 2;
          if (st === "na") return { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: "#DCDAD4" } };
          if (st === "gap") return { type: "group", children: [
            { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: "transparent", stroke: "rgba(33,32,28,0.30)", lineWidth: 0.5 } },
            { type: "line", shape: { x1: x, y1: y + h, x2: x + w, y2: y }, style: { stroke: "rgba(33,32,28,0.45)", lineWidth: 0.8 } }] };
          if (st === "ins") return { type: "rect", shape: { x, y, width: w, height: h },
            style: { fill: "transparent", stroke: "rgba(33,32,28,0.35)", lineWidth: 0.6, lineDash: [1.5, 1.5] } };
          return { type: "group", children: [   // valid zero: dark + center dot
            { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: "#F7F5F1" } },
            { type: "circle", shape: { cx: pt[0], cy: pt[1], r: Math.min(1.4, h / 5) }, style: { fill: "rgba(33,32,28,0.55)" } }] };
        } },
      { type: "scatter", data: unc, symbolSize: 2, animation: false, silent: true, z: 6,
        itemStyle: { color: "#21201C", opacity: 0.5 } },
    ],
  };
}

/* Compare — MODIS raw / VIIRS raw / naive splice / harmonized + interval */
export function compareOption(days: { date: string; source_flag: string; raw_modis_frp_mw: number | null; raw_viirs_frp_mw: number | null; harmonized_lo_mw: number | null; harmonized_hi_mw: number | null; harmonized_estimate_mw: number | null }[]) {
  const ts = days.map(d => d.date);
  const mk = (data: (number | null)[]) => data.map((v, i) => v == null ? [ts[i], null] : [ts[i], v]);
  const lo = days.map(d => d.harmonized_lo_mw);
  const hi = days.map(d => d.harmonized_hi_mw);
  const span = hi.map((h, i) => h == null || lo[i] == null ? null : h - lo[i]);
  return {
    animation: !reduced, textStyle: FONT,
    grid: { left: 56, right: 16, top: 30, bottom: 32 },
    xAxis: { type: "time", axisLine: { lineStyle: { color: "rgba(33,32,28,0.18)" } },
      axisLabel: { color: "#5C5A54", fontSize: 11, formatter: (v: number) => String(new Date(v).getUTCFullYear()) }, splitLine: { show: false } },
    yAxis: { type: "value", name: "FRP-sum (MW, MODIS-equivalent)", nameTextStyle: { color: "#5C5A54", fontSize: 11 },
      axisLabel: { color: "#5C5A54", fontSize: 11 }, splitLine: { lineStyle: { color: "rgba(33,32,28,0.08)" } } },
    tooltip: { show: false },
    series: [
      { name: "_lo", type: "line", symbol: "none", silent: true, stack: "u", data: mk(lo), lineStyle: { opacity: 0 }, areaStyle: { color: "transparent" }, z: 1 },
      { name: "_span", type: "line", symbol: "none", silent: true, stack: "u", data: mk(span), lineStyle: { opacity: 0 }, areaStyle: { color: "rgba(75,63,140,0.18)" }, z: 2 },
      { name: "MODIS raw (reference)", type: "line", symbol: "none", data: mk(days.map(d => d.raw_modis_frp_mw)), lineStyle: { color: "#2D5F9E", width: 1.5 }, itemStyle: { color: "#2D5F9E" }, z: 5 },
      { name: "VIIRS raw", type: "line", symbol: "none", data: mk(days.map(d => d.raw_viirs_frp_mw)), lineStyle: { color: "#B87700", width: 1.5, type: [1, 4] }, itemStyle: { color: "#B87700" }, z: 6 },
      { name: "Naive splice (uncorrected)", type: "line", symbol: "none", data: mk(days.map(d => d.source_flag === "observed_modis" ? d.raw_modis_frp_mw : d.raw_viirs_frp_mw)), lineStyle: { color: "#9E5878", width: 2, type: [6, 4] }, itemStyle: { color: "#9E5878" }, z: 7 },
      { name: "Harmonized", type: "line", symbol: "none", data: mk(days.map(d => d.harmonized_estimate_mw)), lineStyle: { color: "#4B3F8C", width: 3 }, itemStyle: { color: "#4B3F8C" }, z: 8 },
    ],
  };
}

/* Seasons — climatology median + IQR band + critical-window band (stacked trick) */
export function seasonsOption(clim: { month_day: string; median_mw: number | null; iqr?: { p25_mw: number; p75_mw: number } | null; state: string }[], smooth: (number | null)[], windows: { start_md: string; end_md: string; wraps_new_year?: boolean }[]) {
  const md = clim.map(c => c.month_day);
  const med = clim.map(c => c.median_mw);
  const p25 = clim.map(c => c.iqr ? c.iqr.p25_mw : null);
  const p75 = clim.map(c => c.iqr ? c.iqr.p75_mw : null);
  const span = p75.map((v, i) => v == null || p25[i] == null ? null : v - p25[i]);
  const inWin = (s: string) => windows.some(w => {
    if (!w.wraps_new_year) return s >= w.start_md && s <= w.end_md;
    return s >= w.start_md || s <= w.end_md;
  });
  const wBase = md.map(() => 0);
  const wSpan = md.map(s => inWin(s) ? 100 : null);
  return {
    animation: !reduced, textStyle: FONT,
    grid: { left: 52, right: 16, top: 26, bottom: 34 },
    xAxis: { type: "category", data: md, boundaryGap: false, axisLine: { lineStyle: { color: "rgba(33,32,28,0.18)" } },
      axisTick: { show: false }, axisLabel: { color: "#5C5A54", fontSize: 10, interval: (i: number) => md[i].endsWith("-01") } },
    yAxis: { type: "value", max: (v: { max: number }) => Math.ceil((v.max * 1.25) / 5) * 5,
      name: "FRP-sum (MW)", nameTextStyle: { color: "#5C5A54", fontSize: 11 },
      axisLabel: { color: "#5C5A54", fontSize: 11 }, splitLine: { lineStyle: { color: "rgba(33,32,28,0.08)" } } },
    tooltip: { show: false },
    series: [
      { name: "_wb", type: "line", symbol: "none", silent: true, stack: "w", data: wBase, lineStyle: { opacity: 0 }, areaStyle: { color: "transparent" }, z: 0 },
      { name: "_ws", type: "line", symbol: "none", silent: true, stack: "w", data: wSpan, lineStyle: { opacity: 0 }, areaStyle: { color: "rgba(214,138,63,0.25)" }, z: 0 },
      { name: "_p25", type: "line", symbol: "none", silent: true, stack: "q", data: p25, lineStyle: { opacity: 0 }, areaStyle: { color: "transparent" }, z: 3 },
      { name: "_p75", type: "line", symbol: "none", silent: true, stack: "q", data: span, lineStyle: { opacity: 0 }, areaStyle: { color: "rgba(92,90,84,0.22)" }, z: 4 },
      { name: "median", type: "line", symbol: "none", data: smooth.map(v => v == null ? null : v), lineStyle: { color: "#21201C", width: 3 }, itemStyle: { color: "#21201C" }, z: 6 },
    ],
  };
}

/* Weekly chunky calendar — rounded pill cells per week (52 cols × year rows).
   Matches the Figma hi-fi look: thick segments, generous spacing. */
export function calendarWeeklyOption(years: CalYear[]) {
  const yLabels = years.map(y => String(y.year));
  const mdList = years[0]?.positions.map(p => p.month_day) ?? [];
  const weekStart = Array.from({ length: 52 }, (_, wk) => mdList[wk * 7] ?? "");
  const data: [number, number, number][] = [];
  const special: { value: [number, number]; style: string }[] = [];
  years.forEach((y, yi) => {
    const pos = y.positions;
    for (let wk = 0; wk < 52; wk++) {
      const slice = pos.slice(wk * 7, wk * 7 + 7);
      const na = slice.filter(p => p.state === "not_applicable").length;
      const gaps = slice.filter(p => p.state === "retrieval_gap").length;
      if (na === slice.length) { special.push({ value: [wk, yi], style: "na" }); continue; }
      if (gaps >= slice.length - na) { special.push({ value: [wk, yi], style: "gap" }); continue; }
      const vals = slice.filter(p => p.value_mw != null).map(p => p.value_mw as number);
      if (vals.length === 0 || vals.every(v => v === 0)) {
        special.push({ value: [wk, yi], style: "zero" }); continue;
      }
      data.push([wk, yi, Math.round(vals.reduce((a, b) => a + b, 0) * 10) / 10]);
    }
  });
  return {
    animation: !reduced, progressive: 0, textStyle: FONT,
    grid: { left: 64, right: 16, top: 10, bottom: 34 },
    xAxis: { type: "category", data: weekStart, axisLine: { lineStyle: { color: "rgba(33,32,28,0.18)" } },
      axisTick: { show: false },
      axisLabel: { color: "#5C5A54", fontSize: 10,
        interval: (i: number) => i === 0 || weekStart[i].slice(0, 2) !== weekStart[i - 1].slice(0, 2),
        formatter: (v: string) => { const m = Number(v.slice(0, 2)) - 1; return MONTHS[m] ?? v; } } },
    yAxis: { type: "category", data: yLabels, inverse: true,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: "#5C5A54", fontSize: 11, fontFamily: "IBM Plex Mono" } },
    visualMap: { type: "piecewise", show: false, pieces: [
      { gt: 0, lte: 28, color: RAMP[0] }, { gt: 28, lte: 63, color: RAMP[1] },
      { gt: 63, lte: 105, color: RAMP[2] }, { gt: 105, lte: 168, color: RAMP[3] },
      { gt: 168, color: RAMP[4] }] },
    tooltip: { show: false },
    series: [
      { type: "custom", animation: !reduced, progressive: 0, data,
        renderItem: (params: any, api: any) => {
          const pt = api.coord([api.value(0), api.value(1)]);
          const cw = api.size([1, 0])[0], ch = api.size([0, 1])[1];
          const w = Math.max(cw - 6, 4), h = Math.max(ch - 14, 8);
          const val = (api.value(2) as number) || 0;
          const fill = val <= 42 ? RAMP[0] : val <= 98 ? RAMP[1] : val <= 196 ? RAMP[2]
            : val <= 320 ? RAMP[3] : RAMP[4];
          return { type: "rect", shape: { x: pt[0] - w / 2, y: pt[1] - h / 2, width: w, height: h, r: 4 },
            style: { fill },
            emphasis: { style: { stroke: "#21201C", lineWidth: 1 } } };
        } },
      { type: "custom", animation: false, progressive: 20000, silent: true, z: 5, data: special,
        renderItem: (params: any, api: any) => {
          const pt = api.coord([api.value(0), api.value(1)]);
          const cw = api.size([1, 0])[0], ch = api.size([0, 1])[1];
          const w = Math.max(cw - 6, 4), h = Math.max(ch - 14, 8);
          const x = pt[0] - w / 2, y = pt[1] - h / 2;
          const st = special[params.dataIndex].style;
          if (st === "na") return { type: "rect", shape: { x, y, width: w, height: h, r: 4 }, style: { fill: "#DCDAD4" } };
          if (st === "gap") return { type: "group", children: [
            { type: "rect", shape: { x, y, width: w, height: h, r: 4 }, style: { fill: "transparent", stroke: "rgba(33,32,28,0.3)", lineWidth: 0.5 } },
            { type: "line", shape: { x1: x, y1: y + h, x2: x + w, y2: y }, style: { stroke: "rgba(33,32,28,0.4)", lineWidth: 0.8 } }] };
          return { type: "rect", shape: { x, y, width: w, height: h, r: 4 }, style: { fill: "#F7F5F1" } };
        } },
    ],
  };
}
