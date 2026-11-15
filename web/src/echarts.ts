import * as echarts from "echarts";
import type { CalYear } from "./api";

export const RAMP = ["#F8ECD4", "#F0D8A8", "#E5BE77", "#D59B47", "#C07A2A"];

const reduced = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
type ChartTheme = "light" | "dark";

function isDarkMode(theme?: ChartTheme): boolean {
  if (theme) return theme === "dark";
  if (typeof window === "undefined") return false;
  const documentTheme = document.documentElement.getAttribute("data-theme");
  if (documentTheme === "dark") return true;
  if (documentTheme === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function getThemeFont(theme?: ChartTheme) {
  const dark = isDarkMode(theme);
  return {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
    color: dark ? "#BBB7AC" : "#423F39",
  };
}

function getAxisLineColor(theme?: ChartTheme): string {
  return isDarkMode(theme) ? "rgba(255, 255, 255, 0.16)" : "rgba(20, 19, 17, 0.16)";
}

function getSplitLineColor(theme?: ChartTheme): string {
  return isDarkMode(theme) ? "rgba(255, 255, 255, 0.07)" : "rgba(20, 19, 17, 0.07)";
}

export function init(el: HTMLElement) {
  return echarts.init(el, null, { renderer: "canvas", devicePixelRatio: window.devicePixelRatio || 1 });
}

/* Calendar heatmap — 366 month/day columns × year rows; 5 states via pattern+text. */
export function calendarOption(years: CalYear[], denom: number, theme?: ChartTheme) {
  const mdList = years[0]?.positions.map(p => p.month_day) ?? [];
  const yLabels = years.map(y => String(y.year));
  const heatData: [number, number, number][] = [];
  const special: { value: [number, number]; style: string; reason?: string }[] = [];
  const unc: [number, number][] = [];
  const dark = isDarkMode(theme);
  const font = getThemeFont(theme);

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
    animation: !reduced,
    progressive: 0,
    textStyle: font,
    grid: { left: 64, right: 16, top: 8, bottom: 40 },
    xAxis: {
      type: "category",
      data: mdList,
      axisLine: { lineStyle: { color: getAxisLineColor(theme) } },
      axisTick: { show: false },
      axisLabel: {
        color: font.color,
        fontSize: 10,
        interval: (i: number) => mdList[i].endsWith("-01"),
      },
    },
    yAxis: {
      type: "category",
      data: yLabels,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: font.color,
        fontSize: 11,
        fontFamily: "IBM Plex Mono",
      },
    },
    visualMap: {
      type: "piecewise",
      show: false,
      pieces: [
        { min: 0, max: 0, color: dark ? "#1E2028" : "#F7F5F1" },
        { gt: 0, lte: 6, color: RAMP[0] },
        { gt: 6, lte: 12, color: RAMP[1] },
        { gt: 12, lte: 20, color: RAMP[2] },
        { gt: 20, lte: 32, color: RAMP[3] },
        { gt: 32, color: RAMP[4] },
      ],
    },
    tooltip: { show: false },
    series: [
      {
        type: "heatmap",
        data: heatData,
        animation: false,
        progressive: 0,
        itemStyle: { borderColor: dark ? "#17191F" : "#FFFFFF", borderWidth: 0.5 },
        emphasis: { itemStyle: { borderColor: dark ? "#F5F4EE" : "#21201C", borderWidth: 1 } },
      },
      {
        type: "custom",
        animation: false,
        progressive: 20000,
        silent: true,
        z: 5,
        data: special,
        renderItem: (params: any, api: any) => {
          const pt = api.coord([api.value(0), api.value(1)]);
          const w = api.size([1, 0])[0], h = api.size([0, 1])[1];
          const st = special[params.dataIndex].style;
          const x = pt[0] - w / 2, y = pt[1] - h / 2;
          if (st === "na") return { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: dark ? "#2A2E38" : "#DCDAD4" } };
          if (st === "gap") {
            return {
              type: "group",
              children: [
                { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: "transparent", stroke: dark ? "rgba(255,255,255,0.25)" : "rgba(33,32,28,0.30)", lineWidth: 0.5 } },
                { type: "line", shape: { x1: x, y1: y + h, x2: x + w, y2: y }, style: { stroke: dark ? "rgba(255,255,255,0.40)" : "rgba(33,32,28,0.45)", lineWidth: 0.8 } },
              ],
            };
          }
          if (st === "ins") {
            return {
              type: "rect",
              shape: { x, y, width: w, height: h },
              style: { fill: "transparent", stroke: dark ? "rgba(255,255,255,0.30)" : "rgba(33,32,28,0.35)", lineWidth: 0.6, lineDash: [1.5, 1.5] },
            };
          }
          return {
            type: "group",
            children: [
              { type: "rect", shape: { x, y, width: w, height: h }, style: { fill: dark ? "#1E2028" : "#F7F5F1" } },
              { type: "circle", shape: { cx: pt[0], cy: pt[1], r: Math.min(1.4, h / 5) }, style: { fill: dark ? "rgba(255,255,255,0.60)" : "rgba(33,32,28,0.55)" } },
            ],
          };
        },
      },
      {
        type: "scatter",
        data: unc,
        symbolSize: 2,
        animation: false,
        silent: true,
        z: 6,
        itemStyle: { color: dark ? "#F5F4EE" : "#21201C", opacity: 0.6 },
      },
    ],
  };
}

