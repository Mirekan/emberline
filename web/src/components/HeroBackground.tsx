import { memo } from "react";

export const HeroBackground = memo(function HeroBackground() {
  return (
    <div className="hero-bg-container" aria-hidden="true">
      {/* 1. Ambient Thermal Glow Aura */}
      <div className="hero-bg-glow hero-bg-glow-right" />
      <div className="hero-bg-glow hero-bg-glow-left" />

      {/* 2. Topographic Elevation Contours & Spatial Grid */}
      <svg
        className="hero-bg-svg"
        viewBox="0 0 1440 680"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="topoGradMajor" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--ember)" stopOpacity="0.16" />
            <stop offset="50%" stopColor="var(--ink)" stopOpacity="0.10" />
            <stop offset="100%" stopColor="var(--ember)" stopOpacity="0.06" />
          </linearGradient>

          <linearGradient id="topoGradMinor" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--ink)" stopOpacity="0.05" />
            <stop offset="60%" stopColor="var(--ink)" stopOpacity="0.03" />
            <stop offset="100%" stopColor="var(--ink)" stopOpacity="0.06" />
          </linearGradient>

          <pattern id="coordGrid" width="120" height="120" patternUnits="userSpaceOnUse">
            <path d="M 120 0 L 0 0 0 120" fill="none" stroke="var(--ink)" strokeWidth="0.5" strokeOpacity="0.025" />
            <circle cx="0" cy="0" r="1.5" fill="var(--ember)" fillOpacity="0.25" />
          </pattern>
        </defs>

        {/* Coordinate Grid Background */}
        <rect width="100%" height="100%" fill="url(#coordGrid)" />

        {/* Contour Isolines - Peatland Basin Elevation Model */}
        {/* Ridge Layer 1 (Outer Deep Contour) */}
        <path
          d="M -40 220 C 180 180, 360 260, 560 220 C 760 180, 940 90, 1140 120 C 1300 144, 1420 220, 1500 240"
          stroke="url(#topoGradMajor)"
          strokeWidth="1.2"
          strokeDasharray="4 6"
        />
        
        {/* Ridge Layer 2 (Primary Index Contour) */}
        <path
          d="M -60 290 C 160 250, 320 340, 540 300 C 740 260, 920 160, 1120 180 C 1280 196, 1400 300, 1520 330"
          stroke="url(#topoGradMajor)"
          strokeWidth="1.4"
        />

        {/* Ridge Layer 3 (Intermediate) */}
        <path
          d="M -40 360 C 200 320, 380 410, 600 360 C 800 310, 960 240, 1160 260 C 1320 276, 1420 390, 1500 410"
          stroke="url(#topoGradMinor)"
          strokeWidth="0.9"
        />

        {/* Ridge Layer 4 (Lower Peatland Basin) */}
        <path
          d="M -60 440 C 220 390, 420 480, 640 430 C 840 380, 1000 320, 1200 330 C 1340 338, 1440 460, 1520 480"
          stroke="url(#topoGradMajor)"
          strokeWidth="1.2"
        />

        {/* Ridge Layer 5 (Bottom Sub-basin) */}
        <path
          d="M -40 520 C 240 470, 460 550, 680 500 C 880 450, 1040 390, 1240 400 C 1380 408, 1460 540, 1520 560"
          stroke="url(#topoGradMinor)"
          strokeWidth="0.8"
          strokeDasharray="6 8"
        />

        {/* Ridge Layer 6 (Foot Ridge) */}
        <path
          d="M -60 600 C 260 550, 500 620, 720 570 C 920 520, 1080 470, 1280 480 C 1400 486, 1480 610, 1540 630"
          stroke="url(#topoGradMajor)"
          strokeWidth="1.1"
        />

        {/* Secondary Contour Loops (Terrain Swells) */}
        <path
          d="M 880 200 C 960 170, 1060 160, 1120 190 C 1180 220, 1160 260, 1090 270 C 1020 280, 920 270, 870 240 C 840 220, 850 210, 880 200 Z"
          stroke="url(#topoGradMajor)"
          strokeWidth="1.2"
        />
        <path
          d="M 920 215 C 970 195, 1030 190, 1080 210 C 1120 226, 1110 248, 1060 255 C 1010 262, 940 252, 915 238 C 900 230, 905 220, 920 215 Z"
          stroke="url(#topoGradMinor)"
          strokeWidth="0.8"
        />

        {/* Geospatial Coordinate & Elevation Stamp Annotations */}
        <g className="hero-bg-labels" fill="var(--ink)" fillOpacity="0.28" fontSize="8.5" fontFamily="var(--font-mono, monospace)">
          <text x="36" y="70">GEO-SPATIAL ELEVATION BASELINE · 0.1° TILE SYSTEM</text>
          <text x="36" y="86">DATUM: WGS-84 / EQUATORIAL PEATLAND COMPLEX</text>
          
          <text x="575" y="215" fill="var(--ember)" fillOpacity="0.45">+140m</text>
          <text x="555" y="295">+100m</text>
          <text x="615" y="355">+60m</text>
          <text x="655" y="425">+20m (PEAT BASIN)</text>
          
          <text x="1140" y="650">COORDINATE AXIS · REF: 00°45′S 101°30′E</text>
        </g>

        {/* Target Reticle Crosshairs */}
        <g stroke="var(--ember)" strokeWidth="1" strokeOpacity="0.35">
          {/* Top Right Reticle */}
          <line x1="1340" y1="40" x2="1360" y2="40" />
          <line x1="1350" y1="30" x2="1350" y2="50" />
          <circle cx="1350" cy="40" r="16" fill="none" strokeWidth="0.6" strokeDasharray="3 3" />

          {/* Bottom Left Reticle */}
          <line x1="80" y1="620" x2="100" y2="620" />
          <line x1="90" y1="610" x2="90" y2="630" />
          <circle cx="90" cy="620" r="12" fill="none" strokeWidth="0.6" strokeDasharray="2 2" />
        </g>
      </svg>
    </div>
  );
});
