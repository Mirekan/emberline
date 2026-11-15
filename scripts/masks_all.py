#!/usr/bin/env python3
"""Build retrieval masks for every AOI in config/aois.yaml — fish/bash-safe.

Usage:  python3 scripts/masks_all.py
"""
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def fmt(v):
    f = float(v)
    return str(int(f)) if f == int(f) else str(f)


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config" / "aois.yaml").read_text())
    fails = []
    for a in cfg["aois"]:
        bbox = ",".join(fmt(a[k]) for k in ("west", "south", "east", "north"))
        out = f"data/manifests/retrieval_mask_{a['id']}.csv"
        r = subprocess.run(
            ["python3", "-m", "pipeline.ledger_to_mask",
             "--ledger", "data/manifests/fetch_ledger.jsonl",
             "--aoi-id", a["id"], "--bbox", bbox, "--out", out],
            capture_output=True, text=True, cwd=ROOT)
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        mark = "ok" if r.returncode == 0 else "FAIL"
        print(f"{a['id']:16s} | {mark} | {tail[-90:]}")
        if r.returncode != 0:
            fails.append(a["id"])
    print("SEMUA MASK ✅" if not fails else f"GAGAL: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
