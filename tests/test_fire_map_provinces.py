"""Check the province catalog used by FireMap search: python3 tests/test_fire_map_provinces.py."""
import re
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "web/src/screens/FireMap.tsx").read_text()
# Province roster: https://wilayah.id/api/provinces.json (administrative level 1).
EXPECTED = set("""Aceh
Sumatera Utara
Sumatera Barat
Riau
Jambi
Sumatera Selatan
Bengkulu
Lampung
Kepulauan Bangka Belitung
Kepulauan Riau
DKI Jakarta
Jawa Barat
Jawa Tengah
DI Yogyakarta
Jawa Timur
Banten
Bali
Nusa Tenggara Barat
Nusa Tenggara Timur
Kalimantan Barat
Kalimantan Tengah
Kalimantan Selatan
Kalimantan Timur
Kalimantan Utara
Sulawesi Utara
Sulawesi Tengah
Sulawesi Selatan
Sulawesi Tenggara
Gorontalo
Sulawesi Barat
Maluku
Maluku Utara
Papua
Papua Barat
Papua Selatan
Papua Tengah
Papua Pegunungan
Papua Barat Daya""".splitlines())

regions_match = re.search(r"const REGIONS:.*? = \[(.*?)\n\];", SOURCE, re.S)
assert regions_match, "FireMap province catalog not found"
regions = regions_match.group(1)
names = re.findall(r'name: "([^"]+)"', regions)
provinces = [name.removesuffix(" (Merauke)") for name in names]
assert set(provinces) == EXPECTED, f"Missing: {EXPECTED - set(provinces)}; unexpected: {set(provinces) - EXPECTED}"
assert len(provinces) == len(EXPECTED), "Duplicate province entries"

islands_match = re.search(r"export const ISLANDS:.*? = \[(.*?)\n\];", SOURCE, re.S)
assert islands_match, "FireMap island groups not found"
islands = islands_match.group(1)
grouped = [name for group in re.findall(r"provinces: \[([^\]]+)\]", islands) for name in re.findall(r'"([^"]+)"', group)]
assert set(grouped) == EXPECTED, f"Island grouping missing: {EXPECTED - set(grouped)}; unexpected: {set(grouped) - EXPECTED}"
assert len(grouped) == len(EXPECTED), "Duplicate island-group province entries"
assert dict(re.findall(r'name: "([^"]+)", center: \[[^\]]+\], preset: "([^"]+)"', regions)) == {
    "Kalimantan Tengah": "central_kalimantan",
    "Riau": "riau",
    "Sumatera Selatan": "south_sumatra",
    "Jambi": "jambi",
    "Papua Selatan (Merauke)": "merauke",
}, "Existing analysis presets must remain unchanged"
print(f"PASS: all {len(EXPECTED)} provinces listed once; island groups complete; five preset mappings preserved")
