import urllib.request
import json

presets = json.loads(urllib.request.urlopen('http://127.0.0.1:8300/api/aoi/presets').read())['presets']
print(f"{'PRESET ID':18} | {'STATUS':17} | {'METRICS':20} | {'STRESS':6} | {'PEAK SMOOTH':11} | {'WINDOWS'}")
print("-" * 85)
for p in presets:
    pid = p['id']
    try:
        m = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8300/api/method?aoi={pid}').read())
        metrics = m.get('metrics', {})
        status = m.get('status', 'ok')
        stress = len(m.get('stress_tests', []))
        c = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8300/api/aoi/{pid}/calendar').read())
        smooth = [x for x in c.get('climatology_smoothed_median_mw', []) if x is not None]
        max_smooth = max(smooth) if smooth else 0
        windows = len(c.get('critical_windows', []))
        non_null = sum(1 for v in metrics.values() if v is not None)
        print(f"{pid:18} | {status:17} | {len(metrics):2} keys ({non_null:2} non-null) | {stress:6} | {max_smooth:8.2f} MW | {windows:7}")
    except Exception as e:
        print(f"{pid:18} | ERROR: {e}")
