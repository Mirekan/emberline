import { useEffect, useRef } from "react";
import {
  animate,
  motion,
  useMotionValue,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
  useTransform,
  type MotionValue,
} from "framer-motion";
import type { ReactNode } from "react";
import { stageState } from "./stageState";

type ActWindow = [number, number, number, number];

export function RiskGaugeCard() {
  const score = useMotionValue(0);
  const roundedScore = useTransform(score, value => Math.round(value).toString().padStart(2, "0"));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const arc = circumference * (260 / 360);

  useEffect(() => {
    const animation = animate(score, 24, {
      duration: 1.8,
      ease: [0.22, 1, 0.36, 1],
      delay: 0.35,
    });
    return () => animation.stop();
  }, [score]);

  return (
    <div
      className="hero-hud-card"
      role="img"
      aria-label="Ilustrasi gauge 24 dari 100, status Aman. Bukan skor risiko EmberLine."
    >
      <div className="hero-hud-heading">
        <span className="hero-hud-kicker">HUD · Skala ilustratif</span>
        <span className="hero-hud-live"><i /> DEMO</span>
      </div>

      <div className="hero-hud-main">
        <div className="hero-gauge">
          <svg viewBox="0 0 128 128" aria-hidden="true">
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="var(--hud-track)"
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`${arc} ${circumference}`}
            />
            <motion.circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="var(--safe)"
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`0 ${circumference}`}
              animate={{ strokeDasharray: `${arc * 0.24} ${circumference}` }}
              transition={{ duration: 1.8, ease: [0.22, 1, 0.36, 1], delay: 0.35 }}
            />
          </svg>
          <div className="hero-gauge-value">
            <strong><motion.span>{roundedScore}</motion.span></strong>
            <span>/100</span>
            <b><span /> Aman</b>
          </div>
        </div>

        <div className="hero-hud-metrics">
          <div><span>Cakupan konsep</span><strong>38 provinsi</strong></div>
          <div><span>Observasi</span><strong>MODIS + VIIRS</strong></div>
          <div><span>Konteks</span><strong>Historis</strong></div>
        </div>
      </div>

      <p className="hero-hud-note">
        Skor 24/100 dan 38 provinsi mengikuti visual demo new-ui, bukan hasil analisis EmberLine.
      </p>
    </div>
  );
}

const RISK_LEVELS = [
  { label: "Aman", color: "#81d5a3", range: [0.39, 0.45] as [number, number] },
  { label: "Waspada", color: "#f0be68", range: [0.43, 0.49] as [number, number] },
  { label: "Siaga", color: "#fa773f", range: [0.47, 0.53] as [number, number] },
  { label: "Bahaya", color: "#ff8b82", range: [0.51, 0.57] as [number, number] },
];

function RiskLevel({
  progress,
  reduced,
  label,
  color,
  range,
}: {
  progress: MotionValue<number>;
  reduced: boolean;
  label: string;
  color: string;
  range: [number, number];
}) {
  const scaleX = useTransform(progress, range, reduced ? [1, 1] : [0.28, 1]);
  const opacity = useTransform(progress, range, reduced ? [1, 1] : [0.35, 1]);

  return (
    <div className="story-risk-level">
      <motion.span
        style={{ backgroundColor: color, scaleX: reduced ? 1 : scaleX, opacity: reduced ? 1 : opacity }}
      />
      <small>{label}</small>
    </div>
  );
}

function RiskScale({ progress, reduced }: { progress: MotionValue<number>; reduced: boolean }) {
  return (
    <div className="story-risk-scale" aria-label="Skala ilustrasi: Aman, Waspada, Siaga, Bahaya">
      {RISK_LEVELS.map(level => (
        <RiskLevel {...level} key={level.label} progress={progress} reduced={reduced} />
      ))}
    </div>
  );
}

