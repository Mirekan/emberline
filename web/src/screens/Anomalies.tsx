import { useAoi } from "../App";

// Anomalies — unusual-activity markers.
export default function Anomalies() {
  const { series, lang } = useAoi();
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 20, flexWrap: "wrap" }}>
        <div>
          <span className="state-chip chip-neutral" style={{ fontSize: 10, marginBottom: 4 }}>
            {lang === "id" ? "PEMANTAUAN DEVIASI KLIMATOLOGI" : "CLIMATOLOGICAL DEVIATION MONITOR"}
          </span>
          <h1>{lang === "id" ? "Anomali — Penanda Deviasi Statistik Historis" : "Anomalies — statistical unusual-activity markers"}</h1>
        </div>
        <span className="state-chip chip-neutral mono" style={{ fontSize: 11 }}>
          {lang === "id" ? "MODUL PENGEMBANGAN LANJUTAN" : "PLANNED ENHANCEMENT MODULE"}
        </span>
      </div>

      <p className="sub" style={{ marginTop: 6 }}>
        {lang === "id"
          ? "Pratinjau modul pemantauan anomali: menandai hari observasi dengan nilai deviasi |z| ≥ 2,5 terhadap basis klimatologi hari dalam setahun (DOY 1–366) menggunakan median kokoh dan Median Absolute Deviation (MAD). Bersifat statistik deskriptif historis — bukan sistem peringatan dini atau peramalan bahaya."
          : "Preview of anomaly monitoring module: flags observation days where |z| ≥ 2.5 against the day-of-year (DOY 1–366) climatological baseline (robust median / Median Absolute Deviation). Marked as unusual historical deviations — descriptive statistics only, never predictive alerts or danger warnings."}
      </p>

      <div className="card" style={{ marginTop: 20, padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)" }}>
          <h2 style={{ margin: 0 }}>
            {lang === "id" ? "Struktur Telemetri Data Anomali" : "Planned anomaly telemetry structure"}
          </h2>
          <p className="sub" style={{ fontSize: 12, marginTop: 4 }}>
            {lang === "id"
              ? "Sepenuhnya jujur terhadap kontrak data: seluruh kolom diturunkan langsung dari artefak observasi terhitung tanpa interpolasi sintetis."
              : "Strictly contract-honest: all columns will derive from computed baseline artifacts without synthetic interpolation."}
          </p>
        </div>
        <table>
          <thead>
            <tr>
              <th>{lang === "id" ? "Kolom Telemetri" : "Telemetry Column"}</th>
              <th>{lang === "id" ? "Satuan / Standar Pengukuran" : "Measurement Unit / Standard"}</th>
              <th>{lang === "id" ? "Definisi & Makna Ilmiah" : "Scientific Definition & Meaning"}</th>
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
              <td>{lang === "id" ? "Aktivitas pembakaran yang tertekan maupun melonjak keduanya merupakan anomali klimatologis signifikan." : "Suppressed burning and elevated burning are both significant climatological anomalies."}</td>
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
            ? "Baris data terhubung langsung dengan tampilan kalender kebakaran dan grafik deret waktu. Pada kondisi data minim, hari dilabeli dukungan tidak cukup dan tidak pernah dianggap normal."
            : "Rows will link directly to the corresponding fire calendar day and time-series analytical views. Under sparse baseline conditions, days are labeled insufficient_support rather than assumed nominal."}
        </div>
      </div>

      <div className="boundary" style={{ marginTop: 18 }}>
        <b>
          {lang === "id"
            ? "Pemberitahuan Batasan Ilmiah: Penanda anomali adalah statistik deskriptif — bukan peringatan bahaya atau peramalan."
            : "Mandatory Guardrail Notice: Anomaly flags are descriptive statistics — not warning alerts, not forecasts."}
        </b>
        <p className="sub" style={{ marginTop: 4 }}>
          {lang === "id"
            ? "Implementasi telemetri dijadwalkan pada rilis lanjutan. Keterbukaan status ini memastikan tidak ada data anomali rekayasa atau sintetis yang ditampilkan secara palsu."
            : "Telemetry implementation scheduled for future release. Until formal deployment, this honest status disclosure ensures zero fabricated or synthetic anomaly flags."}
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
