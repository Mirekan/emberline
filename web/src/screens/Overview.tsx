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
  const status = preset ? (preset.artifact_status === "available" ? "data ready" : "pending build") : null;

  return (
    <div style={{ textAlign: "center", padding: "72px 16px 64px", maxWidth: 1200, margin: "0 auto" }}>
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(38px, 5.5vw, 76px)",
          fontWeight: 800,
          lineHeight: 1.08,
          letterSpacing: "-0.025em",
          color: "var(--ink)",
          maxWidth: 960,
          margin: "0 auto",
        }}
      >
        See when fire activity rises—and where the record has gaps
      </h1>

      <p style={{ margin: "22px auto 0", fontSize: 16, color: "var(--ink2)", maxWidth: 680, lineHeight: 1.6 }}>
        Fire activity can change with the season, while satellite coverage can leave gaps in the record. This view brings those observations together so you can see when detections rise, compare patterns across the year, and keep the limits of the data in view.
      </p>

      <motion.button
        onClick={goCalendar}
        whileHover={{ scale: 1.03, backgroundColor: "var(--sunken)" }}
        whileTap={{ scale: 0.97 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        style={{
          marginTop: 30,
          padding: "18px 38px",
          fontSize: "clamp(18px, 2vw, 24px)",
          fontWeight: 800,
          fontFamily: "var(--font-display)",
          background: "var(--sunken)",
          color: "var(--ink)",
          border: "1px solid var(--line-strong)",
          borderRadius: 16,
          cursor: "pointer",
          letterSpacing: "-0.01em",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        Explore the calendar →
      </motion.button>

      <p className="mono" style={{ marginTop: 28, fontSize: 13, color: "var(--ink2)" }}>
        Opens: {targetLabel}{span ? ` · ${span}` : ""}{status ? ` · ${status}` : ""}
      </p>

      <p style={{ marginTop: 14, fontSize: 13, color: "var(--ink3)", maxWidth: 640, margin: "14px auto 0", lineHeight: 1.5 }}>
        MODIS &amp; VIIRS observations, harmonized with uncertainty and data gaps flagged. Historical context, never a prediction.
      </p>
    </div>
  );
}
