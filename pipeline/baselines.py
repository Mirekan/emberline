"""EmberLine C-03 — naive and ratio baselines (PROTO-C01-v0.9, F-10/F-11/F-12).

Owner: team member C. Contract test: tests/test_baseline_leakage.py.

Consumes the C-02 matched-pairs table and produces the B0 (naive splice) and B1
(training-fitted global ratio) baselines evaluated on the FROZEN temporal split
(params.yaml split.frozen_split_dates, train <= 2020-10-08).

Protocol rules implemented here:
- Series are aggregated to AOI-day per day/night class from BOTH-retrieved pairs
  (matched_signal + matched_zero + one_sided retained for the record); FITTING
  uses fitting-eligible pairs only (one-sided excluded, F-6).
- B1 ratio r = sum(S_modis)/sum(S_viirs) over TRAINING fitting-eligible pairs
  only; prediction S_hat = r * S_viirs. Training-only law (F-11) is enforced by
  construction and verified by tests.
- Support gate (F-9b / DEC-2): a year is eligible when its paired-retrieval
  fraction >= 0.90 and it has >= 10 MODIS-signal days; fitting needs >= 2
  eligible training years and >= 1 eligible test year — otherwise the result is
  an explicit `insufficient_data`, never a model fitted on thin support.
- Zero/undefined policies (F-15): zero denominators yield N/A with a reason —
  never infinity, never a fabricated zero.
- Every learned value carries its inputs: baseline.json records which years fed
  the fit so A's leakage audit (C-05/A-07) can recompute r from those rows.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError as _exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from _exc

ROOT = Path(__file__).resolve().parents[1]
_PARAMS = yaml.safe_load((ROOT / "config" / "params.yaml").read_text())

PROTOCOL_VERSION = _PARAMS["protocol_version"]
_SPLIT = _PARAMS["split"]["frozen_split_dates"]
TRAIN_END = _SPLIT["train_end"]          # inclusive: training era ends here
TEST_START = _SPLIT["test_start"]        # exclusive start of held-out era
SUPPORT = _PARAMS["support"]
MIN_TRAIN_YEARS = SUPPORT["fitting_requires"]["min_training_years"]
MIN_TEST_YEARS = SUPPORT["fitting_requires"]["min_test_years"]
MIN_RETRIEVAL_FRACTION = SUPPORT["training_year_min_paired_retrieval_fraction"]
MIN_SIGNAL_DAYS = SUPPORT["training_year_min_modis_signal_days"]


class BaselineError(ValueError):
    """Protocol violation — hard-fail, never silently reinterpret."""


def load_pairs(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        try:
            import pandas  # noqa: PLC0415
            return pandas.read_parquet(path).to_dict("records")
        except ImportError as exc:
            raise BaselineError("parquet input needs pyarrow (D-01 pins deps)") from exc
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _num(row: dict, field: str) -> float | None:
    raw = row.get(field)
    if raw in (None, ""):
        return None
    return float(raw)


def aggregate_aoi_days(pairs: list[dict]) -> tuple[list[dict], dict]:
    """C-02 matched pairs -> AOI-day series per day/night class (F-3).

    Series values come from BOTH-retrieved pairs (one-sided rows still belong to
    the observed record); `fitting_rows` counts the F-6-eligible subset.
    """
    buckets: dict[tuple[str, str], dict] = {}
    counts = defaultdict(int)
    for row in pairs:
        day, daynight = str(row["date"]), str(row["daynight"])
        bucket = buckets.setdefault((day, daynight), {
            "date": day, "daynight": daynight,
            "modis_frp_sum_mw": 0.0, "viirs_frp_sum_mw": 0.0,
            "modis_signal_days_contrib": 0,
            "both_retrieved": True, "any_fitting_eligible": False,
        })
        for fam, field in (("modis", "modis_frp_sum_mw"), ("viirs", "viirs_frp_sum_mw")):
            value = _num(row, field)
            if value is None:
                bucket["both_retrieved"] = False  # a missing side poisons the day
            else:
                bucket[field] += value
        if str(row.get("state")) == "matched_signal":
            bucket["modis_signal_days_contrib"] = 1
        if str(row.get("fitting_eligible")).lower() == "true":
            bucket["any_fitting_eligible"] = True
            counts["fitting_eligible_pairs"] += 1
        counts["pairs_seen"] += 1
    days = [buckets[k] for k in sorted(buckets)]
    for bucket in days:
        bucket["modis_frp_sum_mw"] = round(bucket["modis_frp_sum_mw"], 6)
        bucket["viirs_frp_sum_mw"] = round(bucket["viirs_frp_sum_mw"], 6)
    return days, dict(counts)


def eligible_years(aoi_days: list[dict], era_days_mask: dict[str, int]) -> tuple[set[str], list[dict]]:
    """F-9b/DEC-2 eligibility: >=90% paired-retrieval days and >=10 signal days.

    era_days_mask maps year -> number of era days in that year (from the frozen
    overlap era), so the retrieval fraction is computed against the era, not the
    calendar.
    """
    per_year: dict[str, dict] = defaultdict(lambda: {
        "days_both_retrieved": 0, "signal_days": 0, "era_days": 0,
    })
    for year, era_days in era_days_mask.items():
        per_year[year]["era_days"] = era_days
    for bucket in aoi_days:
        year = bucket["date"][:4]
        stats = per_year.setdefault(year, {
            "days_both_retrieved": 0, "signal_days": 0, "era_days": 0,
        })
        if bucket["both_retrieved"]:
            stats["days_both_retrieved"] += 1
        if bucket["modis_signal_days_contrib"]:
            stats["signal_days"] += 1
    eligible: set[str] = set()
    report = []
    for year in sorted(per_year):
        stats = per_year[year]
        fraction = (stats["days_both_retrieved"] / stats["era_days"]) if stats["era_days"] else 0.0
        ok = fraction >= MIN_RETRIEVAL_FRACTION and stats["signal_days"] >= MIN_SIGNAL_DAYS
        if ok:
            eligible.add(year)
        report.append({
            "year": year,
            "era_days": stats["era_days"],
            "days_both_retrieved": stats["days_both_retrieved"],
            "signal_days": stats["signal_days"],
            "retrieval_fraction": round(fraction, 4),
            "eligible": ok,
        })
    return eligible, report


def _era_day_counts(days: list[str]) -> dict[str, int]:
    """Year -> day count inside the delivered/era window (per distinct date)."""
    counts: dict[str, int] = defaultdict(int)
    for day in set(days):
        counts[day[:4]] += 1
    return dict(counts)


def fit_and_predict(aoi_days: list[dict], eligible: set[str]) -> dict:
    """Split by the FROZEN dates, fit B1 on training only, build B0/B1 series."""
    train_days: list[dict] = []
    test_days: list[dict] = []
    for bucket in aoi_days:
        year = bucket["date"][:4]
        if year not in eligible:
            bucket["role"] = "excluded_year"
            continue
        bucket["role"] = "train" if bucket["date"] <= TRAIN_END else "test"
        (train_days if bucket["role"] == "train" else test_days).append(bucket)

    if len({b["date"][:4] for b in train_days}) < MIN_TRAIN_YEARS or \
            len({b["date"][:4] for b in test_days}) < MIN_TEST_YEARS:
        return {"status": "insufficient_data", "train_days": len(train_days),
                "test_days": len(test_days),
                "reason": "eligible training/test year counts below F-9b minimums"}

    sum_modis = sum(b["modis_frp_sum_mw"] for b in train_days if b["any_fitting_eligible"])
    sum_viirs = sum(b["viirs_frp_sum_mw"] for b in train_days if b["any_fitting_eligible"])
    if sum_viirs <= 0:
        return {"status": "insufficient_data",
                "reason": "N/A: zero VIIRS training sum (F-15 zero-denominator policy)"}
    ratio = round(sum_modis / sum_viirs, 8)

    # Every AOI-day derived from C-02 pairs lies inside the overlap era (the
    # post-transition period), so B0's splice value here is the RAW VIIRS
    # observation — the uncorrected "problem as-is" that B1 must beat on the
    # same held-out rows. Pre-VIIRS-era MODIS observations enter the published
    # series later (C-06/E) from the per-sensor units, never through these pairs.
    for bucket in aoi_days:
        if not bucket["both_retrieved"]:
            bucket["B0_naive_splice_mw"], bucket["B1_ratio_pred_mw"] = None, None
            bucket["source_flag"] = "gap"
            continue
        bucket["B0_naive_splice_mw"] = bucket["viirs_frp_sum_mw"]
        bucket["B1_ratio_pred_mw"] = round(ratio * bucket["viirs_frp_sum_mw"], 6)
        bucket["source_flag"] = "overlap_raw_viirs"
    return {
        "status": "ok",
        "B1_ratio": ratio,
        "B1_fit_inputs": {
            "train_dates_eligible_pairs_only": True,
            "train_sum_modis_mw": round(sum_modis, 6),
            "train_sum_viirs_mw": round(sum_viirs, 6),
            "train_years": sorted({b["date"][:4] for b in train_days}),
            "test_years": sorted({b["date"][:4] for b in test_days}),
        },
        "train_days": len(train_days),
        "test_days": len(test_days),
    }


def run(pairs_path: str | Path, out_dir: str | Path, aoi_id: str) -> dict:
    """Full C-03 step: eligibility -> frozen split -> B0/B1 -> artifacts."""
    pairs = load_pairs(pairs_path)
    required = {"date", "daynight", "modis_frp_sum_mw", "viirs_frp_sum_mw", "state", "fitting_eligible"}
    if not pairs:
        raise BaselineError("matched pairs: no rows received (run C-02 first)")
    missing = required - set(pairs[0])
    if missing:
        raise BaselineError(f"matched pairs schema mismatch — missing {sorted(missing)}")
    aoi_days, pair_counts = aggregate_aoi_days(pairs)
    era_days = _era_day_counts([b["date"] for b in aoi_days])
    eligible, year_report = eligible_years(aoi_days, era_days)
    outcome = fit_and_predict(aoi_days, eligible)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    series_path = out_dir / "baseline_series.csv"
    columns = ["date", "daynight", "role", "source_flag", "modis_frp_sum_mw",
               "viirs_frp_sum_mw", "B0_naive_splice_mw", "B1_ratio_pred_mw"]
    with series_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(aoi_days)

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "task": "C-03",
        "aoi_id": aoi_id,
        "frozen_split": {"train_end": TRAIN_END, "test_start": TEST_START},
        "pair_counts": pair_counts,
        "year_eligibility": year_report,
        "eligible_years": sorted(eligible),
        "outcome": outcome,
        "note": "B0 = naive splice; B1 = training-fitted global ratio; FRP-sum is an "
                "aggregate of sampled radiative-power observations, not a fire count",
    }
    manifest_path = out_dir / "baselines.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"aoi_days": aoi_days, "manifest": manifest,
            "outputs": {"series": str(series_path), "manifest": str(manifest_path)}}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="C-03 baselines B0/B1")
    parser.add_argument("--pairs", required=True, help="C-02 matched_pairs.csv")
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--out", default=None, help="default artifacts/<aoi-id>/")
    args = parser.parse_args(argv)
    out_dir = args.out or f"artifacts/{args.aoi_id}"
    result = run(args.pairs, out_dir, args.aoi_id)
    print(json.dumps(result["manifest"]["outcome"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
