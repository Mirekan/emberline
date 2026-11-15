import { memo } from "react";

/**
 * Concept 2 + 3: Nighttime Satellite Thermal Composite + Dynamic Ember Atmosphere & Micro-Grain.
 * Pure background layer with zero layout impact: strictly positioned behind existing hero elements.
 */
export const HeroBackdrop = memo(function HeroBackdrop() {
  return (
    <div className="hero-ambient-backdrop" aria-hidden="true">
      {/* 1. Dynamic Atmospheric Thermal Glow Meshes (Concept 3) */}
      <div className="hero-glow-halo hero-glow-halo-hud" />
      <div className="hero-glow-halo hero-glow-halo-center" />
      <div className="hero-glow-halo hero-glow-halo-ambient" />

      {/* 2. Nighttime Satellite Thermal Composite Vector (Concept 2) */}
      <svg
        className="hero-satellite-svg"
        viewBox="0 0 1440 680"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Thermal Sensor Radiant Hotspot Gradients */}
          <radialGradient id="thermalCore" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.95" />
            <stop offset="25%" stopColor="#FFA439" stopOpacity="0.85" />
            <stop offset="55%" stopColor="#FA773F" stopOpacity="0.55" />
            <stop offset="85%" stopColor="#B84218" stopOpacity="0.20" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>

          <radialGradient id="thermalWide" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FF8B82" stopOpacity="0.80" />
            <stop offset="35%" stopColor="#E8763C" stopOpacity="0.45" />
            <stop offset="70%" stopColor="#933310" stopOpacity="0.15" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>

          {/* Archipelago Landmass Gradient */}
          <linearGradient id="landmassGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--ink)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="var(--ink)" stopOpacity="0.06" />
          </linearGradient>

          {/* Satellite Orbital Overpass Beam */}
          <linearGradient id="satelliteSwath" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--ember)" stopOpacity="0" />
            <stop offset="30%" stopColor="var(--ember)" stopOpacity="0.09" />
            <stop offset="70%" stopColor="var(--ember)" stopOpacity="0.09" />
            <stop offset="100%" stopColor="var(--ember)" stopOpacity="0" />
          </linearGradient>

          {/* Micro-grain Noise Filter */}
          <filter id="heroMicroNoise" x="0%" y="0%" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch" />
            <feColorMatrix type="matrix" values="0 0 0 0 0.8  0 0 0 0 0.5  0 0 0 0 0.3  0 0 0 0.045 0" />
          </filter>
        </defs>

        {/* Satellite Night Track Orbital Angle (MODIS & VIIRS Polar Overpass) */}
        <polygon
          points="280,0 480,0 1260,680 1060,680"
          fill="url(#satelliteSwath)"
        />
        <line
          x1="380"
          y1="0"
          x2="1160"
          y2="680"
          stroke="var(--ember)"
          strokeWidth="0.8"
          strokeDasharray="6 8"
          strokeOpacity="0.32"
        />

        {/* Equatorial Baseline Sensor Coordinate Axis */}
        <line
          x1="0"
          y1="340"
          x2="1440"
          y2="340"
          stroke="var(--ink)"
          strokeWidth="0.5"
          strokeDasharray="4 6"
          strokeOpacity="0.10"
        />

        {/* --- GEOSPATIAL INDONESIAN ARCHIPELAGO COMPOSITE --- */}
        <g fill="url(#landmassGrad)" stroke="var(--ink)" strokeWidth="0.6" strokeOpacity="0.14">
          {/* Sumatra Silhouette */}
          <path d="M 210 180 Q 240 195 270 230 Q 300 270 330 320 Q 360 375 390 425 Q 405 450 380 460 Q 355 450 325 390 Q 285 330 250 270 Q 220 220 200 195 Z" />
          
          {/* Peninsular & Riau Islands */}
          <ellipse cx="360" cy="310" rx="22" ry="12" />
          <circle cx="395" cy="335" r="8" />

          {/* Java Silhouette */}
          <path d="M 395 480 Q 450 485 520 495 Q 600 500 660 505 Q 675 515 650 518 Q 580 515 500 510 Q 420 500 390 490 Z" />

          {/* Kalimantan Silhouette */}
          <path d="M 470 260 Q 530 230 600 245 Q 640 280 635 340 Q 610 390 560 415 Q 520 420 485 395 Q 465 350 460 300 Z" />

          {/* Sulawesi Silhouette */}
          <path d="M 680 300 Q 720 290 735 330 Q 710 360 740 410 Q 755 435 730 435 Q 700 395 690 350 Z" />

          {/* Nusa Tenggara / Bali to Timor */}
          <ellipse cx="690" cy="520" rx="14" ry="7" />
          <ellipse cx="730" cy="525" rx="24" ry="8" />
          <ellipse cx="780" cy="530" rx="30" ry="9" />

          {/* Maluku */}
          <ellipse cx="820" cy="330" rx="12" ry="24" />
          <ellipse cx="850" cy="385" rx="22" ry="10" />

          {/* Papua Silhouette */}
          <path d="M 920 360 Q 980 340 1060 350 Q 1140 370 1220 420 Q 1200 460 1140 450 Q 1060 430 980 410 Q 940 395 920 360 Z" />
        </g>

        {/* --- NIGHTTIME SATELLITE SENSOR THERMAL RADIANCE (FIRMS DETECTIONS) --- */}
        {/* 1. Riau Peatland Cluster (0.6°N, 102.0°E) */}
        <g>
          <circle cx="310" cy="285" r="42" fill="url(#thermalWide)" />
          <circle cx="310" cy="285" r="18" fill="url(#thermalCore)" />
          <circle cx="304" cy="280" r="4" fill="#FFFFFF" />
          <circle cx="315" cy="290" r="3" fill="#FFFFFF" />
          <circle cx="320" cy="275" r="2.5" fill="#FFA439" />
        </g>

        {/* 2. Jambi Plantation Frontier Cluster */}
        <g>
          <circle cx="345" cy="340" r="34" fill="url(#thermalWide)" />
          <circle cx="345" cy="340" r="14" fill="url(#thermalCore)" />
          <circle cx="342" cy="338" r="3" fill="#FFFFFF" />
        </g>

        {/* 3. South Sumatra Ogan Komering Cluster */}
        <g>
          <circle cx="375" cy="395" r="48" fill="url(#thermalWide)" />
          <circle cx="375" cy="395" r="22" fill="url(#thermalCore)" />
          <circle cx="370" cy="390" r="4" fill="#FFFFFF" />
          <circle cx="380" cy="402" r="3.5" fill="#FFFFFF" />
          <circle cx="388" cy="385" r="2" fill="#FFA439" />
        </g>

        {/* 4. Central Kalimantan Mega Rice Project Cluster (114°E, 2.5°S) */}
        <g>
          <circle cx="565" cy="360" r="64" fill="url(#thermalWide)" />
          <circle cx="565" cy="360" r="28" fill="url(#thermalCore)" />
          <circle cx="558" cy="352" r="5" fill="#FFFFFF" />
          <circle cx="572" cy="365" r="4" fill="#FFFFFF" />
          <circle cx="580" cy="348" r="3.5" fill="#FFFFFF" />
          <circle cx="548" cy="370" r="3" fill="#FFA439" />
        </g>

        {/* 5. West Kalimantan Ketapang/Pontianak Frontier */}
        <g>
          <circle cx="505" cy="340" r="30" fill="url(#thermalWide)" />
          <circle cx="505" cy="340" r="12" fill="url(#thermalCore)" />
        </g>

        {/* 6. Merauke Savanna Fire Cluster (Papua Selatan) */}
        <g>
          <circle cx="1140" cy="445" r="46" fill="url(#thermalWide)" />
          <circle cx="1140" cy="445" r="20" fill="url(#thermalCore)" />
          <circle cx="1136" cy="442" r="4" fill="#FFFFFF" />
          <circle cx="1145" cy="448" r="3" fill="#FFFFFF" />
        </g>

        {/* Telemetry HUD Labels & Sensor Coordinate Stamps */}
        <g className="hero-backdrop-tags" fill="var(--ink)" fillOpacity="0.32" fontSize="9" fontFamily="var(--font-mono, monospace)">
          <text x="310" y="248" fill="var(--ember)" fillOpacity="0.75">● SENSOR AQUA/MODIS · RIAU PEAT DOME</text>
          <text x="565" y="318" fill="var(--ember)" fillOpacity="0.75">● SENSOR S-NPP/VIIRS · EX-MRP BASIN</text>
          <text x="1140" y="415" fill="var(--ember)" fillOpacity="0.75">● VIIRS 375m · MERAUKE SAVANNA</text>
          <text x="36" y="58">TELEMETRY COMPOSITE · NASA FIRMS ARCHIVE (2000–2026)</text>
          <text x="36" y="74">ORBIT: SUN-SYNCHRONOUS EQUATORIAL SWATH</text>
        </g>

        {/* Tactile Micro-Grain Noise Overlay (Concept 3) */}
        <rect width="100%" height="100%" filter="url(#heroMicroNoise)" />
      </svg>
    </div>
  );
});
