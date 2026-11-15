"""Run: python3 tests/test_fire_map_tooltips.py."""
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "web/src/screens/FireMap.tsx").read_text()
assert "bgRect.bindTooltip" not in source, "Empty grid background must not display a hover tooltip"
assert "sticky: true" not in source, "Heat tooltips must stay anchored, not follow the cursor"
assert "area.bindTooltip" in source, "Populated heat cells must retain hover details"
assert source.count("L.canvas(") == 1, "Grid and dots must share one canvas; overlapping canvases block cell input"
assert 'bgRect.on("click"' in source, "Empty grid cells must remain inspectable by clicking"
print("PASS: hover details only on heat cells; no cursor-following tooltip; background clicks preserved")
