import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Preset } from "../api";
import { useAoi } from "../App";

export default function Overview({ goCalendar }: { goCalendar: () => void }) {
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
        <h1 id="overview-title">
          See when fire activity rises—and where the record has gaps
        </h1>
        <span className="overview-scroll-cue" aria-hidden="true">Scroll to learn more ↓</span>
      </section>

      <section className="overview-details" aria-label="About the fire record">
        <div className="overview-copy">
          <p className="overview-eyebrow">Why this record matters</p>
          <h2>Make sense of the pattern, and its limits.</h2>
          <p className="overview-description">
            Fire activity can change with the season, while satellite coverage can leave gaps in the record. The calendar brings those observations together so you can see when detections rise, compare patterns across the year, and keep the limits of the data in view.
          </p>
          <p className="mono overview-meta">
            Wilayah: {targetLabel}{span ? ` · ${span}` : ""}{status ? ` · ${status}` : ""}
          </p>
          <p className="overview-disclosure">
            MODIS &amp; VIIRS observations, harmonized with uncertainty and data gaps flagged. Historical context, never a prediction.
          </p>
        </div>

        <motion.button
          className="overview-cta"
          onClick={goCalendar}
          whileHover={{ scale: 1.03, backgroundColor: "var(--sunken)" }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        >
          Explore the calendar →
        </motion.button>
      </section>
    </div>
  );
}
