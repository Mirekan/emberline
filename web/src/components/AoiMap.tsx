import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export type BBox = { west: number; south: number; east: number; north: number };

/**
 * AoiMap (FR-UI-1 P0) — dark Leaflet map with drag-to-draw bounding box.
 * Two-way sync: drawing calls onBounds; prop `bounds` moves the rectangle;
 * prop `fitKey` bump = fit the map to the bounds (e.g. after preset click).
 * Map drawing and typing coordinates are equal paths (FR-UI-1 / DEV-S04).
 */
export default function AoiMap({ bounds, onBounds, fitKey, height = 360 }: {
  bounds: BBox;
  onBounds: (b: BBox) => void;
  fitKey?: number;
  height?: number;
}) {
  const elRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const rectRef = useRef<L.Rectangle | null>(null);
  const drawModeRef = useRef(false);
  const draggingRef = useRef(false);
  const startRef = useRef<L.LatLng | null>(null);
  const cbRef = useRef(onBounds);
  cbRef.current = onBounds;
  const [drawing, setDrawing] = useState(false);

  // init once
  useEffect(() => {
    if (!elRef.current || mapRef.current) return;
    const map = L.map(elRef.current, { center: [-1.4, 102.5], zoom: 8, zoomSnap: 0.25 });
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      { attribution: "Esri, HERE, Garmin, OpenStreetMap contributors", maxZoom: 12,
        }
    ).addTo(map);
    const b = bounds;
    rectRef.current = L.rectangle(
      [[b.south, b.west], [b.north, b.east]] as L.LatLngBoundsExpression,
      { color: "#E8763C", weight: 2, fillOpacity: 0.12 }
    ).addTo(map);
    mapRef.current = map;

    const startDraw = (e: L.LeafletMouseEvent) => {
      if (!drawModeRef.current) return;
      startRef.current = e.latlng;
      draggingRef.current = true;
    };
    const moveDraw = (e: L.LeafletMouseEvent) => {
      if (!draggingRef.current || !startRef.current) return;
      rectRef.current?.setBounds(L.latLngBounds(startRef.current, e.latlng));
    };
    const endDraw = (e: L.LeafletMouseEvent) => {
      if (!draggingRef.current || !startRef.current) return;
      draggingRef.current = false;
      const bb = L.latLngBounds(startRef.current, e.latlng || startRef.current);
      rectRef.current?.setBounds(bb);
      cbRef.current({
        west: bb.getWest(), south: bb.getSouth(), east: bb.getEast(), north: bb.getNorth(),
      });
      drawModeRef.current = false;
      setDrawing(false);
      map.dragging.enable();
      elRef.current!.style.cursor = "";
    };
    map.on("mousedown", startDraw);
    map.on("mousemove", moveDraw);
    map.on("mouseup", endDraw);
    const winUp = () => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      drawModeRef.current = false;
      setDrawing(false);
      map.dragging.enable();
      elRef.current!.style.cursor = "";
    };
    window.addEventListener("mouseup", winUp);
    return () => {
      window.removeEventListener("mouseup", winUp);
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // external bounds -> rectangle (skip while user is drawing)
  useEffect(() => {
    if (draggingRef.current || !mapRef.current) return;
    rectRef.current?.setBounds([[bounds.south, bounds.west], [bounds.north, bounds.east]]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bounds.west, bounds.south, bounds.east, bounds.north]);

  // fitKey bump -> fit map to bounds (preset click)
  useEffect(() => {
    if (!fitKey || !mapRef.current || !rectRef.current) return;
    mapRef.current.fitBounds(rectRef.current.getBounds(), { padding: [24, 24] });
  }, [fitKey]);

  const toggleDraw = () => {
    const next = !drawing;
    setDrawing(next);
    drawModeRef.current = next;
    if (mapRef.current) {
      if (next) {
        mapRef.current.dragging.disable();
        elRef.current!.style.cursor = "crosshair";
      } else {
        mapRef.current.dragging.enable();
        elRef.current!.style.cursor = "";
      }
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <div ref={elRef} style={{ width: "100%", height, borderRadius: 8, border: "1px solid var(--line)", overflow: "hidden" }} />
      <button
        onClick={toggleDraw}
        className={"btn " + (drawing ? "" : "secondary")}
        style={{ position: "absolute", top: 10, right: 10, padding: "6px 14px", fontSize: 12,
                 boxShadow: "0 1px 4px rgba(0,0,0,0.5)" }}>
        {drawing ? "Drawing… release to finish" : "Draw on map"}
      </button>
    </div>
  );
}
