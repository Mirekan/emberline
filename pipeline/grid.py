"""EmberLine C-02 — grid geometry (PROTO-C01-v0.9, frozen decision F-4).

Owner: team member C. Contract test: tests/test_grid_match.py.

Frozen rules implemented here (config/grid.yaml is the source of truth):
- 0.1-degree cells; a detection belongs to the cell containing its reported
  centroid (floor(x / cell_size)); coordinates are never rounded.
- Cells are half-open [west, east) x [south, north): a detection exactly on the
  east/north edge belongs to the neighbouring cell.
- An AOI is the set of cells whose *cell centroid* lies inside the bbox
  (half-open on east/north edges). A detection slightly outside the bbox can
  therefore be included when its cell centroid is inside (and vice versa) —
  this is the frozen F-4 rule, not a bug.
- Bbox validation: finite numbers, west < east, south < north, extent <= cap,
  antimeridian-crossing boxes rejected in v1.
- Unequal physical cell area (~cos latitude) is NOT corrected in v1
  (documented limitation, not silently adjusted).
"""
from __future__ import annotations

import math
from pathlib import Path

try:
    import yaml
except ImportError as _exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from _exc

ROOT = Path(__file__).resolve().parents[1]
_CFG = yaml.safe_load((ROOT / "config" / "grid.yaml").read_text())
CELL_SIZE_DEG = float(_CFG["grid"]["cell_size_deg"])
BBOX_CAP_DEG = float(_CFG["aoi_limits"]["bbox_cap_deg"])
KM_PER_DEG = 111.32  # for the documented, unused-in-v1 area note only


class GridError(ValueError):
    """Raised for bbox or cell violations the protocol forbids."""


def validate_bbox(west: float, south: float, east: float, north: float) -> dict:
    """Enforce F-4 bbox rules. Returns the normalized bbox dict or raises GridError."""
    for name, value in (("west", west), ("south", south), ("east", east), ("north", north)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise GridError(f"bbox {name} must be a finite number, got {value!r}")
    if not west < east:
        raise GridError(
            "bbox must satisfy west < east; antimeridian-crossing boxes are rejected in v1"
        )
    if not south < north:
        raise GridError("bbox must satisfy south < north")
    if not (-180.0 <= west and east <= 180.0 and -90.0 <= south and north <= 90.0):
        raise GridError("bbox out of world range [-180,180]x[-90,90]")
    if (east - west) > BBOX_CAP_DEG or (north - south) > BBOX_CAP_DEG:
        raise GridError(f"bbox extent exceeds the {BBOX_CAP_DEG} deg cap (F-4)")
    return {"west": float(west), "south": float(south), "east": float(east), "north": float(north)}


def cell_indices(lon: float, lat: float) -> tuple[int, int]:
    """Floor-assignment of one detection centroid to (lat_idx, lon_idx). No rounding."""
    if isinstance(lat, bool) or not isinstance(lat, (int, float)) or not math.isfinite(lat):
        raise GridError(f"latitude must be a finite number, got {lat!r}")
    if isinstance(lon, bool) or not isinstance(lon, (int, float)) or not math.isfinite(lon):
        raise GridError(f"longitude must be a finite number, got {lon!r}")
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise GridError(f"coordinates out of world range: lon={lon!r} lat={lat!r}")
    # math.floor handles negative lat/lon (southern/western hemispheres) correctly.
    # Epsilon-corrected floor: exact cell boundaries suffer float representation
    # error (100.1/0.1 -> 1000.9999999999999). 1e-9 deg ~ 0.1 mm, far below the
    # source coordinate precision, so it only repairs boundary values.
    eps = 1e-9
    return math.floor(lat / CELL_SIZE_DEG + eps), math.floor(lon / CELL_SIZE_DEG + eps)


def cell_id(lat_idx: int, lon_idx: int) -> str:
    """Deterministic cell identifier, e.g. 'R10C1004' / southern 'R-124C300'."""
    return f"R{lat_idx}C{lon_idx}"


def cell_centroid(lat_idx: int, lon_idx: int) -> tuple[float, float]:
    """(lon, lat) of the cell centroid."""
    return (lon_idx + 0.5) * CELL_SIZE_DEG, (lat_idx + 0.5) * CELL_SIZE_DEG


def point_in_bbox(lon: float, lat: float, bbox: dict) -> bool:
    """Half-open membership: west <= lon < east and south <= lat < north (F-4)."""
    return bbox["west"] <= lon < bbox["east"] and bbox["south"] <= lat < bbox["north"]


def cell_in_aoi(lat_idx: int, lon_idx: int, bbox: dict) -> bool:
    """F-4 clipping rule: a cell is in the AOI iff its centroid is inside the bbox."""
    clon, clat = cell_centroid(lat_idx, lon_idx)
    return point_in_bbox(clon, clat, bbox)


def assign_cell(lon: float, lat: float, bbox: dict) -> str | None:
    """Assign one detection to its cell; None when that cell lies outside the AOI.

    Counted and disclosed by the caller (never silently dropped): drops are
    reported in the run summary, not hidden.
    """
    lat_idx, lon_idx = cell_indices(lon, lat)
    if not cell_in_aoi(lat_idx, lon_idx, bbox):
        return None
    return cell_id(lat_idx, lon_idx)


def aoi_cell_ids(bbox: dict) -> list[str]:
    """Deterministic (south->north, west->east) list of all cells in the AOI."""
    out: list[str] = []
    lat_lo = math.floor(bbox["south"] / CELL_SIZE_DEG) - 1
    lat_hi = math.floor(bbox["north"] / CELL_SIZE_DEG) + 2
    lon_lo = math.floor(bbox["west"] / CELL_SIZE_DEG) - 1
    lon_hi = math.floor(bbox["east"] / CELL_SIZE_DEG) + 2
    for lat_idx in range(lat_lo, lat_hi):
        for lon_idx in range(lon_lo, lon_hi):
            if cell_in_aoi(lat_idx, lon_idx, bbox):
                out.append(cell_id(lat_idx, lon_idx))
    return out


def cell_area_km2_approx(lat_idx: int) -> float:
    """Approximate physical cell area (km^2) — documentation/limitation only, v1
    does NOT area-correct aggregates (F-4)."""
    lat = (lat_idx + 0.5) * CELL_SIZE_DEG
    return (CELL_SIZE_DEG * KM_PER_DEG) * (CELL_SIZE_DEG * KM_PER_DEG * math.cos(math.radians(lat)))
