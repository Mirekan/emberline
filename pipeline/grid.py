#!/usr/bin/env python3
"""Grid assignment (C-02) — 0.1 deg cells, centroid containment, no rounding.

cell_id scheme (config/grid.yaml F-4): floor(x / 0.1) -> id = R{lat:05d}C{lon:05d}.
Half-open [west, east) x [south, north); detections exactly on the east/north
edge belong to the neighbouring cell. Unequal cell area NOT corrected in v1.
"""
from __future__ import annotations

import math

CELL_DEG = 0.1


def cell_id(lat: float, lon: float) -> str:
    lat_idx = math.floor(lat / CELL_DEG)
    lon_idx = math.floor(lon / CELL_DEG)
    return f"R{lat_idx:05d}C{lon_idx:05d}"
