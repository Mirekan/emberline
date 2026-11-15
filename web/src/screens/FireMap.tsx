import { useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api, Preset, Detections, Detection, Grid, GridCell } from "../api";
import { useAoi } from "../App";

const REGIONS: { name: string; center: [number, number]; preset?: string }[] = [
  { name: "Kalimantan Tengah", center: [-1.8, 113.8], preset: "central_kalimantan" },
  { name: "Riau", center: [0.6, 102.0], preset: "riau" },
  { name: "Sumatera Selatan", center: [-3.3, 104.6], preset: "south_sumatra" },
  { name: "Jambi", center: [-1.8, 103.0], preset: "jambi" },
  { name: "Papua Selatan (Merauke)", center: [-8.0, 139.0], preset: "merauke" },
  { name: "Aceh", center: [4.6, 96.7] },
  { name: "Sumatera Utara", center: [2.2, 98.7] },
  { name: "Kepulauan Riau", center: [0.9, 104.5] },
  { name: "Bangka Belitung", center: [-2.5, 106.0] },
  { name: "Kalimantan Barat", center: [0.2, 109.5] },
  { name: "Kalimantan Selatan", center: [-3.0, 115.5] },
  { name: "Kalimantan Timur", center: [0.5, 116.5] },
  { name: "Kalimantan Utara", center: [2.5, 116.8] },
  { name: "Sulawesi Utara", center: [0.9, 124.2] },
  { name: "Gorontalo", center: [0.6, 122.4] },
  { name: "Sulawesi Tengah", center: [-1.4, 120.4] },
  { name: "Sulawesi Selatan", center: [-3.8, 119.9] },
  { name: "Maluku Utara", center: [1.6, 127.6] },
  { name: "Papua", center: [-4.0, 138.5] },
];

export type IslandRegion = {
  id: string;
  name: string;
  shortName: string;
  center: [number, number];
  zoom: number;
  bounds: L.LatLngBoundsLiteral;
  polygon: [number, number][];
  defaultPreset?: string;
  defaultProvince: string;
  provinces: string[];
};

