import { useEffect, useState } from "react";
import { useAoi } from "../App";
import { api, Preset } from "../api";
import { PRESET_NAMES } from "../presets";

// Planned view for historical anomaly markers.
export default function Anomalies() {
  const { aoi, setAoi, series, lang } = useAoi();
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            {lang === "id" ? "DEVIASI HISTORIS" : "HISTORICAL DEVIATIONS"}
          </span>
          <h1>{lang === "id" ? "Anomali historis" : "Historical anomalies"}</h1>
        </div>
        <span className="state-chip chip-neutral mono" style={{ fontSize: 11 }}>
          {lang === "id" ? "DIRENCANAKAN" : "PLANNED"}
        </span>
      </div>

      <div
        className="card"
        style={{
          marginTop: 18,
          marginBottom: 16,
          padding: "12px 18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          flexWrap: "wrap",
          background: "var(--surface)",
          border: "1px solid var(--line)",
        }}
      >
        <label style={{ display: "inline-flex", alignItems: "center", gap: 10, fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ color: "var(--ember)" }}>
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          <span style={{ color: "var(--ink2)", fontSize: 12 }}>
            {lang === "id" ? "Pilih Wilayah Pantauan:" : "Select Monitored Region:"}
          </span>
          <select
            className="glass-select"
            value={aoi}
            aria-label={lang === "id" ? "Pilih wilayah pantauan" : "Select monitored region"}
            onChange={e => setAoi(e.target.value)}
            style={{ minWidth: 260, fontWeight: 600 }}
          >
            {presets.map(p => (
              <option key={p.id} value={p.id}>
                {PRESET_NAMES[lang]?.[p.id] ?? p.name}
              </option>
            ))}
          </select>
        </label>

        <span className="state-chip chip-neutral mono" style={{ fontSize: 11 }}>
          AOI: {aoi}
        </span>
      </div>

      <p className="sub" style={{ marginTop: 6 }}>
        {lang === "id"
          ? "Modul yang direncanakan akan membandingkan FRP-sum harian dengan median dan MAD untuk hari yang sama dalam setahun (DOY 1–366). Hasilnya akan merangkum deviasi historis, bukan memberi peringatan atau prediksi."
          : "The planned module will compare daily FRP-sum with the median and MAD for the same day of year (DOY 1–366). It will summarize historical deviations, not issue warnings or forecasts."}
      </p>

      <div className="card" style={{ marginTop: 20, padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)" }}>
          <h2 style={{ margin: 0 }}>
            {lang === "id" ? "Kolom yang direncanakan" : "Planned fields"}
          </h2>
          <p className="sub" style={{ fontSize: 12, marginTop: 4 }}>
            {lang === "id"
              ? "Halaman ini menjelaskan kolom yang akan digunakan. Hasil anomali belum dihitung."
              : "This page describes the planned fields. Anomaly results are not calculated yet."}
          </p>
        </div>
        <table>
          <thead>
            <tr>
              <th>{lang === "id" ? "Kolom" : "Field"}</th>
              <th>{lang === "id" ? "Satuan / Format" : "Unit / Format"}</th>
              <th>{lang === "id" ? "Keterangan" : "Description"}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 600 }}>{lang === "id" ? "Tanggal Observasi" : "Observation Date"}</td>
              <td className="mono">YYYY-MM-DD (UTC)</td>
              <td>{lang === "id" ? "Hari kalender UTC dari lintasan deteksi satelit yang diagregasi." : "UTC calendar day of the aggregated satellite detection overpass."}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>{lang === "id" ? "Skor-z Kokoh (Robust z-score)" : "Robust z-score"}</td>
              <td className="mono">z = (FRP - Median) / (1.4826 × MAD)</td>
              <td>{lang === "id" ? "Jarak statistik terstandarisasi dari klimatologi DOY dengan mempertahankan arah tanda (±)." : "Standardized statistical distance from DOY climatology, preserving directional sign (±)."}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>{lang === "id" ? "Arah Deviasi" : "Deviation Direction"}</td>
              <td className="mono">above_normal | below_normal</td>
              <td>{lang === "id" ? "Menunjukkan apakah FRP-sum berada di bawah atau di atas median klimatologi." : "Indicates whether FRP-sum is below or above the climatological median."}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>{lang === "id" ? "Observasi vs Klimatologi" : "Observed vs Climatology"}</td>
              <td className="mono">FRP-sum (MW)</td>
              <td>{lang === "id" ? "Nilai harian FRP terharmonisasi dibandingkan langsung dengan median klimatologis DOY (MW)." : "Daily observed harmonized FRP-sum compared directly with climatological DOY median (MW)."}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600 }}>{lang === "id" ? "Jumlah Sampel Dasar" : "Baseline Sample Size"}</td>
              <td className="mono">years_active / years_eligible</td>
              <td>{lang === "id" ? "Jendela klimatologi acuan dengan penyebut tahun pengamatan aktif yang terverifikasi." : "Frozen reference climatology window with explicit eligible-year denominator count."}</td>
            </tr>
          </tbody>
        </table>
        <div style={{ padding: "12px 18px", borderTop: "1px solid var(--line)", fontSize: 12, color: "var(--ink2)", background: "var(--sunken)" }}>
          {lang === "id"
            ? "Saat data dasar tidak cukup, hasil akan ditandai insufficient_support dan tidak dianggap normal."
            : "If the baseline has too little data, the result will be marked insufficient_support, not treated as normal."}
        </div>
      </div>

      <div className="boundary" style={{ marginTop: 18 }}>
        <b>
          {lang === "id"
            ? "Batasan: penanda anomali bersifat deskriptif, bukan peringatan atau prediksi."
            : "Limit: anomaly flags are descriptive, not warnings or forecasts."}
        </b>
        <p className="sub" style={{ marginTop: 4 }}>
          {lang === "id"
            ? "Fitur ini belum menghitung atau menampilkan penanda anomali."
            : "This feature does not calculate or display anomaly flags yet."}
        </p>
      </div>

      {series && (
        <p className="sub mono" style={{ fontSize: 11, marginTop: 14 }}>
          {lang === "id" ? "Konteks artefak: " : "Artifact context: "}{series.fixture ?? "real production artifacts"} · run ID {series.run_id.slice(-14)}
        </p>
      )}
    </div>
  );
}
