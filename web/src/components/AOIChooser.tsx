import { useEffect, useState } from "react";
import { api, Preset } from "../api";
import { useAoi } from "../App";
import type { BBox } from "./AoiMap";

type Job = { job_id: string; status: string; progress_pct?: number; stage?: string; error?: { message: string } };

/** Area selection WITHOUT the map: preset cards + BboxForm + Analyze (FR-UI-1 keyboard path).
 *  Map drawing lives on the Fire Map screen. */
export default function AOIChooser() {
  const { aoi, setAoi, series } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);
  const [bbox, setBbox] = useState<BBox>({ west: 100.8, south: -1.9, east: 103.4, north: 0.2 });
  const [job, setJob] = useState<Job | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.presets().then(r => setPresets(r.presets)).catch(e => setErr(e.message)); }, []);

  const selectPreset = (p: Preset) => {
    setAoi(p.id);
    setBbox({ west: p.west, south: p.south, east: p.east, north: p.north });
  };

  const runAnalysis = async () => {
    setErr(null);
    try {
      const j = await api.analyze(bbox);
      setJob({ job_id: j.job_id, status: j.status } as Job);
      const poll = setInterval(async () => {
        const st = await api.job(j.job_id);
        setJob(st);
        if (!["queued", "running"].includes(st.status)) clearInterval(poll);
      }, 1200);
    } catch (e: any) { setErr(e.message); }
  };

  const dLon = bbox.east - bbox.west, dLat = bbox.north - bbox.south;
  const tooBig = dLon > 5 || dLat > 5;

  const fields: [string, number, (v: number) => void][] = [
    ["West °E", bbox.west, v => setBbox(b => ({ ...b, west: v }))],
    ["South °N", bbox.south, v => setBbox(b => ({ ...b, south: v }))],
    ["East °E", bbox.east, v => setBbox(b => ({ ...b, east: v }))],
    ["North °N", bbox.north, v => setBbox(b => ({ ...b, north: v }))],
  ];

  return (
    <div>
      <div className="card">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <h2 style={{ fontSize: 15, marginBottom: 10 }}>Presets</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {presets.map(p => (
                <button key={p.id} onClick={() => selectPreset(p)} aria-pressed={p.id === aoi}
                  style={{ textAlign: "left", borderRadius: 8, padding: "12px 14px", cursor: "pointer",
                    border: p.id === aoi ? "1.5px solid var(--ember)" : "1px solid var(--line)",
                    background: p.id === aoi ? "var(--ember-sub)" : "var(--surface)", color: "inherit",
                    transition: "border-color 150ms ease, background 150ms ease" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</span>
                    <span className={"state-chip " + (p.artifact_status === "available" ? "chip-ok" : "chip-neutral")}>
                      {p.artifact_status === "available" ? "Available" : "Pending build"}
                    </span>
                  </div>
                  <div className="mono" style={{ fontSize: 10, color: "var(--ink3)", marginTop: 4 }}>
                    {p.west}°, {p.south}° → {p.east}°, {p.north}°
                  </div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <h2 style={{ fontSize: 15, marginBottom: 10 }}>Custom bounding box</h2>
            <p className="sub" style={{ marginTop: 0, fontSize: 12 }}>Type coordinates directly — fully keyboard-friendly, equal to drawing on the map. Limit 5° × 5°.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8, marginTop: 10 }}>
              {fields.map(([l, v, set]) => (
                <label key={l}>
                  <span style={{ fontSize: 11, color: "var(--ink2)" }}>{l}</span>
                  <input style={{ width: "100%", marginTop: 4 }} inputMode="decimal"
                    value={v} onChange={ev => set(parseFloat(ev.target.value) || 0)} />
                </label>
              ))}
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: tooBig ? "var(--ember)" : "var(--ok)" }}>
              {tooBig ? `${dLon.toFixed(1)}° × ${dLat.toFixed(1)}° — exceeds the 5° × 5° limit.` : `✓ Area ${dLon.toFixed(1)}° × ${dLat.toFixed(1)}° — within limit`}
            </div>
            <button className="btn" style={{ marginTop: 14 }}
              onClick={runAnalysis} disabled={!!job && ["queued", "running"].includes(job.status)}>
              Run analysis
            </button>
          </div>
        </div>
        {job && <div style={{ marginTop: 14, borderTop: "1px solid var(--line)", paddingTop: 12 }}>
          <span className={"state-chip " + (job.status === "complete" ? "chip-ok" : job.status === "queued" || job.status === "running" ? "chip-neutral" : "chip-fail")}>
            {job.status}
          </span>
          <span className="mono" style={{ fontSize: 11, color: "var(--ink2)", marginLeft: 10 }}>{job.job_id}</span>
          {job.status === "running" && <div className="skel" style={{ height: 28, marginTop: 10 }} />}
          {job.error && <p className="sub" style={{ color: "var(--ember)", marginTop: 8 }}>{job.error.message}</p>}
          {err && <p className="sub" style={{ color: "var(--ember)", marginTop: 8 }}>{err}</p>}
        </div>}
        {series && <p className="sub mono" style={{ fontSize: 11, marginTop: 10 }}>n_days={series.n_days} · {series.fixture ?? "real artifacts"} · {series.model_version}</p>}
      </div>
    </div>
  );
}