export const ISLANDS: IslandRegion[] = [
  {
    id: "sumatera",
    name: "Pulau Sumatera",
    shortName: "Sumatera",
    center: [0.5, 101.8],
    zoom: 6,
    bounds: [[5.9, 95.0], [-6.0, 106.0]],
    polygon: [
      [5.9, 95.2], [5.3, 96.0], [4.0, 98.4], [2.2, 100.3], [1.6, 101.6],
      [1.2, 103.0], [0.8, 104.2], [-1.2, 104.5], [-3.2, 106.0], [-5.8, 105.8],
      [-5.9, 104.4], [-4.2, 102.7], [-2.3, 100.8], [-0.5, 98.7], [2.0, 97.0],
      [5.4, 95.2]
    ],
    defaultPreset: "riau",
    defaultProvince: "Riau",
    provinces: ["Aceh", "Sumatera Utara", "Riau", "Kepulauan Riau", "Jambi", "Sumatera Selatan", "Bangka Belitung"]
  },
  {
    id: "kalimantan",
    name: "Pulau Kalimantan",
    shortName: "Kalimantan",
    center: [-1.4, 113.8],
    zoom: 6,
    bounds: [[4.3, 108.8], [-4.3, 117.8]],
    polygon: [
      [4.3, 117.6], [2.1, 117.9], [0.8, 118.0], [-1.3, 117.1], [-3.7, 116.3],
      [-4.2, 114.6], [-3.5, 112.5], [-3.0, 110.5], [-1.8, 109.9], [0.8, 108.9],
      [2.1, 109.3], [1.3, 112.0], [1.7, 115.5], [3.8, 115.8], [4.3, 117.6]
    ],
    defaultPreset: "central_kalimantan",
    defaultProvince: "Kalimantan Tengah",
    provinces: ["Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara"]
  },
  {
    id: "jawa",
    name: "Pulau Jawa",
    shortName: "Jawa",
    center: [-7.3, 110.0],
    zoom: 7,
    bounds: [[-5.8, 105.1], [-8.9, 114.6]],
    polygon: [
      [-5.9, 106.0], [-6.1, 106.9], [-6.4, 108.5], [-6.8, 110.5], [-6.9, 112.6],
      [-7.0, 114.1], [-7.7, 114.5], [-8.6, 114.4], [-8.4, 112.5], [-8.2, 110.5],
      [-7.8, 108.5], [-7.0, 106.5], [-6.7, 105.2], [-5.9, 106.0]
    ],
    defaultProvince: "Jawa Timur",
    provinces: ["Banten", "DKI Jakarta", "Jawa Barat", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur"]
  },
  {
    id: "sulawesi",
    name: "Pulau Sulawesi",
    shortName: "Sulawesi",
    center: [-1.8, 121.0],
    zoom: 6,
    bounds: [[2.0, 118.5], [-6.0, 125.5]],
    polygon: [
      [1.8, 125.0], [0.8, 124.0], [0.9, 121.0], [1.4, 120.8], [-1.0, 119.3],
      [-3.5, 118.8], [-5.6, 119.5], [-5.5, 120.6], [-3.0, 120.4], [-3.0, 121.5],
      [-5.3, 122.8], [-3.7, 122.7], [-1.6, 123.6], [-0.5, 123.3], [-0.3, 120.5],
      [0.8, 121.5], [1.8, 125.0]
    ],
    defaultProvince: "Sulawesi Tengah",
    provinces: ["Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Barat", "Sulawesi Tenggara"]
  },
  {
    id: "bali_nusa",
    name: "Bali & Nusa Tenggara",
    shortName: "Bali & Nusa",
    center: [-8.6, 119.5],
    zoom: 7,
    bounds: [[-8.0, 114.4], [-11.0, 125.2]],
    polygon: [
      [-8.0, 114.5], [-8.1, 115.7], [-8.2, 117.0], [-8.2, 119.0], [-8.2, 121.0],
      [-8.2, 123.5], [-8.3, 125.2], [-9.5, 125.1], [-10.5, 124.0], [-10.8, 123.0],
      [-10.0, 120.0], [-9.0, 118.0], [-9.0, 116.0], [-8.8, 114.5], [-8.0, 114.5]
    ],
    defaultProvince: "Bali",
    provinces: ["Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"]
  },
  {
    id: "maluku",
    name: "Kepulauan Maluku",
    shortName: "Maluku",
    center: [-2.5, 129.5],
    zoom: 6,
    bounds: [[3.0, 125.5], [-8.5, 135.0]],
    polygon: [
      [2.8, 127.5], [2.0, 128.8], [-0.5, 128.5], [-1.8, 130.0], [-3.2, 131.0],
      [-5.5, 132.5], [-7.5, 132.0], [-8.3, 131.0], [-7.5, 128.5], [-4.0, 126.5],
      [-2.0, 125.5], [0.5, 127.0], [2.8, 127.5]
    ],
    defaultProvince: "Maluku Utara",
    provinces: ["Maluku", "Maluku Utara"]
  },
  {
    id: "papua",
    name: "Pulau Papua",
    shortName: "Papua",
    center: [-4.0, 136.0],
    zoom: 6,
    bounds: [[0.0, 130.5], [-9.2, 141.0]],
    polygon: [
      [-0.5, 131.0], [-0.8, 134.0], [-2.3, 135.0], [-1.8, 138.5], [-2.5, 141.0],
      [-9.1, 141.0], [-8.3, 138.5], [-5.0, 138.0], [-4.8, 135.5], [-3.8, 133.5],
      [-4.0, 132.0], [-2.8, 132.0], [-1.5, 130.5], [-0.5, 131.0]
    ],
    defaultProvince: "Papua",
    provinces: ["Papua", "Papua Selatan", "Papua Barat", "Papua Tengah", "Papua Pegunungan"]
  }
];

// Indonesia Territorial Bounds (Sabang to Merauke, Miangas to Rote)
// Formatted with widescreen 16:9 margin so fullscreen viewports never collide with bounds constraints
const INDONESIA_BOUNDS: L.LatLngBoundsLiteral = [
  [12.0, 92.0],   // North-West
  [-13.5, 143.5], // South-East
];

export default function FireMap() {
  const { aoi, setAoi, calFilter, lang, t } = useAoi();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapEl = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const canvasRendererRef = useRef<L.Canvas | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const gridLayerRef = useRef<L.LayerGroup | null>(null);
  const dotsLayerRef = useRef<L.LayerGroup | null>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const coordRef = useRef<HTMLSpanElement>(null);

  const PRESET_NAMES: Record<string, string> = {
    central_kalimantan: "Kalimantan Tengah",
    riau: "Riau",
    south_sumatra: "Sumatera Selatan",
    jambi: "Jambi",
    merauke: "Papua Selatan (Merauke)",
  };

  const [q, setQ] = useState("");
  const [selName, setSelName] = useState<string | null>(() => {
    return PRESET_NAMES[aoi] ?? "Kalimantan Tengah";
  });
  const [presets, setPresets] = useState<Preset[]>([]);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [gridOn, setGridOn] = useState(false); // Default OFF so the map shows clean topography and fire dots
  const [gridLoading, setGridLoading] = useState(false);
  const [gridError, setGridError] = useState("");
  const [selectedCell, setSelectedCell] = useState<GridCell | null>(null);
  const [det, setDet] = useState<Detections | null>(null);
  const [detOn, setDetOn] = useState(true); // Default ON: FIRMS dots are immediately rendered on map load
  const [detLoading, setDetLoading] = useState(false);
  const [detError, setDetError] = useState("");
  const [detYear, setDetYear] = useState("2026"); // Default to 2026 on initial load to prevent overcrowding
  const [detSensor, setDetSensor] = useState<"all" | "modis" | "viirs">("all");
  const [isFs, setIsFs] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mapReady, setMapReady] = useState(false);

  const visibleRowsRef = useRef<Detection[]>([]);

  useEffect(() => {
    api.presets().then(r => setPresets(r.presets)).catch(() => {});
  }, []);

  // Isolate UI controls from Leaflet wheel zoom & click propagation
  useEffect(() => {
    if (sidebarRef.current) {
      L.DomEvent.disableScrollPropagation(sidebarRef.current);
      L.DomEvent.disableClickPropagation(sidebarRef.current);
    }
  }, [sidebarOpen]);

  useEffect(() => {
    if (toolbarRef.current) {
      L.DomEvent.disableScrollPropagation(toolbarRef.current);
      L.DomEvent.disableClickPropagation(toolbarRef.current);
    }
  }, []);

  // Sync selected region name when global AOI changes
  useEffect(() => {
    if (PRESET_NAMES[aoi] && PRESET_NAMES[aoi] !== selName) {
      setSelName(PRESET_NAMES[aoi]);
    }
  }, [aoi]);

  // Fullscreen event listener to dynamically resize the map
  useEffect(() => {
    const onFsChange = () => {
      const fs = !!document.fullscreenElement;
      setIsFs(fs);
      setTimeout(() => {
        mapRef.current?.invalidateSize({ pan: false });
      }, 100);
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  // Determine initial coordinates: focused on active province or whole Indonesia
  const getInitialCoords = (): { center: [number, number]; zoom: number } => {
    if (aoi === "central_kalimantan") return { center: [-1.8, 113.8], zoom: 7 };
    if (aoi === "south_sumatra") return { center: [-3.3, 104.6], zoom: 7 };
    if (aoi === "jambi") return { center: [-1.8, 103.0], zoom: 7 };
    if (aoi === "riau") return { center: [0.6, 102.0], zoom: 7 };
    if (aoi === "merauke") return { center: [-8.0, 139.0], zoom: 7 };
    return { center: [-2.5, 118.0], zoom: 5 }; // Whole Indonesia center
  };

  // Initialize Map locked to Indonesia territory (no global wander, seamless tiles)
  useEffect(() => {
    if (!mapEl.current || mapRef.current) return;

    const { center, zoom } = getInitialCoords();

    // High-performance Canvas renderer: single GPU buffer, zero lag in full screen,
    // padding 0.5 prevents canvas re-draws during pan gestures within 50% margin
    const canvasRenderer = L.canvas({ padding: 0.5 });
    canvasRendererRef.current = canvasRenderer;

    const map = L.map(mapEl.current, {
      center,
      zoom,
      zoomControl: false,
      attributionControl: true,
      minZoom: 5,
      maxZoom: 13,
      maxBounds: INDONESIA_BOUNDS,
      maxBoundsViscosity: 0.5, // Gentle elastic resistance: prevents rubber-band fighting in fullscreen 16:9
      zoomAnimation: true,
      zoomAnimationThreshold: 4,
      fadeAnimation: true,
      markerZoomAnimation: true,
      zoomSnap: 1,
      zoomDelta: 1,
      wheelPxPerZoomLevel: 120,
      wheelDebounceTime: 40,
      renderer: canvasRenderer,
    });

    L.control.zoom({ position: "topright" }).addTo(map);

    // Fast Topography basemap (OpenStreetMap) with 3-tile buffer
    const tileLayer = L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 13,
        minZoom: 5,
        keepBuffer: 3,           // Fast 3-tile buffer: massive performance gain on fullscreen displays
        updateWhenZooming: false,
        updateWhenIdle: true,    // Zero network thrash during continuous drag
      }
    ).addTo(map);

    tileLayerRef.current = tileLayer;
    mapRef.current = map;
    setMapReady(true);

    // Track mouse coordinates directly via DOM ref & requestAnimationFrame
    // Eliminates 100% of React re-renders during mouse movement across fullscreen!
    let rafCoord: number | null = null;
    map.on("mousemove", (e) => {
      if (rafCoord) return;
      rafCoord = window.requestAnimationFrame(() => {
        if (coordRef.current) {
          coordRef.current.textContent = `Lat: ${e.latlng.lat.toFixed(5)}° · Lon: ${e.latlng.lng.toFixed(5)}°`;
        }
        rafCoord = null;
      });
    });

    map.on("mouseout", () => {
      if (coordRef.current) {
        coordRef.current.textContent = "Arahkan kursor ke peta untuk koordinat";
      }
    });

    // Instant click inspector (finds nearest dot within 24px)
    map.on("click", (e) => {
      const rows = visibleRowsRef.current;
      if (!rows || rows.length === 0) return;

      const clickPt = map.latLngToContainerPoint(e.latlng);
      let nearest: Detection | null = null;
      let minDist = 24;

      for (let i = 0; i < rows.length; i++) {
        const d = rows[i];
        const pt = map.latLngToContainerPoint([d.lat, d.lon]);
        const dist = Math.hypot(pt.x - clickPt.x, pt.y - clickPt.y);
        if (dist < minDist) {
          minDist = dist;
          nearest = d;
        }
      }

      if (nearest) {
        const isViirs = nearest.sensor === "viirs";
        L.popup({ autoPan: false, closeButton: true })
          .setLatLng([nearest.lat, nearest.lon])
          .setContent(
            `<div style="font-size:12px; min-width:200px; line-height:1.5; font-family:var(--font-sans, system-ui);">
              <div style="font-weight:700; color:${isViirs ? "#EF4444" : "#2563EB"}; margin-bottom:4px; display:flex; align-items:center; justify-content:space-between;">
                <span>${isViirs ? "VIIRS 375m (S-NPP)" : "MODIS 1km (Aqua)"}</span>
                <span style="font-size:10px; padding:1px 6px; background:rgba(128,128,128,0.15); border-radius:4px; font-weight:600;">Conf: ${nearest.conf}</span>
              </div>
              <div style="font-size:12px;">FRP: <b>${nearest.frp.toFixed(2)} MW</b></div>
              <div style="font-size:11.5px; color:#666;">${nearest.date} · ${nearest.daynight === "D" ? "Day overpass" : "Night overpass"}</div>
              <div style="font-size:11px; font-family:monospace; color:#222; background:rgba(0,0,0,0.06); padding:2px 6px; border-radius:4px; margin-top:4px;">
                Lat: <b>${nearest.lat.toFixed(5)}°</b> · Lon: <b>${nearest.lon.toFixed(5)}°</b>
              </div>
              <div style="font-size:10px; color:#22c55e; font-weight:600; margin-top:4px;">
                Presisi koordinat FIRMS (${isViirs ? "375 m" : "1.000 m"})
              </div>
              <div style="font-size:10px; color:#888; margin-top:4px; border-top:1px dashed rgba(128,128,128,0.3); padding-top:4px; line-height:1.3;">
                Piksel observasi satelit — bukan klaim batas fisik kebakaran.
              </div>
            </div>`
          )
          .openOn(map);
      }
    });

    let resizeTimer: ReturnType<typeof setTimeout>;
    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        map.invalidateSize({ pan: false });
      }, 100);
    };

    window.addEventListener("resize", onResize);
    return () => {
      if (rafCoord) window.cancelAnimationFrame(rafCoord);
      window.removeEventListener("resize", onResize);
      clearTimeout(resizeTimer);
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);

  // Load the density grid overlay
  useEffect(() => {
    let cancelled = false;
    const targetAoi = selName === null ? "all" : aoi;
    setGrid(null);
    setGridError("");
    setGridLoading(true);
    api.grid(targetAoi)
      .then(data => {
        if (!cancelled) setGrid(data);
      })
      .catch(error => {
        if (!cancelled) {
          setGridError(error instanceof Error ? error.message : "Gagal memuat intensitas peta.");
        }
      })
      .finally(() => {
        if (!cancelled) setGridLoading(false);
      });
    return () => { cancelled = true; };
  }, [aoi, selName]);

  // Load satellite hotspot detections across the entire active region
  useEffect(() => {
    let cancelled = false;
    const targetAoi = selName === null ? "all" : aoi;
    setDet(null);
    setDetError("");
    setDetLoading(true);
    api.detections(targetAoi)
      .then(data => {
        if (!cancelled) setDet(data);
      })
      .catch(error => {
        if (!cancelled) {
          setDetError(error instanceof Error ? error.message : "Gagal memuat titik satelit.");
        }
      })
      .finally(() => {
        if (!cancelled) setDetLoading(false);
      });
    return () => { cancelled = true; };
  }, [aoi, selName]);

function getCellRisk(count: number, maxCount: number): { label: "Aman" | "Waspada" | "Siaga" | "Bahaya"; color: string; bg: string } {
  if (count === 0) {
    return { label: "Aman", color: "#10B981", bg: "rgba(16, 185, 129, 0.15)" };
  }
  const intensity = maxCount > 0 ? Math.log1p(count) / Math.log1p(maxCount) : 0;
  if (intensity < 0.33) {
    return { label: "Waspada", color: "#FACC15", bg: "rgba(250, 204, 21, 0.2)" };
  }
  if (intensity < 0.66) {
    return { label: "Siaga", color: "#F97316", bg: "rgba(249, 115, 22, 0.25)" };
  }
  return { label: "Bahaya", color: "#EF4444", bg: "rgba(239, 68, 68, 0.32)" };
}

  const maxCount = useMemo(() => {
    return grid && grid.cells.length > 0 ? Math.max(0, ...grid.cells.map(c => c.detection_count)) : 0;
  }, [grid]);

  // Render 0.1° density grid overlay when toggled on
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    gridLayerRef.current?.remove();
    gridLayerRef.current = null;
    if (!gridOn || !grid || grid.cells.length === 0) return;

    const layer = L.layerGroup();
    for (const cell of grid.cells) {
      const count = cell.detection_count;
      const isSelected = selectedCell?.cell_id === cell.cell_id;
      if (count === 0 && !isSelected) continue; // Skip empty cells unless selected
      const risk = getCellRisk(count, maxCount);

      const area = L.rectangle(
        [[cell.south, cell.west], [cell.north, cell.east]],
        {
          color: isSelected ? "#FFFFFF" : risk.color,
          weight: isSelected ? 2.5 : 0.6,
          fillColor: risk.color,
          fillOpacity: isSelected ? 0.45 : count === 0 ? 0.04 : 0.16 + (maxCount > 0 ? (Math.log1p(count) / Math.log1p(maxCount)) * 0.32 : 0),
          interactive: true,
          bubblingMouseEvents: false,
        },
      );
      area.bindTooltip(
        `<div style="font-size:11px; line-height:1.4;">
          <div style="font-weight:700; color:${risk.color}; margin-bottom:2px;">Status: ${risk.label}</div>
          <div>${count.toLocaleString()} observasi satelit</div>
          <div style="font-size:10px; color:#888;">Klik untuk fokus sel</div>
        </div>`,
        { sticky: true }
      );
      area.on("click", (e) => {
        L.DomEvent.stopPropagation(e);
        setSelectedCell(prev => {
          if (prev?.cell_id === cell.cell_id) {
            const p = presets.find(pp => pp.id === aoi);
            if (p) {
              map.flyToBounds([[p.south, p.west], [p.north, p.east]], { padding: [50, 50], duration: 0.8 });
            }
            return null;
          } else {
            map.flyToBounds([[cell.south, cell.west], [cell.north, cell.east]], {
              padding: [80, 80],
              maxZoom: 11,
              duration: 0.8,
            });
            return cell;
          }
        });
      });
      area.addTo(layer);
    }
    layer.addTo(map);
    gridLayerRef.current = layer;
  }, [grid, gridOn, selectedCell, maxCount, mapReady, aoi, presets]);

  const detRows = useMemo(() => {
    if (!det) return [];
    return det.detections.filter(d => {
      const matchTime = (detYear === "all" || d.date.startsWith(detYear));
      const matchSensor = (detSensor === "all" || d.sensor === detSensor);
      if (!matchTime || !matchSensor) return false;
      if (selectedCell) {
        return (
          d.lat >= selectedCell.south &&
          d.lat <= selectedCell.north &&
          d.lon >= selectedCell.west &&
          d.lon <= selectedCell.east
        );
      }
      return true;
    });
  }, [det, detYear, detSensor, selectedCell]);

  const detYears = useMemo(() => {
    if (!det) return [];
    return [...new Set(det.detections.map(d => d.date.slice(0, 4)))].sort((a, b) => b.localeCompare(a));
  }, [det]);

  // Render satellite detection dots at their true geographic coordinates
  useEffect(() => {
    const map = mapRef.current;
    const canvasRenderer = canvasRendererRef.current;
    if (!map || !canvasRenderer) return;

    if (dotsLayerRef.current) {
      dotsLayerRef.current.remove();
      dotsLayerRef.current = null;
    }

    if (!det || !detOn) {
      visibleRowsRef.current = [];
      return;
    }

    const rows = detRows;

    // Limit to 2,500 highest FRP points when "all" years are selected for smooth GPU rendering
    const cappedRows = rows.length > 2500
      ? [...rows].sort((a, b) => b.frp - a.frp).slice(0, 2500)
      : rows;

    visibleRowsRef.current = cappedRows;

    const maxFrp = Math.max(0, ...cappedRows.map(d => d.frp));
    const g = L.layerGroup();

    for (let i = 0; i < cappedRows.length; i++) {
      const d = cappedRows[i];
      const t = maxFrp > 0 ? Math.min(1, d.frp / maxFrp) : 0;
      const isViirs = d.sensor === "viirs";

      L.circleMarker([d.lat, d.lon], {
        renderer: canvasRenderer,
        radius: isViirs ? (2.8 + Math.sqrt(t) * 2.2) : (4.0 + Math.sqrt(t) * 2.5),
        color: "#FFFFFF",
        weight: 0.6,
        fillColor: isViirs ? "#EF4444" : "#2563EB",
        fillOpacity: 0.88,
        interactive: false,
      }).addTo(g);
    }

    g.addTo(map);
    dotsLayerRef.current = g;
  }, [det, detOn, detRows, mapReady]);

  // Smoothly pan only when user explicitly switches AOI preset
  const lastAoiRef = useRef<string>(aoi);
  useEffect(() => {
    if (lastAoiRef.current !== aoi && mapRef.current) {
      lastAoiRef.current = aoi;
      setSelectedCell(null);
      const p = presets.find(pp => pp.id === aoi);
      if (p) {
        mapRef.current.flyToBounds([[p.south, p.west], [p.north, p.east]], {
          padding: [50, 50],
          duration: 0.9,
        });
      }
    }
  }, [aoi, presets]);

  const flyTo = (r: (typeof REGIONS)[number]) => {
    setSelName(r.name);
    if (r.preset) {
      lastAoiRef.current = r.preset;
      setAoi(r.preset);
      const p = presets.find(pp => pp.id === r.preset);
      if (p) {
        mapRef.current?.flyToBounds([[p.south, p.west], [p.north, p.east]], {
          padding: [50, 50],
          duration: 0.9,
        });
        return;
      }
    }
    mapRef.current?.flyTo(r.center, 7, { duration: 0.8 });
  };

  const list = useMemo(() => {
    return REGIONS.filter(r => r.name.toLowerCase().includes(q.toLowerCase()));
  }, [q]);
  const chipFor = (r: (typeof REGIONS)[number]) => {
    const p = presets.find(pp => pp.id === r.preset);
    if (!p) return null;
    return p.artifact_status === "available" ? t("map_status_ready") : t("map_status_queued");
  };
  const curPreset = presets.find(p => p.id === aoi);

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        height: isFs ? "100vh" : "calc(100vh - 104px)",
        minHeight: isFs ? "100vh" : 520,
        overflow: "hidden",
        background: "var(--bg)",
      }}
    >
      {/* Base Map Container */}
      <div ref={mapEl} style={{ position: "absolute", inset: 0 }} />

      {/* Floating Control Toolbar */}
      <div
        ref={toolbarRef}
        style={{
          position: "absolute",
          top: 80,
          right: 10,
          zIndex: 900,
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <button
          type="button"
          onClick={toggleFullscreen}
          className="seg-btn"
          style={{
            background: "var(--surface)",
            boxShadow: "var(--shadow-sm)",
            padding: "6px 10px",
            fontSize: 11,
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
          title={isFs ? t("map_exit_fullscreen") : t("map_fullscreen")}
        >
          {isFs ? t("map_exit_fullscreen") : t("map_fullscreen")}
        </button>

        <button
          type="button"
          onClick={() => setSidebarOpen(s => !s)}
          className="seg-btn"
          style={{
            background: "var(--surface)",
            boxShadow: "var(--shadow-sm)",
            padding: "6px 10px",
            fontSize: 11,
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
          title={sidebarOpen ? t("map_close_panel") : t("map_open_panel")}
        >
          {sidebarOpen ? t("map_close_panel") : t("map_open_panel")}
        </button>

        <button
          type="button"
          onClick={() => setDetOn(o => !o)}
          className={"seg-btn" + (detOn ? " active" : "")}
          style={{
            background: detOn ? "var(--ember-sub)" : "var(--surface)",
            color: detOn ? "var(--ember)" : "var(--ink)",
            borderColor: detOn ? "var(--ember-border)" : "var(--line)",
            boxShadow: "var(--shadow-sm)",
            padding: "6px 10px",
            fontSize: 11,
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
          aria-pressed={detOn}
          title={detOn ? "Sembunyikan titik satelit FIRMS" : "Tampilkan titik satelit FIRMS"}
        >
          {detOn ? "Titik Satelit: Aktif" : "Titik Satelit: Nonaktif"}
        </button>

        <button
          type="button"
          onClick={() => setGridOn(g => !g)}
          className={"seg-btn" + (gridOn ? " active" : "")}
          style={{
            background: gridOn ? "var(--ember-sub)" : "var(--surface)",
            color: gridOn ? "var(--ember)" : "var(--ink)",
            borderColor: gridOn ? "var(--ember-border)" : "var(--line)",
            boxShadow: "var(--shadow-sm)",
            padding: "6px 10px",
            fontSize: 11,
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
          aria-pressed={gridOn}
          title={gridOn ? "Sembunyikan grid kepadatan 0,1°" : "Tampilkan grid kepadatan 0,1°"}
        >
          {gridOn ? "Grid 0,1°: Aktif" : "Grid 0,1°: Nonaktif"}
        </button>
      </div>

      {/* Floating Toggle Button when Sidebar is Closed */}
      {!sidebarOpen && (
        <button
          type="button"
          onClick={() => setSidebarOpen(true)}
          className="seg-btn"
          style={{
            position: "absolute",
            left: 16,
            top: 16,
            zIndex: 900,
            background: "var(--surface)",
            boxShadow: "var(--shadow-md)",
            padding: "8px 14px",
            fontSize: 12,
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          {t("map_filter_btn")}
        </button>
      )}

      {/* Floating Sidebar Filter */}
      <div
        ref={sidebarRef}
        style={{
          position: "absolute",
          left: 16,
          top: 16,
          bottom: 48,
          width: 320,
          background: "var(--surface)",
          borderRadius: 12,
          border: "1px solid var(--line)",
          boxShadow: "var(--shadow-md)",
          display: sidebarOpen ? "flex" : "none",
          flexDirection: "column",
          zIndex: 900,
        }}
      >
        <div style={{ padding: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--ink2)" }}>
              {t("map_filter_title")}
            </span>
            <div style={{ display: "flex", gap: 4 }}>
              <button
                type="button"
                className={"seg-btn" + (selName === null ? " active" : "")}
                style={{ fontSize: 10.5, padding: "2px 8px" }}
                onClick={() => {
                  setSelName(null);
                  mapRef.current?.fitBounds([[6.0, 95.0], [-11.0, 141.0]], { padding: [30, 30] });
                }}
                title={lang === "id" ? "Fokus ke seluruh kepulauan Indonesia" : "Focus on all Indonesian archipelago"}
              >
                {t("map_all_regions")}
              </button>
              <button
                type="button"
                className="seg-btn"
                style={{ fontSize: 10.5, padding: "2px 8px" }}
                onClick={() => setSidebarOpen(false)}
                title={lang === "id" ? "Sembunyikan panel ini" : "Hide this panel"}
              >
                {t("map_inspector_close")}
              </button>
            </div>
          </div>
          <input
            type="text"
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder={t("map_search_placeholder")}
            style={{ width: "100%", borderRadius: 8, padding: "8px 12px" }}
          />
        </div>

        {calFilter && (
          <div style={{
            margin: "0 14px 8px", fontSize: 11.5, color: "var(--ember)",
            background: "var(--ember-sub)", border: "1px solid var(--ember-border)",
            borderRadius: 8, padding: "6px 10px",
          }}>
            Temporal calendar scope: <b>{calFilter}</b>
          </div>
        )}

        {(gridLoading || gridError) && (
          <div style={{
            margin: "0 14px 8px", fontSize: 10.5, color: gridError ? "var(--danger, #dc2626)" : "var(--ink2)",
            background: "var(--sunken)", border: "1px solid var(--line)",
            borderRadius: 8, padding: "6px 10px",
          }}>
            {gridError ? `Intensitas peta gagal dimuat: ${gridError}` : "Memuat intensitas observasi per area…"}
          </div>
        )}

        {/* Titik Satelit FIRMS Control Card */}
        <div style={{
          margin: "0 14px 8px", padding: 10,
          background: "var(--sunken)", borderRadius: 8, border: "1px solid var(--line)",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--ink)" }}>
              Titik Satelit FIRMS
            </span>
            <button
              type="button"
              className={"seg-btn" + (detOn ? " active" : "")}
              onClick={() => setDetOn(o => !o)}
              aria-pressed={detOn}
              style={{
                background: detOn ? "var(--ember-sub)" : "var(--surface)",
                color: detOn ? "var(--ember)" : "var(--ink)",
                fontWeight: 600,
                fontSize: 11,
                padding: "3px 10px",
              }}
              title={detOn ? "Sembunyikan titik satelit" : "Tampilkan titik satelit"}
            >
              {detOn ? "Ditampilkan" : "Disembunyikan"}
            </button>
          </div>

          {!detOn ? (
            <div style={{ fontSize: 10.5, color: "var(--ink3)", lineHeight: 1.4 }}>
              Lapisan titik satelit dinonaktifkan.
            </div>
          ) : detLoading ? (
            <div style={{ fontSize: 10.5, color: "var(--ink3)" }}>Memuat titik satelit…</div>
          ) : detError ? (
            <div role="alert" style={{ fontSize: 10.5, color: "var(--danger, #dc2626)", lineHeight: 1.4 }}>
              Titik satelit gagal dimuat: {detError}
            </div>
          ) : det ? (
            <>
              <div style={{ fontSize: 10.5, color: "var(--ink2)", marginBottom: 7 }}>
                {selectedCell
                  ? `${detRows.length.toLocaleString()} titik dalam sel ${selectedCell.cell_id} (${detYear === "all" ? "Semua tahun" : `Tahun ${detYear}`})`
                  : `${detRows.length.toLocaleString()} observasi titik satelit (${detYear === "all" ? "Semua tahun" : `Tahun ${detYear}`})`}
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <select
                  className="glass-select"
                  value={detYear}
                  style={{ flex: 1, minWidth: 0 }}
                  onChange={e => setDetYear(e.target.value)}
                >
                  <option value="all">{t("map_time_all")}</option>
                  {detYears.map(y => (
                    <option key={y} value={y}>{lang === "id" ? `Tahun ${y}` : `Year ${y}`}</option>
                  ))}
                </select>
                <select
                  className="glass-select"
                  value={detSensor}
                  style={{ flex: 1, minWidth: 0 }}
                  onChange={e => setDetSensor(e.target.value as "all" | "modis" | "viirs")}
                >
                  <option value="all">Semua Sensor</option>
                  <option value="viirs">VIIRS 375m</option>
                  <option value="modis">MODIS 1km</option>
                </select>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8, fontSize: 11, color: "var(--ink2)" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                  <i style={{ width: 10, height: 10, borderRadius: "50%", background: "#EF4444", display: "inline-block" }} /> VIIRS 375m
                </span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                  <i style={{ width: 10, height: 10, borderRadius: "50%", background: "#2563EB", display: "inline-block" }} /> MODIS 1km
                </span>
                <span style={{ marginLeft: "auto", color: "var(--ink3)", fontSize: 10 }}>Radius ∝ √FRP</span>
              </div>

              <div style={{ fontSize: 10, color: "var(--ink3)", marginTop: 5, lineHeight: 1.4 }}>
                Menyebar alami pada koordinat asli satelit. Klik titik mana saja di peta untuk detail FRP & sensor.
              </div>
            </>
          ) : null}
        </div>

        {/* Selected Cell Inspection Card */}
        {selectedCell && (
          <div style={{
            margin: "0 14px 8px", padding: 10,
            background: "var(--sunken)", borderRadius: 8,
            border: "1px solid var(--line)",
            borderLeft: `4px solid ${getCellRisk(selectedCell.detection_count, maxCount).color}`,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--ink)" }}>
                Inspeksi Sel Terfokus
              </span>
              <span style={{
                fontSize: 10, fontWeight: 700,
                color: getCellRisk(selectedCell.detection_count, maxCount).color,
                background: getCellRisk(selectedCell.detection_count, maxCount).bg,
                padding: "2px 8px", borderRadius: 4,
              }}>
                Status: {getCellRisk(selectedCell.detection_count, maxCount).label}
              </span>
            </div>
            <div style={{ fontSize: 10.5, color: "var(--ink2)", marginBottom: 4 }}>
              Sel: <span className="mono">{selectedCell.cell_id}</span> (0,1° ≈ 11 km)
            </div>
            <div style={{ fontSize: 10.5, color: "var(--ink2)", marginBottom: 8 }}>
              Observasi Satelit: <b>{selectedCell.detection_count.toLocaleString()}</b> titik ({selectedCell.total_viirs} VIIRS · {selectedCell.total_modis} MODIS)
            </div>
            <button
              type="button"
              className="seg-btn"
              onClick={() => {
                setSelectedCell(null);
                const p = presets.find(pp => pp.id === aoi);
                if (p) {
                  mapRef.current?.flyToBounds([[p.south, p.west], [p.north, p.east]], { padding: [50, 50], duration: 0.8 });
                }
              }}
              style={{
                width: "100%", padding: "5px 10px", fontSize: 10.5,
                fontWeight: 600, background: "var(--surface)", display: "block", textAlign: "center",
              }}
            >
              Lepas Fokus Sel (Tampilkan Semua)
            </button>
          </div>
        )}

        {/* Grid Kepadatan Observasi 0.1° Card */}
        <div style={{
          margin: "0 14px 8px", padding: 10,
          background: "var(--sunken)", borderRadius: 8, border: "1px solid var(--line)",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--ink)" }}>
              Grid Kepadatan (0,1°)
            </span>
            <button
              type="button"
              className={"seg-btn" + (gridOn ? " active" : "")}
              onClick={() => setGridOn(g => !g)}
              aria-pressed={gridOn}
              style={{
                background: gridOn ? "var(--ember-sub)" : "var(--surface)",
                color: gridOn ? "var(--ember)" : "var(--ink)",
                fontWeight: 600,
                fontSize: 10.5,
                padding: "2px 8px",
              }}
              title={gridOn ? "Sembunyikan lapisan grid kepadatan" : "Tampilkan lapisan grid kepadatan"}
            >
              {gridOn ? "Aktif" : "Nonaktif"}
            </button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, fontSize: 10, color: "var(--ink2)", textAlign: "center", marginTop: 4 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
              <span style={{ display: "inline-block", width: "100%", height: 4, borderRadius: 2, background: "#10B981" }} />
              <span>Aman</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
              <span style={{ display: "inline-block", width: "100%", height: 4, borderRadius: 2, background: "#FACC15" }} />
              <span>Waspada</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
              <span style={{ display: "inline-block", width: "100%", height: 4, borderRadius: 2, background: "#F97316" }} />
              <span>Siaga</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
              <span style={{ display: "inline-block", width: "100%", height: 4, borderRadius: 2, background: "#EF4444" }} />
              <span>Bahaya</span>
            </div>
          </div>
          <div style={{ fontSize: 10, color: "var(--ink3)", lineHeight: 1.4, marginTop: 7 }}>
            {gridOn ? "Klik sel mana saja pada peta untuk memperbesar & menginspeksi titik di area tersebut." : "Aktifkan bila ingin melihat agregasi densitas spasial (Aman, Waspada, Siaga, Bahaya)."}
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", overscrollBehavior: "contain", scrollBehavior: "smooth", padding: "0 8px 8px" }}>
          {list.map(r => {
            const chip = chipFor(r);
            // Strict single selection: only one region can EVER be active at a time!
            const active = r.name === selName;
            return (
              <button
                key={r.name}
                className={"region-item" + (active ? " active" : "")}
                onClick={() => flyTo(r)}
                aria-pressed={active}
              >
                <span>{r.name}</span>
                {chip && (
                  <span className={"chip " + (chip === t("map_status_ready") ? "ready" : "pending")}>
                    {chip}
                  </span>
                )}
              </button>
            );
          })}
          {list.length === 0 && (
            <p style={{ padding: "8px 12px", fontSize: 12, color: "var(--ink3)" }}>
              {lang === "id" ? `Tidak ada wilayah yang cocok dengan "${q}".` : `No regions match "${q}".`}
            </p>
          )}
        </div>

        <div style={{ borderTop: "1px solid var(--line)", padding: "10px 14px", fontSize: 10.5, color: "var(--ink3)" }}>
          {lang === "id" ? "Wilayah Aktif: " : "Active Region: "}
          <span style={{ color: "var(--ink)", fontWeight: 600 }}>
            {selName ?? (lang === "id" ? "Seluruh Kepulauan Indonesia" : "All Indonesian Archipelago")}
          </span>
          <span> · {t("map_status_ready")}</span>
        </div>
      </div>

      {/* Real-time Cursor Coordinate Tracker */}
      <div
        style={{
          position: "absolute",
          left: sidebarOpen ? 350 : 16,
          bottom: 16,
          zIndex: 890,
          background: "var(--surface)",
          border: "1px solid var(--line)",
          boxShadow: "var(--shadow-sm)",
          borderRadius: 8,
          padding: "5px 12px",
          fontSize: 11,
          display: "flex",
          alignItems: "center",
          gap: 10,
          color: "var(--ink2)",
          transition: "left 0.2s ease",
        }}
      >
        <span style={{ color: "var(--ink)", fontWeight: 600 }}>{lang === "id" ? "Wilayah: Indonesia" : "Region: Indonesia"}</span>
        <span>·</span>
        <span ref={coordRef} className="mono">
          {lang === "id" ? "Arahkan kursor ke peta untuk koordinat" : "Hover cursor over map for coordinates"}
        </span>
      </div>

      {/* Scientific Honesty Chip (Guardrail FR-UI-12) */}
      <span
        className="state-chip chip-ok"
        style={{
          position: "absolute", right: 16, bottom: 16, zIndex: 890,
          background: "var(--surface)", boxShadow: "var(--shadow-sm)",
          padding: "5px 12px", fontSize: 11,
        }}
      >
        Hotspot = observasi termal satelit, bukan kepastian kebakaran fisik · Radius ∝ FRP (MW)
      </span>
    </div>
  );
}
