import { memo } from "react";

export const HeroBackground = memo(function HeroBackground() {
  return (
    <div className="hero-forest-bg" aria-hidden="true">
      {/* 1. Ambient Thermal Peatland Fire Glow */}
      <div className="forest-fire-glow forest-fire-glow-base" />
      <div className="forest-fire-glow forest-fire-glow-accent" />

      {/* 2. Vector Silhouette of Peatland Forest with Smoldering Embers & Smoke */}
      <svg
        className="forest-fire-svg"
        viewBox="0 0 1440 480"
        fill="none"
        preserveAspectRatio="xMidYMax slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Ground fireline gradient */}
          <linearGradient id="groundFireGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="var(--ember)" stopOpacity="0.45" />
            <stop offset="35%" stopColor="#E8763C" stopOpacity="0.22" />
            <stop offset="70%" stopColor="#F0BE68" stopOpacity="0.08" />
            <stop offset="100%" stopColor="var(--canvas)" stopOpacity="0" />
          </linearGradient>

          {/* Peatland ground flare hotspots */}
          <radialGradient id="fireHotspot1" cx="32%" cy="92%" r="28%">
            <stop offset="0%" stopColor="#FF6B35" stopOpacity="0.38" />
            <stop offset="40%" stopColor="var(--ember)" stopOpacity="0.18" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>

          <radialGradient id="fireHotspot2" cx="78%" cy="90%" r="35%">
            <stop offset="0%" stopColor="#FFA439" stopOpacity="0.42" />
            <stop offset="45%" stopColor="var(--ember)" stopOpacity="0.20" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>

          {/* Tree Silhouette Gradient (Fading into smoke/sky) */}
          <linearGradient id="treeSilGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="var(--ink)" stopOpacity="0.32" />
            <stop offset="60%" stopColor="var(--ink)" stopOpacity="0.18" />
            <stop offset="100%" stopColor="var(--ink)" stopOpacity="0.04" />
          </linearGradient>

          {/* Distant background tree line */}
          <linearGradient id="distantTreeGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="var(--ink)" stopOpacity="0.14" />
            <stop offset="70%" stopColor="var(--ink)" stopOpacity="0.05" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </linearGradient>

          {/* Rising Smoke Wisps Gradient */}
          <linearGradient id="smokeGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="var(--ember)" stopOpacity="0.20" />
            <stop offset="50%" stopColor="var(--ink3)" stopOpacity="0.08" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Hotspot radial heat sources at ground level */}
        <rect x="0" y="240" width="1440" height="240" fill="url(#fireHotspot1)" />
        <rect x="0" y="200" width="1440" height="280" fill="url(#fireHotspot2)" />
        <rect x="0" y="320" width="1440" height="160" fill="url(#groundFireGrad)" />

        {/* --- LAYER 1: Distant Background Forest Canopy (Hazy Treeline) --- */}
        <path
          d="M 0 380 
             Q 30 350 70 365 Q 110 340 160 355 Q 210 330 270 350 Q 330 335 390 355
             Q 450 325 510 345 Q 570 330 630 350 Q 690 320 760 345 Q 820 330 880 350
             Q 940 315 1010 340 Q 1070 325 1140 345 Q 1200 320 1260 340 Q 1320 330 1380 350
             Q 1410 340 1440 355 L 1440 480 L 0 480 Z"
          fill="url(#distantTreeGrad)"
        />

        {/* --- LAYER 2: Midground Peatland Forest Trees (Tall Trunks & Broad Crowns) --- */}
        {/* Tree Cluster Left (behind copy) */}
        <g fill="url(#treeSilGrad)">
          {/* Tree 1: Tall Dipterocarp */}
          <path d="M 85 480 L 89 270 Q 75 250 60 230 Q 80 220 92 210 Q 100 170 115 190 Q 130 175 140 200 Q 155 220 140 240 Q 125 250 97 270 L 101 480 Z" />
          {/* Tree 2: Slender Palm / Peat Tree */}
          <path d="M 170 480 L 173 310 Q 150 300 135 285 Q 160 275 174 265 Q 185 245 195 260 Q 215 250 220 275 Q 200 290 180 310 L 183 480 Z" />
          {/* Tree 3 */}
          <path d="M 280 480 L 284 330 Q 260 315 250 295 Q 275 285 286 270 Q 305 260 315 280 Q 330 270 340 295 Q 320 315 293 330 L 296 480 Z" />
          {/* Tree 4 */}
          <path d="M 410 480 L 413 350 Q 390 335 385 315 Q 405 310 415 295 Q 430 285 440 305 Q 460 300 455 325 Q 435 340 422 350 L 424 480 Z" />
        </g>

        {/* Tree Cluster Center & Right (under & behind the HUD card) */}
        <g fill="url(#treeSilGrad)">
          {/* Tree 5: Large emergent crown */}
          <path d="M 640 480 L 645 260 Q 615 240 595 210 Q 625 200 645 185 Q 660 145 685 165 Q 710 145 730 175 Q 755 200 735 225 Q 710 240 658 260 L 661 480 Z" />
          {/* Tree 6 */}
          <path d="M 780 480 L 784 290 Q 760 270 745 250 Q 770 240 786 225 Q 805 205 825 230 Q 845 215 855 245 Q 835 265 797 290 L 800 480 Z" />
          {/* Tree 7: Prominent Peat Swamp Canopy Tree */}
          <path d="M 950 480 L 956 230 Q 920 210 900 175 Q 935 165 958 145 Q 975 110 1005 130 Q 1035 110 1055 145 Q 1085 170 1060 200 Q 1030 215 970 230 L 974 480 Z" />
          {/* Tree 8 */}
          <path d="M 1110 480 L 1115 280 Q 1085 260 1070 235 Q 1098 225 1118 205 Q 1135 185 1155 210 Q 1180 195 1190 225 Q 1165 250 1128 280 L 1131 480 Z" />
          {/* Tree 9: Far Right Forest Flank */}
          <path d="M 1270 480 L 1276 250 Q 1240 230 1225 195 Q 1258 185 1278 165 Q 1295 130 1325 150 Q 1355 130 1375 165 Q 1400 190 1380 220 Q 1350 235 1290 250 L 1294 480 Z" />
          {/* Tree 10 */}
          <path d="M 1385 480 L 1389 310 Q 1365 295 1355 270 Q 1380 260 1392 245 Q 1410 230 1425 255 Q 1445 245 1450 270 Q 1430 290 1401 310 L 1403 480 Z" />
        </g>

        {/* --- LAYER 3: Smoke Trails & Ascending Thermal Plumes --- */}
        <g fill="url(#smokeGrad)">
          {/* Smoke column from ground peat fire 1 */}
          <path d="M 330 480 C 310 420, 270 380, 290 320 C 310 260, 360 220, 340 160 C 320 100, 280 80, 250 40 L 290 40 C 320 80, 360 120, 380 180 C 400 240, 360 290, 340 350 C 320 410, 360 450, 380 480 Z" />
          {/* Smoke column from hotspot 2 */}
          <path d="M 980 480 C 960 410, 920 370, 940 300 C 960 230, 1020 190, 1000 130 C 980 80, 940 60, 910 20 L 950 20 C 980 60, 1030 100, 1045 160 C 1060 220, 1010 270, 995 330 C 980 390, 1010 440, 1030 480 Z" />
          {/* Secondary smoke wisp */}
          <path d="M 680 480 C 660 430, 630 400, 645 350 C 660 300, 700 260, 685 210 C 670 160, 640 140, 610 90 L 640 90 C 670 130, 710 160, 725 215 C 740 270, 700 310, 685 360 C 670 410, 700 450, 720 480 Z" />
        </g>

        {/* --- LAYER 4: Glowing Floating Embers / Sparks (Bara Api Melayang) --- */}
        <g>
          {/* Embers left */}
          <circle cx="210" cy="380" r="1.8" fill="#FFA439" opacity="0.75" />
          <circle cx="245" cy="320" r="1.2" fill="#FF6B35" opacity="0.65" />
          <circle cx="290" cy="270" r="2.0" fill="#FFC857" opacity="0.70" />
          <circle cx="340" cy="210" r="1.5" fill="#FFA439" opacity="0.60" />
          <circle cx="310" cy="150" r="1.0" fill="#FF6B35" opacity="0.50" />

          {/* Embers center */}
          <circle cx="610" cy="390" r="1.6" fill="#FFA439" opacity="0.80" />
          <circle cx="670" cy="330" r="2.2" fill="#FF6B35" opacity="0.75" />
          <circle cx="640" cy="260" r="1.4" fill="#FFC857" opacity="0.65" />
          <circle cx="710" cy="200" r="1.8" fill="#FFA439" opacity="0.60" />
          <circle cx="680" cy="140" r="1.0" fill="#FF6B35" opacity="0.50" />

          {/* Embers right (under HUD card) */}
          <circle cx="890" cy="410" r="2.2" fill="#FFA439" opacity="0.85" />
          <circle cx="940" cy="350" r="1.6" fill="#FF6B35" opacity="0.75" />
          <circle cx="990" cy="290" r="2.4" fill="#FFC857" opacity="0.80" />
          <circle cx="960" cy="220" r="1.8" fill="#FFA439" opacity="0.70" />
          <circle cx="1030" cy="170" r="1.4" fill="#FF6B35" opacity="0.60" />
          <circle cx="1080" cy="250" r="2.0" fill="#FFA439" opacity="0.75" />
          <circle cx="1140" cy="310" r="1.5" fill="#FFC857" opacity="0.65" />
          <circle cx="1220" cy="360" r="1.8" fill="#FF6B35" opacity="0.70" />
        </g>

        {/* --- LAYER 5: Forest Floor / Peat Ground Baseline --- */}
        <path
          d="M 0 460 Q 360 450 720 458 Q 1080 448 1440 460 L 1440 480 L 0 480 Z"
          fill="var(--ink)"
          fillOpacity="0.18"
        />
      </svg>
    </div>
  );
});
