import React, { createContext, useContext, useEffect, useState } from "react";
import { motion, MotionConfig } from "framer-motion";
import { api, Series } from "./api";
import { HomeIcon, MapIcon, CalendarIcon, CrisisIcon, ChartIcon, ResearchIcon, FlameMark, SunIcon, MoonIcon } from "./components/Icons";
import Overview from "./screens/Overview";
import CalendarScreen from "./screens/CalendarScreen";
import Compare from "./screens/Compare";
import Seasons from "./screens/Seasons";
import MethodScreen from "./screens/MethodScreen";
import FireMap from "./screens/FireMap";
import Anomalies from "./screens/Anomalies";

const TABS = [
  ["overview", "Overview", HomeIcon],
  ["firemap", "Fire Map", MapIcon],
  ["firecalendar", "Fire Calendar", CalendarIcon],
  ["anomalies", "Anomalies", CrisisIcon],
  ["analytics", "Analytics", ChartIcon],
  ["methodology", "Methodology", ResearchIcon],
] as const;
type TabId = (typeof TABS)[number][0];

type Ctx = {
  aoi: string;
  setAoi: (a: string) => void;
  series: Series | null;
  calFilter: string | null;
  setCalFilter: (f: string | null) => void;
};
const AoiContext = createContext<Ctx>({ aoi: "riau", setAoi: () => {}, series: null, calFilter: null, setCalFilter: () => {} });
export const useAoi = () => useContext(AoiContext);

export default function App() {
  const [tab, setTab] = useState<TabId>("overview");
  const [aoi, setAoi] = useState("riau");
  const [series, setSeries] = useState<Series | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [calFilter, setCalFilter] = useState<string | null>(null);
  const [theme, setTheme] = useState<"light" | "dark" | "system">(() => {
    return (localStorage.getItem("emberline-theme") as "light" | "dark" | "system") || "system";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
      localStorage.removeItem("emberline-theme");
    } else {
      root.setAttribute("data-theme", theme);
      localStorage.setItem("emberline-theme", theme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(curr => (curr === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    if (tab === "firemap" || tab === "anomalies") return; // backlog / live map screens
    setSeries(null); setError(null);
    api.series(aoi).then(setSeries).catch(e => setError(e.message));
  }, [aoi, tab]);

  const isMock = Boolean(series?.mock || series?.fixture);

  const provLeft = series
    ? (
      <>
        <span>Run <span className="mono">{series.run_id.slice(-14)}</span></span>
        <span className="prov-sep">|</span>
        <span>Model <span className="mono">{series.model_version ?? "v1.0-harm"}</span></span>
        <span className="prov-sep">|</span>
        <span className="mono">{series.days.length.toLocaleString("en-US")} daily observations</span>
      </>
    )
    : "Memuat data observasi satelit…";

  return (
    <AoiContext.Provider value={{ aoi, setAoi, series, calFilter, setCalFilter }}>
      <MotionConfig reducedMotion="user">
        <div className="app">
          <header className="topbar">
            <div className="brand">
              <FlameMark size={32} />
              <span className="brand-word">EmberLine</span>
              <span className="brand-tag">SPACE APPS 2026</span>
              {isMock && (
                <span className="mock-badge" title="Synthetic fixture artifact active (Mandatory Guardrail FR-UI-12)">
                  <span className="mock-dot" /> MOCK / SYNTHETIC
                </span>
              )}
            </div>

            <nav className="iconnav" role="tablist" aria-label="Console Sections">
              {TABS.map(([id, label, Icon]) => (
                <button
                  key={id}
                  role="tab"
                  aria-selected={tab === id}
                  className={"iconnav-item" + (tab === id ? " active" : "")}
                  onClick={() => setTab(id as TabId)}
                >
                  {tab === id && (
                    <motion.span
                      layoutId="activeTab"
                      className="nav-pill"
                      transition={{ type: "spring", stiffness: 320, damping: 30 }}
                    />
                  )}
                  <Icon /> <span>{label}</span>
                </button>
              ))}
            </nav>

            <div className="topbar-actions">
              <button
                className="glossary-trigger"
                onClick={() => setTab("methodology")}
                title="Inspect plain-language definitions for every scientific term"
              >
                <ResearchIcon /> <span>Inspect glossary</span>
              </button>
              <button
                className="theme-toggle"
                onClick={toggleTheme}
                title={`Toggle Light / Dark mode (current: ${theme})`}
                aria-label="Toggle visual theme"
              >
                {theme === "dark" ? <SunIcon /> : <MoonIcon />}
              </button>
            </div>
          </header>

          {tab !== "firemap" && (
            <div className="prov">
              <div className="prov-left">{provLeft}</div>
              <div className="prov-right">
                <span className="state-chip chip-neutral" style={{ fontSize: 10 }}>Descriptive, not predictive</span>
                <span className="prov-sep">|</span>
                <span>NASA FIRMS</span>
                <span className="prov-sep">|</span>
                <span>MODIS C6.1 (Aqua) + VIIRS 375m (S-NPP)</span>
              </div>
            </div>
          )}

          <main className={"content" + (tab === "firemap" ? " content-flush" : "")}>
            <div key={tab} className="screen-fade">
              {error && tab === "analytics" && (
                <div className="status-panel failed" style={{ marginBottom: 20 }}>
                  <div className="status-title">Data Pengamatan Belum Tersedia</div>
                  <p className="status-desc">
                    Data observasi satelit multi-sensor untuk wilayah ini sedang dalam tahap pemrosesan.
                  </p>
                  {aoi !== "riau" && (
                    <div style={{ marginTop: 10 }}>
                      <button className="btn secondary" onClick={() => setAoi("riau")}>
                        Kembali ke Riau (Data Siap)
                      </button>
                    </div>
                  )}
                </div>
              )}
              <motion.div
                key={tab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 320, damping: 30 }}
              >
                {tab === "overview" && <Overview goCalendar={() => setTab("firecalendar")} />}
                {tab === "firemap" && <FireMap />}
                {tab === "firecalendar" && <CalendarScreen goMap={() => setTab("firemap")} />}
                {tab === "anomalies" && <Anomalies />}
                {tab === "analytics" && <Compare />}
                {tab === "methodology" && <MethodScreen />}
              </motion.div>
            </div>
          </main>

          <footer className="footer">
            <div className="boundary-line">
              <b>Mandatory Scientific Disclosure:</b> Historical &amp; descriptive — not predictive.
              A hotspot is a satellite thermal detection pixel, not necessarily a physical fire.
              Seasonal critical window indicates historical peak burning climatology, not a safe-to-burn recommendation.
              Data source: NASA FIRMS.
            </div>
            <div className="meta-right">@AstraGokilNasaGamerHebatGaming2026 · NASA Space Apps 2026 Jakarta</div>
          </footer>
        </div>
      </MotionConfig>
    </AoiContext.Provider>
  );
}
