import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api, Preset } from "../api";
import { useAoi } from "../App";

// Region list from the user's Figma frame (Search sidebar). Centers = province
// centroids for flyTo; `preset` links a region to a real analyzable AOI.
const REGIONS: { name: string; center: [number, number]; preset?: string }[] = [
  { name: "Aceh", center: [4.6, 96.7] },
  { name: "Sumatera Utara", center: [2.2, 98.7] },
  { name: "Riau", center: [0.5, 102.3], preset: "riau" },
  { name: "Kepulauan Riau", center: [0.9, 104.5] },
  { name: "Jambi", center: [-1.8, 103.0], preset: "jambi" },
  { name: "Sumatera Selatan", center: [-3.3, 104.6], preset: "south_sumatra" },
  { name: "Bangka Belitung", center: [-2.5, 106.0] },
  { name: "Kalimantan Barat", center: [0.2, 109.5] },
  { name: "Kalimantan Tengah", center: [-2.2, 113.5], preset: "central_kalimantan" },
  { name: "Kalimantan Selatan", center: [-3.0, 115.5] },
  { name: "Kalimantan Timur", center: [0.5, 116.5] },
  { name: "Kalimantan Utara", center: [2.5, 116.8] },
  { name: "Sulawesi Utara", center: [0.9, 124.2] },
  { name: "Gorontalo", center: [0.6, 122.4] },
  { name: "Sulawesi Tengah", center: [-1.4, 120.4] },
  { name: "Sulawesi Selatan", center: [-3.8, 119.9] },
  { name: "Maluku Utara", center: [1.6, 127.6] },
  { name: "Papua", center: [-4.0, 138.5] },
  { name: "Papua Selatan", center: [-6.5, 138.8] },
];

export default function FireMap() {
  const { aoi, setAoi, calFilter } = useAoi();
  const mapEl = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const [q, setQ] = useState("");
  const [selName, setSelName] = useState<string | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => { api.presets().then(r => setPresets(r.presets)).catch(() => {}); }, []);

  useEffect(() => {
    if (!mapEl.current || mapRef.current) return;
    const map = L.map(mapEl.current, {
      zoomControl: false,
      attributionControl: true,
      minZoom: 4, maxZoom: 11,
    });
    L.control.zoom({ position: "topright" }).addTo(map);
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      { attribution: "Esri, HERE, Garmin, OpenStreetMap contributors", maxZoom: 11 }
    ).addTo(map);
    map.fitBounds([[6.5, 94.5], [-11.5, 141.5]]);
    mapRef.current = map;
    const onResize = () => map.invalidateSize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); map.remove(); mapRef.current = null; };
  }, []);

  const flyTo = (r: (typeof REGIONS)[number]) => {
    setSelName(r.name); // instant visual feedback even for non-preset regions
    mapRef.current?.flyTo(r.center, 8, { duration: 0.9 });
    if (r.preset) setAoi(r.preset);
  };

  // Arriving from the calendar (or any AOI change): fly to the active AOI's exact bbox
  const flownRef = useRef<string | null>(null);
  useEffect(() => {
    const p = presets.find(pp => pp.id === aoi);
    if (p && mapRef.current && flownRef.current !== aoi) {
      flownRef.current = aoi;
      mapRef.current.flyToBounds([[p.south, p.west], [p.north, p.east]], { padding: [48, 48], duration: 1.1 });
    }
  }, [aoi, presets]);

  const list = REGIONS.filter(r => r.name.toLowerCase().includes(q.toLowerCase()));
  const chipFor = (r: (typeof REGIONS)[number]) => {
    const p = presets.find(pp => pp.id === r.preset);
    if (!p) return null;
    return p.artifact_status === "available" ? "DATA READY" : "PENDING";
  };
  const curPreset = presets.find(p => p.id === aoi);

  return (
    <div style={{ position: "relative", height: "calc(100vh - 112px)", minHeight: 520 }}>
      <div ref={mapEl} style={{ position: "absolute", inset: 0 }} />

      {/* Sidebar — Search + region list (matches Figma frame) */}
      <div style={{ position: "absolute", left: 16, top: 16, bottom: 16, width: 300,
        background: "var(--surface)", borderRadius: 12, border: "1px solid var(--line)",
        boxShadow: "0 4px 16px rgba(0,0,0,0.18)", display: "flex", flexDirection: "column", zIndex: 900 }}>
        <div style={{ padding: 14 }}>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search"
            style={{ width: "100%", borderRadius: 999, padding: "8px 16px" }} />
        </div>
        {calFilter && (
          <div style={{ margin: "0 14px 8px", fontSize: 11, color: "var(--ember)",
            background: "var(--ember-sub)", border: "1px solid rgba(154,52,18,0.35)",
            borderRadius: 8, padding: "6px 10px" }}>
            Calendar scope: <b>{calFilter}</b>
          </div>
        )}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px 8px" }}>
          {list.map(r => {
            const chip = chipFor(r);
            const active = r.name === selName; // single source of truth: last clicked — never two at once
            return (
              <button key={r.name} className={"region-item" + (active ? " active" : "")}
                onClick={() => flyTo(r)}>
                <span>{r.name}</span>
                {chip && <span className={"chip " + (chip === "DATA READY" ? "ready" : "pending")}>{chip}</span>}
              </button>
            );
          })}
          {list.length === 0 && <p style={{ padding: "8px 12px", fontSize: 12, color: "var(--ink3)" }}>No region matches “{q}”.</p>}
          <p style={{ padding: "10px 12px", fontSize: 10, color: "var(--ink3)" }}>
            + 20 more provinces · regions with a colored chip have analyzable AOI artifacts
          </p>
        </div>
        <div style={{ borderTop: "1px solid var(--line)", padding: "10px 14px", fontSize: 10, color: "var(--ink3)" }}>
          Active AOI: <span style={{ color: "var(--ink)", fontWeight: 600 }}>
            {curPreset ? curPreset.name : `${aoi} (custom bbox)`}
          </span>
          {curPreset && <span> · {curPreset.artifact_status === "available" ? "DATA READY" : "PENDING BUILD"}</span>}
          <div style={{ marginTop: 4 }}>Gridded FIRMS layer = O-02 backlog preview · dots layer belum aktif</div>
        </div>
      </div>

      {/* Backlog chip — honest status */}
      <span className="state-chip chip-neutral" style={{ position: "absolute", right: 16, bottom: 16, zIndex: 900,
        background: "var(--surface)" }}>
        OPTIONAL – BACKLOG (P1 · needs approval A) — O-02 preview
      </span>
    </div>
  );
}
