import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Preset } from "../api";
import { useAoi } from "../App";
import ScrollyActs from "../components/ScrollyActs";

export default function Overview({ goCalendar, goMethod }: { goCalendar: () => void; goMethod: () => void }) {
  const { aoi, series, lang, t } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);
  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  const preset = presets.find(p => p.id === aoi);
  const targetLabel = preset ? preset.name : `${aoi} (custom bbox)`;
  const span = series && series.days.length
    ? `${series.days[0].date.slice(0, 4)}–${series.days[series.days.length - 1].date.slice(0, 4)}`
    : null;
  const status = preset ? (preset.artifact_status === "available" ? t("overview_data_ready") : t("overview_queued")) : null;

  return (
    <div className="overview-page">
      <section className="overview-hero" aria-labelledby="overview-title">
        <div className="overview-hero-copy">
          <p className="overview-eyebrow"><i /> {t("overview_eyebrow")}</p>
          <h1 id="overview-title">
            {t("overview_title_1")}
            <br />
            <span>{t("overview_title_2")}</span>
          </h1>
          <p className="overview-description">
            {t("overview_desc")}
          </p>
          <div className="overview-actions">
            <button className="btn" onClick={goCalendar}>{t("overview_btn_calendar")} <span aria-hidden="true">↗</span></button>
            <button className="btn secondary" onClick={goMethod}>{t("overview_btn_method")}</button>
          </div>
          <span className="overview-scroll-cue">{t("overview_scroll_cue")} <span aria-hidden="true">↓</span></span>
        </div>
        <div className="overview-stats" aria-label={lang === "id" ? "Ringkasan cakupan observasi" : "Observation coverage summary"}>
          <div><strong>38</strong><span>{t("overview_stat_provinces")}</span></div>
          <div><strong>{series?.days.length.toLocaleString(lang === "id" ? "id-ID" : "en-US") ?? "—"}</strong><span>{t("overview_stat_obs")}</span></div>
          <div><strong>{span ?? "MODIS + VIIRS"}</strong><span>{t("overview_stat_history")}</span></div>
        </div>
      </section>

      <ScrollyActs />

      <section className="overview-details" aria-label={lang === "id" ? "Tentang rekam observasi EmberLine" : "About EmberLine observation records"}>
        <div className="overview-copy">
          <p className="overview-eyebrow">{t("overview_details_eyebrow")}</p>
          <h2>{t("overview_details_heading")}</h2>
          <p className="overview-description">
            {t("overview_details_desc")}
          </p>
          <p className="mono overview-meta">
            {t("overview_region")}: {targetLabel}{span ? ` · ${span}` : ""}{status ? ` · ${status}` : ""}
          </p>
          <p className="overview-disclosure">
            {lang === "id"
              ? "Observasi MODIS & VIIRS yang diharmonisasi, dengan ketidakpastian dan celah data ditandai. Konteks historis, bukan prediksi."
              : "Harmonized MODIS & VIIRS observations, with flagged uncertainty intervals and retrieval gaps. Historical context, not prediction."}
          </p>
        </div>

        <motion.button
          className="overview-cta"
          onClick={goCalendar}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        >
          {t("overview_btn_calendar")} →
        </motion.button>
        <button className="overview-method-link" onClick={goMethod}>
          {lang === "id" ? "Baca metodologi EmberLine →" : "Read EmberLine methodology →"}
        </button>
      </section>
    </div>
  );
}
