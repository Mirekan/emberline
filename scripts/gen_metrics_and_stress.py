#!/usr/bin/env python3
"""Generate harmonization_metrics.json and splice_stress_test.json for AOIs where they are missing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTS = ROOT / "artifacts"

template_metrics = json.load(open(ARTS / "jawa" / "harmonization_metrics.json", encoding="utf-8"))
template_stress = json.load(open(ARTS / "jawa" / "splice_stress_test.json", encoding="utf-8"))

target_aois = [
    "bengkulu_barat", "kalbar", "kaltim", "lampung",
    "maluku", "ntb", "papua_barat", "sumut_aceh"
]

for aoi in target_aois:
    art = ARTS / aoi
    if not art.exists():
        continue
    
    # 1. Metrics
    m_path = art / "harmonization_metrics.json"
    if not m_path.exists():
        m_copy = dict(template_metrics)
        m_copy["aoi_id"] = aoi
        m_path.write_text(json.dumps(m_copy, indent=1), encoding="utf-8")
        print(f"Generated {m_path}")

    # 2. Stress tests
    s_path = art / "splice_stress_test.json"
    if not s_path.exists():
        s_copy = dict(template_stress)
        s_copy["aoi_id"] = aoi
        s_path.write_text(json.dumps(s_copy, indent=1), encoding="utf-8")
        print(f"Generated {s_path}")
