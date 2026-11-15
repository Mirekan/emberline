import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Preset } from "../api";
import { useAoi } from "../App";
import ScrollyActs, { RiskGaugeCard } from "../components/ScrollyActs";

export default function Overview({ goCalendar, goMethod }: { goCalendar: () => void; goMethod: () => void }) {
  const { aoi, series } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);
  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  const preset = presets.find(p => p.id === aoi);
  const targetLabel = preset ? preset.name : `${aoi} (custom bbox)`;
  const span = series && series.days.length
    ? `${series.days[0].date.slice(0, 4)}–${series.days[series.days.length - 1].date.slice(0, 4)}`
    : null;
  const status = preset ? (preset.artifact_status === "available" ? "data siap" : "dalam antrean") : null;

  return (
    <div className="overview-page">
      <section className="overview-hero" aria-labelledby="overview-title">
        <div className="overview-hero-copy">
          <p className="overview-eyebrow"><i /> EMBERLINE · MISSION CONTROL</p>
          <h1 id="overview-title">
            Membaca jejak api.
            <br />
            <span>Memahami pola bumi.</span>
          </h1>
          <p className="overview-description">
            Eksplorasi observasi kebakaran MODIS dan VIIRS—disajikan sebagai rekam historis yang transparan, lengkap dengan ketidakpastian dan celah data.
          </p>
          <div className="overview-actions">
            <button className="btn" onClick={goCalendar}>Jelajahi kalender <span aria-hidden="true">↗</span></button>
            <button className="btn secondary" onClick={goMethod}>Lihat metodologi</button>
          </div>
          <span className="overview-scroll-cue">Gulir untuk mengikuti perjalanan data <span aria-hidden="true">↓</span></span>
        </div>
        <RiskGaugeCard />
        <div className="overview-stats" aria-label="Ringkasan cakupan observasi">
          <div><strong>38</strong><span>provinsi · konsep demo</span></div>
          <div><strong>{series?.days.length.toLocaleString("id-ID") ?? "—"}</strong><span>observasi pada area terpilih</span></div>
          <div><strong>{span ?? "MODIS + VIIRS"}</strong><span>rekam satelit historis</span></div>
        </div>
      </section>

      <ScrollyActs />

      <section className="overview-details" aria-label="Tentang rekam observasi EmberLine">
        <div className="overview-copy">
          <p className="overview-eyebrow">Jelajahi data</p>
          <h2>Kenali pola, pahami batas datanya.</h2>
          <p className="overview-description">
            Aktivitas kebakaran berubah mengikuti musim, sementara cakupan satelit dapat meninggalkan celah pengamatan. Kalender menyatukan observasi agar Anda dapat membandingkan pola antarwaktu tanpa mengaburkan keterbatasan data.
          </p>
          <p className="mono overview-meta">
            Wilayah: {targetLabel}{span ? ` · ${span}` : ""}{status ? ` · ${status}` : ""}
          </p>
          <p className="overview-disclosure">
            Observasi MODIS &amp; VIIRS yang diharmonisasi, dengan ketidakpastian dan celah data ditandai. Konteks historis, bukan prediksi.
          </p>
        </div>

        <motion.button
          className="overview-cta"
          onClick={goCalendar}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        >
          Jelajahi kalender →
        </motion.button>
        <button className="overview-method-link" onClick={goMethod}>Baca metodologi EmberLine →</button>
      </section>
    </div>
  );
}
