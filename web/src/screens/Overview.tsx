import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Preset } from "../api";
import { useAoi } from "../App";

export default function Overview({ goCalendar }: { goCalendar: () => void }) {
  const { aoi, series } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);
  useEffect(() => { api.presets().then(r => setPresets(r.presets)).catch(() => {}); }, []);

  const preset = presets.find(p => p.id === aoi);
  const targetLabel = preset ? preset.name : `${aoi} (custom bbox)`;
  const span = series && series.days.length
    ? `${series.days[0].date.slice(0, 4)}–${series.days[series.days.length - 1].date.slice(0, 4)}`
    : null;
  const status = preset ? (preset.artifact_status === "available" ? "data ready" : "pending build") : null;

  return (
    <div style={{ textAlign: "center", padding: "72px 16px 64px" }}>
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(44px, 6vw, 84px)", fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.02em", color: "var(--ink)" }}>
        See a fire record that no longer jumps when the satellite changes
      </h1>
      <motion.button onClick={goCalendar}
        whileHover={{ scale: 1.04, backgroundColor: "#DFDCD6" }}
        whileTap={{ scale: 0.96 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        style={{ marginTop: 48, padding: "30px 72px", fontSize: 42, fontWeight: 800, fontFamily: "var(--font-display)",
          background: "#E7E5E1",
          color: "var(--ink)", border: "1px solid var(--line)",
          borderRadius: 16, cursor: "pointer", letterSpacing: "-0.01em" }}>
        Explore the calendar →
      </motion.button>
      <p className="sub mono" style={{ marginTop: 16, fontSize: 12 }}>
        Opens: {targetLabel}{span ? ` · ${span}` : ""}{status ? ` · ${status}` : ""}
      </p>
      <p className="sub" style={{ marginTop: 20 }}>
        Honest hotspot history — MODIS &amp; VIIRS harmonized, with uncertainty, gaps flagged, never predicted.
      </p>
    </div>
  );
}
