import json
import yaml
from pathlib import Path

arts = Path("artifacts")
all_dets = []
seen = set()
for p in sorted(arts.glob("*/detections.json")):
    if p.parent.name == "all":
        continue
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for d in data.get("detections", []):
            key = (d["date"], round(d["lat"], 4), round(d["lon"], 4))
            if key not in seen:
                seen.add(key)
                all_dets.append(d)
    except Exception:
        pass

aois = yaml.safe_load(open("config/aois.yaml", encoding="utf-8"))["aois"]
for a in aois:
    aoi_dir = arts / a["id"]
    if not aoi_dir.is_dir():
        continue
    det_file = aoi_dir / "detections.json"
    if det_file.exists():
        continue
    sub = [d for d in all_dets if a["west"] <= d["lon"] <= a["east"] and a["south"] <= d["lat"] <= a["north"]]
    name = a.get("name", a["id"])
    payload = {
        "n_detections": len(sub),
        "note": f"FIRMS satellite detections for {name}.",
        "detections": sub,
    }
    det_file.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"Wrote {det_file} with {len(sub)} detections")