/* Compare — MODIS raw / VIIRS raw / naive splice / harmonized + interval.
   `visible` toggles each series (legend click-to-show-hide in Compare screen).
   MANDATORY GUARDRAIL: Uncertainty band (_lo and _span) is preserved intact. */
export function compareOption(
  days: {
    date: string;
    source_flag: string;
    raw_modis_frp_mw: number | null;
    raw_viirs_frp_mw: number | null;
    harmonized_lo_mw: number | null;
    harmonized_hi_mw: number | null;
    harmonized_estimate_mw: number | null;
  }[],
  visible: { modis: boolean; viirs: boolean; naive: boolean; harm: boolean } = { modis: true, viirs: true, naive: true, harm: true },
  theme?: ChartTheme,
) {
  const ts = days.map(d => d.date);
  const mk = (data: (number | null)[]) => data.map((v, i) => (v == null ? [ts[i], null] : [ts[i], v]));
  const lo = days.map(d => d.harmonized_lo_mw);
  const hi = days.map(d => d.harmonized_hi_mw);
  const span = hi.map((h, i) => (h == null || lo[i] == null ? null : h - lo[i]));
  const font = getThemeFont(theme);
  const dark = isDarkMode(theme);

  const seriesList: any[] = [];

  if (visible.harm) {
    seriesList.push(
      {
        name: "_lo",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "u",
        data: mk(lo),
        lineStyle: { opacity: 0 },
        areaStyle: { color: "transparent" },
        z: 1,
      },
      {
        name: "_span",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "u",
        data: mk(span),
        lineStyle: { opacity: 0 },
        areaStyle: { color: dark ? "rgba(167, 139, 250, 0.22)" : "rgba(76, 53, 150, 0.18)" },
        z: 2,
      },
      {
        name: "Harmonized",
        type: "line",
        symbol: "none",
        data: mk(days.map(d => d.harmonized_estimate_mw)),
        lineStyle: { color: dark ? "#A78BFA" : "#483188", width: 3 },
        itemStyle: { color: dark ? "#A78BFA" : "#483188" },
        z: 8,
      }
    );
  }

  if (visible.modis) {
    seriesList.push({
      name: "MODIS raw (reference)",
      type: "line",
      symbol: "none",
      data: mk(days.map(d => d.raw_modis_frp_mw)),
      lineStyle: { color: dark ? "#60A5FA" : "#1D5B9E", width: 1.6 },
      itemStyle: { color: dark ? "#60A5FA" : "#1D5B9E" },
      z: 5,
    });
  }

  if (visible.viirs) {
    seriesList.push({
      name: "VIIRS raw",
      type: "line",
      symbol: "none",
      data: mk(days.map(d => d.raw_viirs_frp_mw)),
      lineStyle: { color: dark ? "#F59E0B" : "#B56D00", width: 1.6, type: [1, 4] },
      itemStyle: { color: dark ? "#F59E0B" : "#B56D00" },
      z: 6,
    });
  }

  if (visible.naive) {
    seriesList.push({
      name: "Naive splice (uncorrected)",
      type: "line",
      symbol: "none",
      data: mk(days.map(d => (d.source_flag === "observed_modis" ? d.raw_modis_frp_mw : d.raw_viirs_frp_mw))),
      lineStyle: { color: dark ? "#F472B6" : "#983C5C", width: 2, type: [6, 4] },
      itemStyle: { color: dark ? "#F472B6" : "#983C5C" },
      z: 7,
    });
  }

  return {
    animation: !reduced,
    textStyle: font,
    grid: { left: 8, right: 16, top: 30, bottom: 32, containLabel: true },
    xAxis: {
      type: "time",
      axisLine: { lineStyle: { color: getAxisLineColor(theme) } },
      axisLabel: {
        color: font.color,
        fontSize: 11,
        formatter: (v: number) => String(new Date(v).getUTCFullYear()),
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      name: "FRP-sum (MW, MODIS-equivalent)",
      nameTextStyle: { color: font.color, fontSize: 11 },
      axisLabel: { color: font.color, fontSize: 11 },
      splitLine: { lineStyle: { color: getSplitLineColor(theme) } },
    },
    tooltip: { show: false },
    series: seriesList,
  };
}

/* Seasons — climatology median + IQR band + critical-window band (stacked trick) */
export function seasonsOption(
  clim: { month_day: string; median_mw: number | null; iqr?: { p25_mw: number; p75_mw: number } | null; state: string }[],
  smooth: (number | null)[],
  windows: { start_md: string; end_md: string; wraps_new_year?: boolean }[],
  theme?: ChartTheme,
) {
  const md = clim.map(c => c.month_day);
  const p25 = clim.map(c => (c.iqr ? c.iqr.p25_mw : null));
  const p75 = clim.map(c => (c.iqr ? c.iqr.p75_mw : null));
  const span = p75.map((v, i) => (v == null || p25[i] == null ? null : v - p25[i]));
  const inWin = (s: string) =>
    windows.some(w => {
      if (!w.wraps_new_year) return s >= w.start_md && s <= w.end_md;
      return s >= w.start_md || s <= w.end_md;
    });
  const wBase = md.map(() => 0);
  const wSpan = md.map(s => (inWin(s) ? 100 : null));
  const font = getThemeFont(theme);
  const dark = isDarkMode(theme);

  return {
    animation: !reduced,
    textStyle: font,
    grid: { left: 8, right: 16, top: 26, bottom: 34, containLabel: true },
    xAxis: {
      type: "category",
      data: md,
      boundaryGap: false,
      axisLine: { lineStyle: { color: getAxisLineColor(theme) } },
      axisTick: { show: false },
      axisLabel: {
        color: font.color,
        fontSize: 10,
        interval: (i: number) => md[i].endsWith("-01"),
      },
    },
    yAxis: {
      type: "value",
      max: (v: { max: number }) => Math.ceil((v.max * 1.25) / 5) * 5,
      name: "FRP-sum (MW)",
      nameTextStyle: { color: font.color, fontSize: 11 },
      axisLabel: { color: font.color, fontSize: 11 },
      splitLine: { lineStyle: { color: getSplitLineColor(theme) } },
    },
    tooltip: { show: false },
    series: [
      {
        name: "_wb",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "w",
        data: wBase,
        lineStyle: { opacity: 0 },
        areaStyle: { color: "transparent" },
        z: 0,
      },
      {
        name: "_ws",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "w",
        data: wSpan,
        lineStyle: { opacity: 0 },
        areaStyle: { color: dark ? "rgba(240, 106, 56, 0.28)" : "rgba(214, 138, 63, 0.25)" },
        z: 0,
      },
      {
        name: "_p25",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "q",
        data: p25,
        lineStyle: { opacity: 0 },
        areaStyle: { color: "transparent" },
        z: 3,
      },
      {
        name: "_p75",
        type: "line",
        symbol: "none",
        silent: true,
        stack: "q",
        data: span,
        lineStyle: { opacity: 0 },
        areaStyle: { color: dark ? "rgba(255, 255, 255, 0.14)" : "rgba(92, 90, 84, 0.20)" },
        z: 4,
      },
      {
        name: "median",
        type: "line",
        symbol: "none",
        data: smooth.map(v => (v == null ? null : v)),
        lineStyle: { color: dark ? "#F5F4EE" : "#141311", width: 3 },
        itemStyle: { color: dark ? "#F5F4EE" : "#141311" },
        z: 6,
      },
    ],
  };
}
