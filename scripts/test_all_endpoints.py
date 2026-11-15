import urllib.request
import json

base = "http://127.0.0.1:8300"
presets_res = json.loads(urllib.request.urlopen(f"{base}/api/aoi/presets").read())["presets"]
aois = [p["id"] for p in presets_res]
print(f"Testing {len(aois)} presets across all endpoints...\n")

endpoints = [
    ("series", "/api/aoi/{aoi}/series"),
    ("calendar", "/api/aoi/{aoi}/calendar"),
    ("windows", "/api/aoi/{aoi}/windows"),
    ("grid", "/api/aoi/{aoi}/grid"),
    ("detections", "/api/aoi/{aoi}/detections"),
    ("method", "/api/method?aoi={aoi}")
]

results = {}
for aoi in aois:
    results[aoi] = {}
    for name, ep in endpoints:
        url = base + ep.format(aoi=aoi)
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                results[aoi][name] = resp.status
        except urllib.error.HTTPError as e:
            results[aoi][name] = e.code
        except Exception as e:
            results[aoi][name] = str(e)[:15]

hdr = f"{'AOI':<20} | " + " | ".join(f"{e[0]:<10}" for e in endpoints)
print(hdr)
print("-" * len(hdr))
for aoi, res in results.items():
    statuses = " | ".join(f"{str(res.get(e[0], '-')):<10}" for e in endpoints)
    print(f"{aoi:<20} | {statuses}")
