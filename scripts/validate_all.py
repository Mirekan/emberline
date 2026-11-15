#!/usr/bin/env python3
"""Validate every AOI in config/aois.yaml — runbook helper (fish/bash-safe).

Usage:  python3 scripts/validate_all.py
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
        slug = ("w" + fmt(a["west"]) + "_s" + fmt(a["south"])
                + "_e" + fmt(a["east"]) + "_n" + fmt(a["north"]))
        r = subprocess.run(
            ["python3", "pipeline/validate.py", "--slug", slug,
             "--source", "MODIS_SP", "VIIRS_SNPP_SP"],
            capture_output=True, text=True, cwd=ROOT)
        tail = [l for l in r.stdout.splitlines() if "coverage" in l]
        mark = "ok" if r.returncode == 0 else "FAIL"
        print(f"{a['id']:16s} | {mark} | {tail[0] if tail else r.stderr[-120:]}")
        if r.returncode != 0:
            fails.append(a["id"])
    print("SEMUA VALID ✅" if not fails else f"GAGAL: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
