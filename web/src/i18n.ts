// EmberLine Internationalization (i18n) Dictionary
// Supports Indonesian ('id') and English ('en') with type safety and fallback.

export type Lang = "id" | "en";

export const DICTIONARY = {
  id: {
    // Navigation & Global UI
    nav_overview: "Ikhtisar",
    nav_firemap: "Peta Kebakaran",
    nav_firecalendar: "Kalender Kebakaran",
    nav_anomalies: "Anomali",
    nav_analytics: "Analitik",
    nav_methodology: "Metodologi",
    nav_glossary: "Daftar Istilah",
    nav_lang_toggle: "Ganti bahasa (ID / EN)",
    nav_theme_dark: "Ganti ke mode gelap",
    nav_theme_light: "Ganti ke mode terang",
    mock_badge: "DATA CONTOH / SINTETIS",
    mock_badge_title: "Artefak tiruan aktif (Prinsip Kejujuran Ilmiah FR-UI-12)",

    // Telemetry Provenance Bar
    prov_loading: "Memuat data observasi satelit…",
    prov_run: "Eksekusi",
    prov_model: "Model",
    prov_daily_obs: "pengamatan harian",
    prov_descriptive: "Deskriptif, bukan prediktif",

    // Footer
    footer_disclosure_label: "Pengungkapan Ilmiah Wajib:",
    footer_disclosure_text:
      "Bersifat historis dan deskriptif — bukan prediktif. Titik panas (hotspot) adalah piksel deteksi termal satelit, belum tentu kebakaran fisik di daratan. Jendela kritis musiman menunjukkan puncak klimatologis historis, bukan rekomendasi pembakaran aman. Sumber data: NASA FIRMS.",
    footer_credit: "@AstraGokilNasaGamerHebatGaming2026 · NASA Space Apps 2026 Jakarta",

    // Overview Screen
    overview_eyebrow: "EMBERLINE · KONTROL MISI",
    overview_title_1: "Membaca jejak api.",
    overview_title_2: "Memahami pola bumi.",
    overview_desc:
      "Eksplorasi observasi kebakaran MODIS dan VIIRS—disajikan sebagai rekam historis yang transparan, lengkap dengan ketidakpastian dan celah data satelit.",
    overview_btn_calendar: "Jelajahi kalender",
    overview_btn_method: "Lihat metodologi",
    overview_scroll_cue: "Gulir untuk mengikuti perjalanan data",
    overview_stat_provinces: "provinsi · konsep demo",
    overview_stat_obs: "observasi pada area terpilih",
    overview_stat_history: "rekam satelit historis",
    overview_details_eyebrow: "Jelajahi data",
    overview_details_heading: "Kenali pola, pahami batas datanya.",
    overview_details_desc:
      "Aktivitas kebakaran berubah mengikuti musim, sementara cakupan satelit dapat meninggalkan celah pengamatan. Kalender menyatukan observasi agar Anda dapat membandingkan pola antarwaktu tanpa mengaburkan keterbatasan data.",
    overview_region: "Wilayah",
    overview_data_ready: "data siap",
    overview_queued: "dalam antrean",

    // HUD / Gauge Card
    hud_kicker: "HUD · Skala ilustratif",
    hud_safe: "Aman",
    hud_concept_coverage: "Cakupan konsep",
    hud_concept_val: "38 provinsi",
    hud_obs_label: "Observasi",
    hud_obs_val: "MODIS + VIIRS",
    hud_context_label: "Konteks",
    hud_context_val: "Historis",

    // FireMap Screen
    map_fullscreen: "Layar Penuh",
    map_exit_fullscreen: "Keluar Layar Penuh",
    map_open_panel: "Buka Panel",
    map_close_panel: "Tutup Panel",
    map_filter_title: "Wilayah Indonesia",
    map_filter_btn: "Filter Wilayah Indonesia",
    map_all_regions: "Semua Wilayah",
    map_search_placeholder: "Cari provinsi (mis. Riau, Kalimantan)…",
    map_basemap: "Peta Dasar:",
    map_basemap_dark: "Gelap (Esri)",
    map_basemap_osm: "Topografi (OSM)",
    map_points_on: "Titik Api: Aktif",
    map_points_off: "Titik Api: Nonaktif",
    map_points_desc: "Tampilkan atau sembunyikan titik deteksi satelit FIRMS",
    map_status_ready: "DATA SIAP",
    map_status_queued: "DALAM ANTREAN",
    map_time_range: "Rentang Waktu Observasi:",
    map_time_7d: "7 Hari Terakhir",
    map_time_30d: "30 Hari Terakhir",
    map_time_1y: "1 Tahun Terakhir",
    map_time_all: "Semua Tahun (2012–2026)",
    map_sensor_layers: "Lapisan Sensor Satelit:",
    map_inspector_title: "Inspeksi Titik Panas Terpilih",
    map_inspector_close: "Tutup",
    map_inspector_latlon: "Koordinat:",
    map_inspector_frp: "Energi Radiasi (FRP):",
    map_inspector_sensor: "Instrumen:",
    map_inspector_conf: "Keyakinan Deteksi:",
    map_inspector_dn: "Waktu Lintasan:",
    map_inspector_day: "Siang (Day overpass)",
    map_inspector_night: "Malam (Night overpass)",
    map_inspector_nearest: "Titik api terdekat berjarak",

    // Calendar Screen
    cal_title: "Kalender Kebakaran & Klimatologi",
    cal_view_yearly: "Ringkasan Tahunan",
    cal_view_monthly: "Komposit Bulanan",
    cal_sensor_harm: "Total FRP Terharmonisasi (Standar MODIS, MW)",
    cal_sensor_modis: "Total Mentah MODIS (Resolusi 1 km, MW)",
    cal_sensor_viirs: "Total Mentah VIIRS (Resolusi 375 m, MW)",
    cal_year_choice: "Pilihan Tahun",
    cal_month_choice: "Pilihan Bulan",
    cal_all_years: "Semua Tahun Pengamatan",
    cal_all_months: "Sepanjang Tahun (12 Bulan)",
    cal_gap_label: "Celah Data",
    cal_zero_label: "Valid 0 MW",
    cal_inspection_title: "Pemeriksaan Periode Terpilih",
    cal_no_period: "Belum Ada Periode Terpilih",
    cal_no_period_desc: "Klik salah satu kotak tahun atau bulan pada matriks untuk memeriksa profil telemetri dan hari aktif.",
    cal_kpi_label: "Akumulasi Energi Panas (FRP)",
    cal_ready_regions: "Wilayah yang Siap:",
    cal_open_region: "Buka",

    // Analytics (Compare) Screen
    compare_title: "Analitik — Rekam Satelit Mentah vs Deret Terharmonisasi",
    compare_export_btn: "Ekspor Deret Harian (CSV)",
    compare_legend_harm: "Terharmonisasi (Estimasi)",
    compare_legend_modis: "MODIS Aqua (Mentah)",
    compare_legend_viirs: "VIIRS SNPP (Mentah)",

    // Common Messages
    err_not_available: "Data Belum Tersedia untuk Wilayah Ini",
    err_not_available_desc: "Data observasi satelit untuk wilayah ini sedang dalam tahap pemrosesan awal.",
    back_to_ready: "Kembali ke Wilayah yang Siap",
  },
  en: {
    // Navigation & Global UI
    nav_overview: "Overview",
    nav_firemap: "Fire Map",
    nav_firecalendar: "Fire Calendar",
    nav_anomalies: "Anomalies",
    nav_analytics: "Analytics",
    nav_methodology: "Methodology",
    nav_glossary: "Inspect Glossary",
    nav_lang_toggle: "Switch language (ID / EN)",
    nav_theme_dark: "Switch to dark mode",
    nav_theme_light: "Switch to light mode",
    mock_badge: "MOCK / SYNTHETIC",
    mock_badge_title: "Synthetic fixture artifact active (Mandatory Guardrail FR-UI-12)",

    // Telemetry Provenance Bar
    prov_loading: "Loading satellite telemetry observations…",
    prov_run: "Run",
    prov_model: "Model",
    prov_daily_obs: "daily observations",
    prov_descriptive: "Descriptive, not predictive",

    // Footer
    footer_disclosure_label: "Mandatory Scientific Disclosure:",
    footer_disclosure_text:
      "Historical & descriptive — not predictive. A hotspot is a satellite thermal detection pixel, not necessarily a physical fire. Seasonal critical window indicates historical peak burning climatology, not a safe-to-burn recommendation. Data source: NASA FIRMS.",
    footer_credit: "@AstraGokilNasaGamerHebatGaming2026 · NASA Space Apps 2026 Jakarta",

    // Overview Screen
    overview_eyebrow: "EMBERLINE · MISSION CONTROL",
    overview_title_1: "Reading fire footprints.",
    overview_title_2: "Understanding Earth patterns.",
    overview_desc:
      "Exploration of MODIS and VIIRS fire observations—presented as a transparent historical record, complete with uncertainties and satellite retrieval gaps.",
    overview_btn_calendar: "Explore calendar",
    overview_btn_method: "Inspect methodology",
    overview_scroll_cue: "Scroll to follow data journey",
    overview_stat_provinces: "provinces · demo concept",
    overview_stat_obs: "observations in selected area",
    overview_stat_history: "historical satellite records",
    overview_details_eyebrow: "Explore data",
    overview_details_heading: "Recognize patterns, understand data limits.",
    overview_details_desc:
      "Fire activity shifts with seasons, while satellite passes can leave observation gaps. The calendar unifies observations so you can compare patterns over time without obscuring data limitations.",
    overview_region: "Region",
    overview_data_ready: "data ready",
    overview_queued: "queued",

    // HUD / Gauge Card
    hud_kicker: "HUD · Illustrative scale",
    hud_safe: "Safe",
    hud_concept_coverage: "Concept coverage",
    hud_concept_val: "38 provinces",
    hud_obs_label: "Observations",
    hud_obs_val: "MODIS + VIIRS",
    hud_context_label: "Context",
    hud_context_val: "Historical",

    // FireMap Screen
    map_fullscreen: "Fullscreen",
    map_exit_fullscreen: "Exit Fullscreen",
    map_open_panel: "Open Panel",
    map_close_panel: "Close Panel",
    map_filter_title: "Indonesia Regions",
    map_filter_btn: "Filter Indonesia Regions",
    map_all_regions: "All Regions",
    map_search_placeholder: "Search province (e.g. Riau, Kalimantan)…",
    map_basemap: "Basemap:",
    map_basemap_dark: "Dark (Esri)",
    map_basemap_osm: "Topography (OSM)",
    map_points_on: "Fire Points: Active",
    map_points_off: "Fire Points: Inactive",
    map_points_desc: "Show or hide FIRMS satellite detection dots",
    map_status_ready: "DATA READY",
    map_status_queued: "IN QUEUE",
    map_time_range: "Observation Time Range:",
    map_time_7d: "Last 7 Days",
    map_time_30d: "Last 30 Days",
    map_time_1y: "Last 1 Year",
    map_time_all: "All Years (2012–2026)",
    map_sensor_layers: "Satellite Sensor Layers:",
    map_inspector_title: "Selected Hotspot Inspection",
    map_inspector_close: "Close",
    map_inspector_latlon: "Coordinates:",
    map_inspector_frp: "Radiative Power (FRP):",
    map_inspector_sensor: "Instrument:",
    map_inspector_conf: "Detection Confidence:",
    map_inspector_dn: "Overpass Time:",
    map_inspector_day: "Day overpass",
    map_inspector_night: "Night overpass",
    map_inspector_nearest: "Nearest fire point is",

    // Calendar Screen
    cal_title: "Fire Calendar & Climatology",
    cal_view_yearly: "Yearly Summary",
    cal_view_monthly: "Monthly Composite",
    cal_sensor_harm: "Harmonized FRP-sum (MODIS-equivalent, MW)",
    cal_sensor_modis: "Raw MODIS FRP-sum (1 km scale, MW)",
    cal_sensor_viirs: "Raw VIIRS FRP-sum (375 m scale, MW)",
    cal_year_choice: "Year Selection",
    cal_month_choice: "Month Selection",
    cal_all_years: "All Observation Years",
    cal_all_months: "Full Annual Cycle (12 Months)",
    cal_gap_label: "Retrieval Gap",
    cal_zero_label: "Valid 0 MW",
    cal_inspection_title: "Selected Period Inspection",
    cal_no_period: "No Period Selected",
    cal_no_period_desc: "Click any year or month box in the matrix to inspect telemetry profiles and active observation days.",
    cal_kpi_label: "Fire Radiative Power (FRP) Sum",
    cal_ready_regions: "Ready Regions:",
    cal_open_region: "Open",

    // Analytics (Compare) Screen
    compare_title: "Analytics — Raw Satellite Records vs Harmonized Series",
    compare_export_btn: "Export Daily Series (CSV)",
    compare_legend_harm: "Harmonized (Model Estimate)",
    compare_legend_modis: "MODIS Aqua (Raw)",
    compare_legend_viirs: "VIIRS SNPP (Raw)",

    // Common Messages
    err_not_available: "Data Not Yet Available for this Region",
    err_not_available_desc: "Satellite telemetry data for this region is in preliminary processing.",
    back_to_ready: "Return to Ready Region",
  },
} as const;

export type TranslationKey = keyof typeof DICTIONARY.id;

export function getTranslation(lang: Lang, key: TranslationKey, params?: Record<string, string | number>): string {
  const dict = DICTIONARY[lang] || DICTIONARY.id;
  let text: string = dict[key] || DICTIONARY.id[key] || key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v));
    }
  }
  return text;
}