function ActPanel({
  progress,
  range,
  index,
  eyebrow,
  title,
  emphasis,
  body,
  align,
  reduced,
  children,
}: {
  progress: MotionValue<number>;
  range: ActWindow;
  index: string;
  eyebrow: string;
  title: string;
  emphasis: string;
  body: string;
  align: "left" | "right";
  reduced: boolean;
  children?: ReactNode;
}) {
  const [fadeIn, fullIn, fullOut, fadeOut] = range;
  const opacity = useTransform(progress, [fadeIn, fullIn, fullOut, fadeOut], [0, 1, 1, reduced ? 1 : 0]);
  const y = useTransform(progress, [fadeIn, fullIn, fullOut, fadeOut], [reduced ? 0 : 32, 0, 0, reduced ? 0 : -32]);
  const blur = useTransform(
    progress,
    [fadeIn, fullIn, fullOut, fadeOut],
    reduced ? ["blur(0px)", "blur(0px)", "blur(0px)", "blur(0px)"] : ["blur(6px)", "blur(0px)", "blur(0px)", "blur(6px)"],
  );

  return (
    <motion.article
      className={`story-act story-act-${align}`}
      style={{ opacity: reduced ? 1 : opacity, y: reduced ? 0 : y, filter: reduced ? "none" : blur }}
      aria-label={`${index} ${eyebrow}`}
    >
      <p className="story-act-kicker"><span>{index}</span> {eyebrow}</p>
      <h2>{title} <em>{emphasis}</em></h2>
      <p className="story-act-copy">{body}</p>
      {children}
    </motion.article>
  );
}

function StoryProgress({ progress }: { progress: MotionValue<number> }) {
  const scaleY = useTransform(progress, [0.02, 0.98], [0.02, 1]);
  return (
    <div className="story-progress" aria-hidden="true">
      <span>CERITA</span>
      <div className="story-progress-track">
        <motion.i style={{ scaleY, transformOrigin: "top" }} />
      </div>
      <div className="story-progress-dots"><i /><i /><i /></div>
    </div>
  );
}

export default function ScrollyActs() {
  const sectionRef = useRef<HTMLElement>(null);
  const prefersReducedMotion = useReducedMotion();
  const reduced = prefersReducedMotion ?? false;
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end end"],
  });

  useMotionValueEvent(scrollYProgress, "change", value => {
    stageState.progress = reduced ? 0 : value;
  });

  useEffect(() => {
    if (reduced) stageState.progress = 0;
  }, [reduced]);

  return (
    <section
      className={`overview-story${reduced ? " overview-story-static" : ""}`}
      id="cerita"
      ref={sectionRef}
      style={{ height: reduced ? "auto" : "300vh" }}
      aria-label="Cerita observasi EmberLine dalam tiga tahap"
    >
      <StoryProgress progress={scrollYProgress} />
      <div className="overview-story-sticky">
        <ActPanel
          progress={scrollYProgress}
          range={[0, 0.06, 0.27, 0.36]}
          index="01"
          eyebrow="Deteksi"
          title="Panas permukaan"
          emphasis="terbaca dari orbit."
          body="MODIS dan VIIRS menangkap anomali termal. EmberLine menyatukan observasi historis sambil mempertahankan perbedaan sensor dan celah pengamatan."
          align="left"
          reduced={reduced}
        >
          <div className="story-chip-row"><span>MODIS C6.1</span><span>VIIRS 375 m</span><span>FIRMS</span></div>
        </ActPanel>
        <ActPanel
          progress={scrollYProgress}
          range={[0.32, 0.4, 0.6, 0.68]}
          index="02"
          eyebrow="Analisa"
          title="Dari sensor berbeda"
          emphasis="ke rekam yang utuh."
          body="Harmonisasi membantu membandingkan deret waktu. Ketidakpastian dan batas metodologi tetap ditampilkan agar pola historis tidak disalahartikan sebagai prediksi."
          align="right"
          reduced={reduced}
        >
          <RiskScale progress={scrollYProgress} reduced={reduced} />
        </ActPanel>
        <ActPanel
          progress={scrollYProgress}
          range={[0.64, 0.72, 0.95, 1]}
          index="03"
          eyebrow="Kesiapsiagaan"
          title="Pahami rekamnya."
          emphasis="Siapkan langkah."
          body="Saat bara visual mendingin menjadi hijau, ceritanya beralih dari deteksi ke pemahaman. Data EmberLine bersifat historis dan deskriptif—untuk kondisi terkini, ikuti informasi resmi BPBD setempat."
          align="left"
          reduced={reduced}
        >
          <div className="story-chip-row"><span className="story-safe-chip"><i /> Historis, bukan prediksi</span><span>Informasi resmi BPBD</span></div>
        </ActPanel>
      </div>
    </section>
  );
}
