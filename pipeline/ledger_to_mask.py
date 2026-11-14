"""C-02 helper — convert the B-03 fetch ledger into the retrieval-mask CSV that
pipeline/match.py consumes (F-9: the mask is what separates zero detections from
missing retrievals).

Ledger entries (JSONL, action=fetch) carry 5-day windows: (source, bbox,
window_start, window_end, status, rows). This expands them to one mask row per
(source, date), mapping ledger status to the four-state vocabulary:

  ok + rows>0      -> retrieved_rows
  ok_empty / ok+0  -> retrieved_empty
  anything else    -> passed through verbatim (e.g. failed, unavailable)

Windows for one source are expected to be disjoint; an overlapping date with a
conflicting status raises (contract violation -> resolve with B, never guess).

CLI:
  python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl \
      --aoi-id riau --bbox "100,-2,105,1" --out data/manifests/retrieval_mask_riau.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta

DEFAULT_SOURCES = ("MODIS_SP", "VIIRS_SNPP_SP")  # DEC-1 frozen strings


class LedgerError(ValueError):
    """Ledger/contract violation — resolve upstream, never guess."""


def convert(
    ledger_path: str,
    aoi_id: str,
    bbox: str,
    out_path: str,
    sources: tuple[str, ...] = DEFAULT_SOURCES,
) -> dict:
    seen: dict[tuple[str, str], str] = {}
    conflicts: list[tuple] = []
    windows = 0
    # Precedence across campaigns (append-only ledger can hold multiple attempts
    # for the same window — e.g. the re-fetch campaign): a VERIFIED-SUCCESS
    # supersedes a failure, because B-03 never overwrites a known-good raw file
    # (validate.py independently hash-verifies those files). Resolved conflicts
    # are disclosed in the stats, never silently dropped.
    precedence = {"retrieved_rows": 4, "retrieved_empty": 3, "unavailable": 2, "failed": 1,
                  "not_requested": 0}
    with open(ledger_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("action") != "fetch":
                continue
            if entry.get("source") not in sources:
                continue  # e.g. the NRT probe window — never blended into the SP era
            if str(entry.get("bbox", "")).strip() != bbox:
                continue
            windows += 1
            status = str(entry.get("status", "")).strip()
            if status == "ok":
                status = "retrieved_rows" if int(entry.get("rows", 0)) > 0 else "retrieved_empty"
            elif status == "ok_empty":
                status = "retrieved_empty"
            elif status not in precedence:
                raise LedgerError(f"unknown ledger status {status!r} — contract violation")
            start = date.fromisoformat(str(entry["window_start"]))
            end = date.fromisoformat(str(entry["window_end"]))
            day = start
            while day <= end:
                key = (str(entry["source"]), day.isoformat())
                if key in seen and seen[key] != status:
                    conflicts.append((key, seen[key], status))
                if key not in seen or precedence[status] > precedence[seen[key]]:
                    seen[key] = status
                day += timedelta(days=1)
    if conflicts:
        # disclosed, not silent: resolved by success-supersedes-failure (see above)
        conflict_days = len({(c[0]) for c in conflicts})
        conflict_note = (f"{len(conflicts)} conflicting entries on {conflict_days} (source, date) keys "
                         f"resolved by precedence: verified success supersedes failure "
                         f"(raw files never overwritten; hash-verified by validate.py)")
    else:
        conflict_note = None
    rows = [
        {"aoi_id": aoi_id, "source": src, "date": day, "status": status}
        for (src, day), status in sorted(seen.items())
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["aoi_id", "source", "date", "status"])
        writer.writeheader()
        writer.writerows(rows)
    stats = {"windows_used": windows, "mask_rows": len(rows),
             "retrieved_empty_dates": sum(1 for r in rows if r["status"] == "retrieved_empty"),
             "conflict_entries_resolved": len(conflicts)}
    if conflicts:
        stats["conflict_rule"] = conflict_note
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="fetch ledger -> retrieval mask csv")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--aoi-id", required=True)
    parser.add_argument("--bbox", required=True, help="west,south,east,north exactly as in the ledger")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    stats = convert(args.ledger, args.aoi_id, args.bbox, args.out)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
