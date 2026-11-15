import React, { createContext, lazy, Suspense, useContext, useEffect, useState } from "react";
import { motion, MotionConfig } from "framer-motion";
import { api, Series } from "./api";
import { HomeIcon, MapIcon, CalendarIcon, CrisisIcon, ChartIcon, ResearchIcon, FlameMark, ContrastThemeIcon } from "./components/Icons";
import { getTranslation, Lang, TranslationKey } from "./i18n";
import Overview from "./screens/Overview";
import CalendarScreen from "./screens/CalendarScreen";
import Compare from "./screens/Compare";
import Seasons from "./screens/Seasons";
import MethodScreen from "./screens/MethodScreen";
import FireMap from "./screens/FireMap";
import Anomalies from "./screens/Anomalies";

const EmberStage = lazy(() => import("./components/EmberStage"));

const TAB_DEFS = [
  { id: "overview" as const, key: "nav_overview" as const, Icon: HomeIcon },
  { id: "firemap" as const, key: "nav_firemap" as const, Icon: MapIcon },
  { id: "firecalendar" as const, key: "nav_firecalendar" as const, Icon: CalendarIcon },
  { id: "anomalies" as const, key: "nav_anomalies" as const, Icon: CrisisIcon },
  { id: "analytics" as const, key: "nav_analytics" as const, Icon: ChartIcon },
  { id: "methodology" as const, key: "nav_methodology" as const, Icon: ResearchIcon },
];
type TabId = (typeof TAB_DEFS)[number]["id"];

type Ctx = {
  aoi: string;
  setAoi: (a: string) => void;
  series: Series | null;
  theme: "light" | "dark";
  calFilter: string | null;
  setCalFilter: (f: string | null) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  toggleLang: () => void;
  t: (k: TranslationKey, params?: Record<string, string | number>) => string;
};
const AoiContext = createContext<Ctx>({
  aoi: "riau",
  setAoi: () => { },
  series: null,
  theme: "light",
  calFilter: null,
  setCalFilter: () => { },
  lang: "id",
  setLang: () => { },
  toggleLang: () => { },
  t: (k: TranslationKey) => k,
});
export const useAoi = () => useContext(AoiContext);

export default function App() {
  const [tab, setTab] = useState<TabId>("overview");
  const [aoi, setAoi] = useState("riau");
  const [series, setSeries] = useState<Series | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [calFilter, setCalFilter] = useState<string | null>(null);
  const [lang, setLang] = useState<Lang>(() => {
    // Strictly default to 'id' (Bahasa Indonesia) on first load
    const savedLang = localStorage.getItem("emberline-lang-v3");
    return savedLang === "en" ? "en" : "id";
  });
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const savedTheme = localStorage.getItem("emberline-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("emberline-theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("lang", lang);
    localStorage.setItem("emberline-lang-v3", lang);
  }, [lang]);

  const toggleTheme = () => {
    setTheme(curr => (curr === "dark" ? "light" : "dark"));
  };

  const toggleLang = () => {
    setLang(curr => (curr === "id" ? "en" : "id"));
  };

  const t = (k: TranslationKey, params?: Record<string, string | number>) => getTranslation(lang, k, params);

  useEffect(() => {
    if (tab === "firemap" || tab === "anomalies") return; // backlog / live map screens
    setSeries(null); setError(null);
    api.series(aoi).then(setSeries).catch(e => setError(e.message));
  }, [aoi, tab]);

  return (
    <AoiContext.Provider value={{ aoi, setAoi, series, theme, calFilter, setCalFilter, lang, setLang, toggleLang, t }}>
      <MotionConfig reducedMotion="user">
        <div className="app">
          {tab === "overview" && (
            <Suspense fallback={<div className="ember-stage" aria-hidden="true"><div className="ember-stage-fallback" /></div>}>
              <EmberStage theme={theme} />
            </Suspense>
          )}
          <header className="topbar">
            <div className="brand">
              <img src="/emberline_logo.png" alt="Logo" style={{ width: 150, height: 50, objectFit: "contain" }} />
            </div>

            <nav className="iconnav" role="tablist" aria-label="Console Sections">
              {TAB_DEFS.map(({ id, key, Icon }) => (
                <button
                  key={id}
                  role="tab"
                  aria-selected={tab === id}
                  className={"iconnav-item" + (tab === id ? " active" : "")}
                  onClick={() => setTab(id)}
                >
                  {tab === id && (
                    <motion.span
                      layoutId="activeTab"
                      className="nav-pill"
                      transition={{ type: "spring", stiffness: 320, damping: 30 }}
                    />
                  )}
                  <Icon /> <span>{t(key)}</span>
                </button>
              ))}
            </nav>

            <div className="topbar-actions">
              <button
                className="lang-toggle-btn"
                onClick={toggleLang}
                title={t("nav_lang_toggle")}
                aria-label={t("nav_lang_toggle")}
              >
                {lang === "id" ? "ID" : "EN"}
              </button>

              <button
                className="theme-toggle-btn"
                onClick={toggleTheme}
                title={theme === "dark" ? t("nav_theme_light") : t("nav_theme_dark")}
                aria-label={theme === "dark" ? t("nav_theme_light") : t("nav_theme_dark")}
                aria-pressed={theme === "dark"}
              >
                <ContrastThemeIcon />
              </button>
            </div>
          </header>

          <main className={"content" + (tab === "firemap" ? " content-flush" : "") + (tab === "overview" ? " content-overview" : "")}>
            <div key={tab} className="screen-fade">
              {error && tab === "analytics" && (
                <div className="status-panel failed" style={{ marginBottom: 20 }}>
                  <div className="status-title">{t("err_not_available")}</div>
                  <p className="status-desc">
                    {t("err_not_available_desc")}
                  </p>
                  {aoi !== "riau" && (
                    <div style={{ marginTop: 10 }}>
                      <button className="btn secondary" onClick={() => setAoi("riau")}>
                        {t("back_to_ready")}
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
                {tab === "overview" && (
                  <Overview
                    goCalendar={() => setTab("firecalendar")}
                    goMethod={() => setTab("methodology")}
                  />
                )}
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
              <b>{t("footer_disclosure_label")}</b> {t("footer_disclosure_text")}
            </div>
            <div className="meta-right">{t("footer_credit")}</div>
          </footer>
        </div>
      </MotionConfig>
    </AoiContext.Provider>
  );
}
