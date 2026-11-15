import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api, Calendar, Preset } from "../api";
import { yearTiles, monthTiles, yearTilesFromDays, monthTilesFromDays, Tile, MONTHS_ID, MONTHS_EN, RawField } from "../calendarTiles";
import { useAoi } from "../App";
import { PRESET_NAMES } from "../presets";
import SearchableRegionSelect from "../components/SearchableRegionSelect";
import Seasons from "./Seasons";

type CalendarSensor = "harm" | "modis" | "viirs";

export default function CalendarScreen({ goMap }: { goMap: () => void }) {
  const { aoi, setAoi, setCalFilter, series, lang, t } = useAoi();
  const [cal, setCal] = useState<Calendar | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [view, setView] = useState<"yearly" | "monthly">("yearly");
  const [yearSel, setYearSel] = useState("all");
  const [monthSel, setMonthSel] = useState("all");
  const [sensor, setSensor] = useState<CalendarSensor>("harm");
  const [sel, setSel] = useState<{ key: string; title: string; sub: string; value: string; notes: string[] } | null>(null);

  const monthNames = lang === "en" ? MONTHS_EN : MONTHS_ID;

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
      ? (view === "yearly" ? yearTiles(yearsAll, monthSel) : monthTiles(yearsAll, yearSel, lang))
      : (view === "yearly" ? yearTilesFromDays(days, monthSel, rawField) : monthTilesFromDays(days, yearSel, rawField, lang))),
    [sensor, view, yearsAll, yearSel, monthSel, days, rawField, lang]
  );

  const sensorLabel = sensor === "harm"
    ? t("cal_sensor_harm")
    : sensor === "modis"
    ? t("cal_sensor_modis")
    : t("cal_sensor_viirs");

  const readyPresets = presets.filter(p => p.artifact_status === "available");

  const summary = useMemo(() => {
    if (!tiles.length) return null;
    const peak = tiles.reduce((p, item) => (item.total > p.total ? item : p), tiles[0]);
    return {
      total: tiles.reduce((a, item) => a + item.total, 0),
      peak,
      active: tiles.filter(item => !item.isGap && item.total > 0).length,
      gaps: tiles.reduce((a, item) => a + item.gapDays, 0),
      unit: view === "yearly" ? t("cal_period_year_active") : t("cal_period_month_active"),
      peakUnit: view === "yearly" ? t("cal_period_year") : t("cal_period_month"),
      valueLabel: sensor === "harm"
        ? t("cal_summary_harm_label")
        : t("cal_summary_raw_label", { sensor: sensor === "modis" ? "MODIS" : "VIIRS" }),
      span: view === "yearly"
        ? (monthSel === "all" ? t("cal_summary_full_annual") : t("cal_summary_month_only", { month: monthNames[Number(monthSel) - 1] }))
        : (yearSel === "all" ? t("cal_summary_all_years_span", { count: yearsAll.length }) : t("cal_summary_year_only", { year: yearSel })),
    };
  }, [tiles, view, monthSel, yearSel, yearsAll.length, sensor, lang, t, monthNames]);

  const onTile = (tile: Tile) => {
    const notes: string[] = [];
    notes.push(t("cal_note_active_days", { active: tile.activeDays, total: tile.days }));
    if (tile.isGap) {
      notes.push(t("cal_note_full_gap"));
    } else if (tile.gapDays > 0) {
      notes.push(t("cal_note_partial_gap", { count: tile.gapDays }));
    }
    if (view === "yearly" && monthSel !== "all") {
      notes.push(t("cal_note_month_bound", { month: monthNames[Number(monthSel) - 1] }));
    }
    if (view === "monthly" && yearSel === "all") {
      notes.push(t("cal_note_clim_comp", {
        count: yearsAll.length,
        start: yearsAll[0]?.year ?? 2012,
        end: yearsAll[yearsAll.length - 1]?.year ?? 2026,
      }));
    }
    if (view === "monthly" && yearSel !== "all") {
      notes.push(t("cal_note_cal_year", { year: yearSel }));
    }

    setSel({
      key: tile.key,
      title: view === "yearly"
        ? (lang === "id" ? `Tahun ${tile.label}` : `Year ${tile.label}`)
        : (lang === "id"
            ? `Bulan ${tile.label} · ${yearSel === "all" ? "Rata-rata semua tahun" : `Tahun ${yearSel}`}`
            : `Month ${tile.label} · ${yearSel === "all" ? "All-year average" : `Year ${yearSel}`}`),
      sub: sensor === "harm"
        ? t("cal_inspect_harm_sub")
        : t("cal_inspect_raw_sub", { sensor: sensorLabel }),
      value: `${tile.total.toLocaleString(lang === "id" ? "id-ID" : "en-US")} MW`,
      notes,
    });
  };

  const calFilterDesc = view === "yearly"
    ? t("cal_filter_desc_yearly", { months: monthSel === "all" ? t("cal_filter_all_months") : t("cal_filter_month_only", { month: monthNames[Number(monthSel) - 1] }) })
    : t("cal_filter_desc_monthly", { years: yearSel === "all" ? t("cal_filter_all_years") : t("cal_filter_year_only", { year: yearSel }) });

  const goMapWithFilter = () => {
    setCalFilter(calFilterDesc);
    goMap();
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
        <div style={{ maxWidth: 640 }}>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            {t("cal_chip_temporal")}
          </span>
          <h1>{t("cal_heading")}</h1>
          <p className="sub">
            {t("cal_lead_desc", { period: view === "yearly" ? t("cal_period_year") : t("cal_period_month") })}
          </p>
          <button
            className="btn secondary"
            style={{ marginTop: 12, padding: "7px 15px", fontSize: 12.5 }}
            onClick={goMapWithFilter}
            title={t("cal_btn_view_map", { filter: calFilterDesc })}
          >
            {t("cal_btn_view_map", { filter: calFilterDesc })}
          </button>
        </div>
      </div>

      <div className="calendar-controls">
        <div className="calendar-filter-control">
          <SearchableRegionSelect
            value={aoi}
            onChange={(newAoi) => { setAoi(newAoi); setSel(null); }}
            presets={presets}
            lang={lang}
            label={t("cal_label_region")}
          />
        </div>

        <div className="calendar-filter-control">
          <span className="calendar-filter-label" id="calendar-sensor-label">{t("cal_label_sensor")}</span>
          <div className="calendar-segmented calendar-segmented-sensor" role="group" aria-labelledby="calendar-sensor-label">
            {([
              { value: "harm", label: t("cal_sensor_short_harm"), description: t("cal_sensor_opt_harm") },
              { value: "modis", label: t("cal_sensor_short_modis"), description: t("cal_sensor_opt_modis") },
              { value: "viirs", label: t("cal_sensor_short_viirs"), description: t("cal_sensor_opt_viirs") },
            ] satisfies { value: CalendarSensor; label: string; description: string }[]).map(option => (
              <button
                key={option.value}
                type="button"
                className={sensor === option.value ? "active" : ""}
                aria-pressed={sensor === option.value}
                aria-label={option.description}
                title={option.description}
                onClick={() => { setSensor(option.value); setSel(null); }}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="calendar-filter-control">
          <span className="calendar-filter-label" id="calendar-view-label">{t("cal_label_view")}</span>
          <div className="calendar-segmented" role="group" aria-labelledby="calendar-view-label">
            <button
              type="button"
              className={view === "yearly" ? "active" : ""}
              aria-pressed={view === "yearly"}
              onClick={() => { setView("yearly"); setSel(null); }}
            >
              {t("cal_view_short_yearly")}
            </button>
            <button
              type="button"
              className={view === "monthly" ? "active" : ""}
              aria-pressed={view === "monthly"}
              onClick={() => { setView("monthly"); setSel(null); }}
            >
              {t("cal_view_short_monthly")}
            </button>
          </div>
        </div>

        {view === "monthly" ? (
          <label className="calendar-filter-control">
            <span className="calendar-filter-label">{t("cal_year_choice")}</span>
            <select
              className="glass-select"
              value={yearSel}
              aria-label={t("cal_year_choice")}
              onChange={e => { setYearSel(e.target.value); setSel(null); }}
            >
              <option value="all">{t("cal_all_years")}</option>
              {yearsAll.map(y => (
                <option key={y.year} value={String(y.year)}>{t("cal_year_opt", { year: y.year })}</option>
              ))}
            </select>
          </label>
        ) : (
          <label className="calendar-filter-control">
            <span className="calendar-filter-label">{t("cal_month_choice")}</span>
            <select
              className="glass-select"
              value={monthSel}
              aria-label={t("cal_month_choice")}
              onChange={e => { setMonthSel(e.target.value); setSel(null); }}
            >
              <option value="all">{t("cal_all_months")}</option>
              {monthNames.map((m, i) => (
                <option key={m} value={String(i + 1).padStart(2, "0")}>{t("cal_month_opt", { month: m })}</option>
              ))}
            </select>
          </label>
        )}

        <div className="calendar-filter-summary" aria-live="polite">
          {calFilterDesc}
        </div>
      </div>

      {sensor !== "harm" && cal && (
        <div className="boundary" style={{ marginTop: 18 }}>
          <b>{t("cal_sensor_boundary_title", { sensor: sensor === "modis" ? "MODIS" : "VIIRS" })}</b>
          <p className="sub" style={{ marginTop: 2 }}>
            {t("cal_sensor_boundary_body")}
          </p>
        </div>
      )}

      {loading && (
        <div className="status-panel loading" style={{ marginTop: 20 }}>
          <div className="status-title">{t("cal_loading_title")}</div>
          <p className="status-desc">{t("cal_loading_desc")}</p>
          <div className="skel" style={{ height: 28, marginTop: 8 }} />
        </div>
      )}

      {err && (
        <div className="status-panel failed" style={{ marginTop: 20, padding: "18px 22px", borderRadius: 12 }}>
          <div className="status-title" style={{ fontSize: 16, fontWeight: 700 }}>
            {t("err_not_available")}
          </div>
          <p className="status-desc" style={{ marginTop: 6, fontSize: 13.5, color: "var(--ink2)", lineHeight: 1.6 }}>
            {t("err_not_available_desc")}{" "}{t("cal_choose_ready")}
          </p>
          {readyPresets.length > 0 && (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 14 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)" }}>{t("cal_ready_regions")}</span>
              {readyPresets.map(p => (
                <button
                  key={p.id}
                  className="btn secondary"
                  style={{ padding: "6px 14px", fontSize: 12.5, borderRadius: 8, fontWeight: 600 }}
                  onClick={() => setAoi(p.id)}
                >
                  {t("cal_open_region")} {PRESET_NAMES[lang]?.[p.id] ?? p.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!loading && !err && cal && yearsAll.length === 0 && (
        <div className="status-panel failed" style={{ marginTop: 20, padding: "18px 22px", borderRadius: 12 }}>
          <div className="status-title" style={{ fontSize: 16, fontWeight: 700 }}>
            {lang === "id" ? "Dukungan Data Kalender Belum Tersedia (Gerbang F-9b)" : "Calendar Telemetry Unavailable (F-9b Gate)"}
          </div>
          <p className="status-desc" style={{ marginTop: 6, fontSize: 13.5, color: "var(--ink2)", lineHeight: 1.6 }}>
            {lang === "id"
              ? "Wilayah ini tidak memiliki jumlah hari sinyal yang mencukupi selama era pelatihan untuk membangun kurva klimatologi multi-tahun yang stabil. Sesuai aturan kejujuran kontrak ilmiah (Rule E-03 / DEC-2), data tidak direkayasa atau diinterpolasi secara semu."
              : "This region has insufficient signal days during the training era to establish a stable multi-year climatology curve. Per scientific contract honesty (Rule E-03 / DEC-2), observations are strictly not fabricated or artificially interpolated."}
          </p>
          {readyPresets.length > 0 && (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 14 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink)" }}>{t("cal_ready_regions")}</span>
              {readyPresets.map(p => (
                <button
                  key={p.id}
                  className="btn secondary"
                  style={{ padding: "6px 14px", fontSize: 12.5, borderRadius: 8, fontWeight: 600 }}
                  onClick={() => setAoi(p.id)}
                >
                  {t("cal_open_region")} {PRESET_NAMES[lang]?.[p.id] ?? p.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!loading && !err && cal && yearsAll.length > 0 && (
        <div className="grid2" style={{ marginTop: 18, gridTemplateColumns: "3fr 2fr" }}>
          <div className="card">
            {summary && (
              <div className="cal-summary">
                <span className="big">{summary.total.toLocaleString(lang === "id" ? "id-ID" : "en-US")}</span>
                <span className="unit">{summary.valueLabel}</span>
                <span className="stat">
                  {t("cal_peak_label", { unit: summary.peakUnit })} <b>{summary.peak.label}</b> ({summary.peak.total.toLocaleString(lang === "id" ? "id-ID" : "en-US")} MW)
                </span>
                <span className="stat">
                  <b>{summary.active}</b> {summary.unit}
                </span>
                <span className="stat">
                  <b>{t("cal_gap_days_stat", { count: summary.gaps })}</b>
                </span>
              </div>
            )}

            <div className="tiles">
              {tiles.map(tile => {
                const isSelected = sel?.key === tile.key;
                return (
                  <button
                    key={tile.key}
                    className={"tile" + (tile.isGap ? " gap" : "") + (isSelected ? " selected" : "") + (tile.isPeak ? " peak" : "")}
                    data-tier={tile.tier}
                    onClick={() => onTile(tile)}
                    aria-label={`${lang === "id" ? "Pemeriksaan" : "Inspect"} ${tile.label}: ${
                      tile.isGap
                        ? t("cal_tile_gap_text")
                        : `${tile.total.toLocaleString(lang === "id" ? "id-ID" : "en-US")} MW FRP`
                    }`}
                  >
                    <span className="tile-label">{tile.label}</span>
                    <span className="tile-value">
                      {tile.isGap
                        ? t("cal_tile_gap_text")
                        : `${tile.total.toLocaleString(lang === "id" ? "id-ID" : "en-US")} MW`}
                    </span>
                    {tile.gapDays > 0 && !tile.isGap && (
                      <span className="tile-flags">
                        {t("cal_tile_gap_sub", { count: tile.gapDays })}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="legend-row">
              <span className="item">
                <span className="ramp">
                  {[0, 1, 2, 3, 4, 5].map(tier => (
                    <i key={tier} data-tier={tier} />
                  ))}
                </span>
                <span>{t("cal_legend_gradient")}</span>
              </span>
              <span className="item">
                <i className="sw-gap" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>{t("cal_legend_gap")}</span>
              </span>
              <span className="item">
                <i className="sw-zero" style={{ width: 14, height: 14, borderRadius: 3 }} />
                <span>{t("cal_legend_zero")}</span>
              </span>
            </div>
          </div>

          <div className="card">
            <h2>
              {t("cal_inspection_title", { period: view === "yearly" ? t("cal_inspect_year_unit") : t("cal_inspect_month_unit") })}
            </h2>
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
                    <span className="kpi-label">{t("cal_kpi_label")}</span>
                    <span className="kpi-val">{sel.value}</span>
                    <span className="kpi-sub">
                      {sensor === "harm" ? t("cal_kpi_harm_sub") : t("cal_kpi_raw_sub")}
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
                  <div className="status-title">{t("cal_no_period")}</div>
                  <p className="status-desc">
                    {t("cal_no_period_desc", { period: view === "yearly" ? t("cal_period_year") : t("cal_period_month") })}
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
