import subprocess
import glob
import os
import json

targets = [
    'bengkulu_barat',
    'kaltim',
    'lampung',
    'maluku',
    'ntb',
    'papua_barat',
    'sumut_aceh',
    'papua_selatan',
]

for aoi in targets:
    b_csv = f'artifacts/{aoi}/baseline_series.csv'
    h_csv = f'artifacts/{aoi}/harmonized_daily.csv'
    if not os.path.exists(b_csv) or not os.path.exists(h_csv):
        print(f'{aoi}: missing baseline or harmonized csv')
        continue
    cmd = [
        'python', '-m', 'pipeline.metrics',
        '--baselines', b_csv,
        '--harmonized', h_csv,
        '--aoi-id', aoi,
    ]
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1')
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if p.returncode == 0:
        print(f'{aoi}: SUCCESS')
    else:
        print(f'{aoi}: FAILED: {p.stderr.strip() or p.stdout.strip()}')
