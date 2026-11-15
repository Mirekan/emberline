import { useEffect, useState } from "react";
import { api, Preset } from "../api";
import { useAoi } from "../App";
import type { BBox } from "./AoiMap";

type Job = { job_id: string; status: string; progress_pct?: number; stage?: string; error?: { message: string } };

/** Area selection WITHOUT the map: preset cards + BboxForm + Analyze (FR-UI-1 keyboard path).
 *  Map drawing lives on the Fire Map screen. */
export default function AOIChooser() {
  const { aoi, setAoi } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);
  const [bbox, setBbox] = useState<BBox>({ west: 100.8, south: -1.9, east: 103.4, north: 0.2 });
  const [job, setJob] = useState<Job | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(e => setErr(e.message));
  }, []);

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
    } catch (e: any) {
      setErr(e.message);
    }
  };

  const dLon = bbox.east - bbox.west;
  const dLat = bbox.north - bbox.south;
  const tooBig = dLon > 5 || dLat > 5;
  const invalidSpan = dLon <= 0 || dLat <= 0;

  const fields: [string, number, (v: number) => void][] = [
    ["West longitude (°E)", bbox.west, v => setBbox(b => ({ ...b, west: v }))],
    ["South latitude (°N/°S)", bbox.south, v => setBbox(b => ({ ...b, south: v }))],
    ["East longitude (°E)", bbox.east, v => setBbox(b => ({ ...b, east: v }))],
    ["North latitude (°N/°S)", bbox.north, v => setBbox(b => ({ ...b, north: v }))],
  ];

  return (
    <div>
      <div className="card">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div>
            <h2>Pilihan Wilayah Standar</h2>
            <p className="sub" style={{ fontSize: 12, marginBottom: 12 }}>
              Basis data pengamatan satelit historis yang telah tervalidasi.
            </p>
            <div style={{ display: "grid", gap: 8 }}>
              {presets.map(p => {
                const isSelected = p.id === aoi;
                return (
                  <button
                    key={p.id}
                    onClick={() => selectPreset(p)}
                    aria-pressed={isSelected}
                    style={{
                      textAlign: "left",
                      borderRadius: 8,
                      padding: "10px 12px",
                      cursor: "pointer",
                      border: isSelected ? "2px solid var(--ember)" : "1px solid var(--line)",
                      background: isSelected ? "var(--ember-sub)" : "var(--surface)",
                      color: "inherit",
                      transition: "all 140ms ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                      <span style={{ fontSize: 13.5, fontWeight: 600 }}>{p.name}</span>
                      <span className={"state-chip " + (p.artifact_status === "available" ? "chip-ok" : "chip-neutral")}>
                        {p.artifact_status === "available" ? "Data Siap" : "Dalam Antrean"}
                      </span>
                    </div>
                    <div className="mono" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 4 }}>
                      [{p.west.toFixed(1)}°E, {p.south.toFixed(1)}°N] → [{p.east.toFixed(1)}°E, {p.north.toFixed(1)}°N]
                    </div>
                  </button>
                );
              })}
              {presets.length === 0 && !err && (
                <div className="status-panel loading">
                  <div className="status-title">Memuat daftar wilayah…</div>
                </div>
              )}
            </div>
          </div>

          <div>
            <h2>Custom bounding box coordinates</h2>
            <p className="sub" style={{ fontSize: 12, marginBottom: 12 }}>
              Define coordinates manually for accessible, keyboard-first area of interest selection. Maximum scope is 5.0° × 5.0°.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
              {fields.map(([label, val, setVal]) => (
                <label key={label} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span>{label}</span>
                  <input
                    type="number"
                    step="0.1"
                    inputMode="decimal"
                    value={val}
                    onChange={ev => setVal(parseFloat(ev.target.value) || 0)}
                  />
                </label>
              ))}
            </div>

            <div
              style={{
                marginTop: 10,
                fontSize: 12,
                fontWeight: 500,
                color: tooBig || invalidSpan ? "var(--ember)" : "var(--ok)",
              }}
            >
              {invalidSpan
                ? "Invalid coordinate bounds: East must exceed West, North must exceed South."
                : tooBig
                ? `Extent ${dLon.toFixed(2)}° × ${dLat.toFixed(2)}° — exceeds maximum allowed 5.0° × 5.0° aperture.`
                : `✓ Area aperture ${dLon.toFixed(2)}° × ${dLat.toFixed(2)}° — within 5.0° limit.`}
            </div>

            <button
              className="btn"
              style={{ marginTop: 14 }}
              onClick={runAnalysis}
              disabled={tooBig || invalidSpan || (!!job && ["queued", "running"].includes(job.status))}
            >
              {job && ["queued", "running"].includes(job.status)
                ? "Executing analysis pipeline…"
                : "Analyze bounding box coordinates"}
            </button>
          </div>
        </div>

        {err && (
          <div className="status-panel failed" style={{ marginTop: 16 }}>
            <div className="status-title">Preset query failed</div>
            <p className="status-desc">{err}</p>
          </div>
        )}

        {job && (
          <div style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span
                className={
                  "state-chip " +
                  (job.status === "complete"
                    ? "chip-ok"
                    : job.status === "failed"
                    ? "chip-fail"
                    : "chip-warn")
                }
              >
                {job.status === "queued" && "Queued in pipeline"}
                {job.status === "running" && "Harmonizing satellite granules…"}
                {job.status === "complete" && "Analysis complete"}
                {job.status === "failed" && "Execution failed"}
              </span>
              <span className="mono" style={{ fontSize: 11, color: "var(--ink2)" }}>
                Job ID: {job.job_id}
              </span>
              {job.progress_pct != null && (
                <span className="mono" style={{ fontSize: 11, color: "var(--ink2)" }}>
                  {job.progress_pct}%
                </span>
              )}
            </div>

            {job.status === "running" && <div className="skel" style={{ height: 16, marginTop: 10, borderRadius: 4 }} />}
            {job.stage && (
              <p className="sub mono" style={{ fontSize: 11, marginTop: 6 }}>
                Stage: {job.stage}
              </p>
            )}
            {job.error && (
              <p className="sub" style={{ color: "var(--ember)", marginTop: 8, fontWeight: 500 }}>
                {job.error.message}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
