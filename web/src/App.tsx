import React, { createContext, useContext, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api, Series } from "./api";
import { HomeIcon, MapIcon, CalendarIcon, CrisisIcon, ChartIcon, ResearchIcon, FlameMark } from "./components/Icons";
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

type Ctx = { aoi: string; setAoi: (a: string) => void; series: Series | null; calFilter: string | null; setCalFilter: (f: string | null) => void };
const AoiContext = createContext<Ctx>({ aoi: "riau", setAoi: () => {}, series: null, calFilter: null, setCalFilter: () => {} });
export const useAoi = () => useContext(AoiContext);

export default function App() {
  const [tab, setTab] = useState<TabId>("overview");
  const [aoi, setAoi] = useState("riau");
  const [series, setSeries] = useState<Series | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [calFilter, setCalFilter] = useState<string | null>(null);

  useEffect(() => {
    if (tab === "firemap" || tab === "anomalies") return; // backlog screens don't need artifacts
    setSeries(null); setError(null);
    api.series(aoi).then(setSeries).catch(e => setError(e.message));
  }, [aoi, tab]);

  const prov = series
    ? `run ${series.run_id.slice(-14)} · ${series.model_version ?? "?"}`
    : "loading artifacts…";

  return (
    <AoiContext.Provider value={{ aoi, setAoi, series, calFilter, setCalFilter }}>
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <FlameMark size={34} />
            <span className="brand-word">EmberLine</span>
          </div>
          <nav className="iconnav" role="tablist" aria-label="Sections">
            {TABS.map(([id, label, Icon]) => (
              <button key={id} role="tab" aria-selected={tab === id}
                className={"iconnav-item" + (tab === id ? " active" : "")}
                onClick={() => setTab(id as TabId)}>
                <Icon /> <span>{label}</span>
              </button>
            ))}
          </nav>
        </header>
        {tab !== "firemap" && <div className="prov">{prov}</div>}
        <main className={"content" + (tab === "firemap" ? " content-flush" : "")}>
          <div key={tab} className="screen-fade">
          {error && tab === "analytics" &&
            <div className="card"><h2>Could not load artifacts</h2>
              <p className="sub">{error} — start the API (make serve) or run pipeline/run.py.</p></div>}
          <motion.div key={tab} className="screen-fade"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 240, damping: 26 }}>
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
          <div className="handle">@AstraGokilNasaGamerHebatGaming2026</div>
          <div className="boundary-line">
            Historical &amp; descriptive — not predictive. A hotspot is an observation, not
            necessarily a fire. Critical window is not a safe-to-burn recommendation. Data: NASA FIRMS.
          </div>
        </footer>
      </div>
    </AoiContext.Provider>
  );
}
