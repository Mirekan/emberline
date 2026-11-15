# Azure fetch runbook — full-Indonesia mosaic (wave-2, 12 tiles)

Era profile (b): **2018-01-01..2026-07-31** per tile (625 windows × 2 sources).
Governance: AOI-PRESETS-EXPANSION APPROVED (DECISIONS.md). Quota check: 12 parallel
processes ≈ 143 trx/min < 5.000/10 min FIRMS ceiling ✓.

## 0. VM setup (Ubuntu 22.04/24.04, B1s/B2s, ~10 min)

```bash
git clone https://github.com/Mirekan/emberline && cd emberline
pip install -r requirements.txt
cp .env.example .env && nano .env          # FIRMS_MAP_KEY (human-filled, never committed)
```

## 1. Parallel fetch — ONE REPO CLONE PER TILE, one process each

**Why clones:** the fetch ledger is append-only with a FIXED path; concurrent writes to
one ledger = the append-race that corrupted provenance in B-05. One clone per tile gives
each process its own ledger with zero code changes.

```bash
cd ~
for tile in kalbar kaltim papua_selatan sulsel ntt ntb sumut_aceh lampung papua_barat maluku jawa bengkulu_barat; do
  git clone ~/emberline ~/emberline-$tile && cd ~/emberline-$tile
  cp ~/emberline/.env .env
  nohup python3 pipeline/fetch_firms.py fetch --aoi $tile > fetch-$tile.log 2>&1 &
  cd ~
done
```

12 parallel processes ≈ 143 trx/min total. Per tile: 1,250 windows ≈ 105 min.
**Monitor:** `grep -c '"action": "fetch"' ~/emberline-*/data/manifests/fetch_ledger.jsonl`
(target 625 × 2 sources = 1,250 per tile; `fetch_firms.py verify` per clone when done).

Tier-C tiles (papua_barat, maluku, jawa, bengkulu_barat) may be smoke-fetched first:
add `--limit-windows 60` → density check (rows/window) → decide continue or leave
`insufficient` honestly.

## 2. Merge into the main checkout (~15 min)

```bash
cd ~/emberline
for tile in kalbar kaltim papua_selatan sulsel ntt ntb sumut_aceh lampung papua_barat maluku jawa bengkulu_barat; do
  rsync -a ~/emberline-$tile/data/raw/ data/raw/            # slug dirs are distinct — no collision
  cat ~/emberline-$tile/data/manifests/fetch_ledger.jsonl >> data/manifests/fetch_ledger.jsonl
  rsync -a ~/emberline-$tile/data/processed/ data/processed/
  rsync -a ~/emberline-$tile/data/manifests/validation_report_*.json data/manifests/
  rsync -a ~/emberline-$tile/data/manifests/ingest_evidence_*.md data/manifests/
done
python3 pipeline/fetch_firms.py manifest && python3 pipeline/fetch_firms.py verify
```

## 3. Validate + masks per tile (~20 min)

```bash
for slug in w109_s-3_e114_n2 w114_s-2_e119_n3 w132_s-9_e137_n-4 w119_s-5_e124_n0 \
            w120_s-10_e125_n-5 w115_s-10_e120_n-5 w95_s1_e100_n6 w103_s-8_e108_n-5 \
            w130_s-6_e135_n-1 w125_s-8_e130_n-3 w107_s-8_e112_n-3 w100_s-5_e103_n-2; do
  python3 pipeline/validate.py --slug $slug --source MODIS_SP VIIRS_SNPP_SP
done
python3 tests/test_b_ingestion.py

# masks — bbox strings MUST match the fetch bbox in the ledger (int format):
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id kalbar         --bbox "109,-3,114,2"    --out data/manifests/retrieval_mask_kalbar.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id kaltim        --bbox "114,-2,119,3"    --out data/manifests/retrieval_mask_kaltim.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id papua_selatan --bbox "132,-9,137,-4"   --out data/manifests/retrieval_mask_papua_selatan.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id sulsel        --bbox "119,-5,124,0"    --out data/manifests/retrieval_mask_sulsel.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id ntt           --bbox "120,-10,125,-5"  --out data/manifests/retrieval_mask_ntt.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id ntb           --bbox "115,-10,120,-5"  --out data/manifests/retrieval_mask_ntb.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id sumut_aceh    --bbox "95,1,100,6"      --out data/manifests/retrieval_mask_sumut_aceh.csv
python3 -m pipeline.ledger_to_mask --ledger data/manifests/fetch_ledger.jsonl --aoi-id lampung       --bbox "103,-8,108,-5"   --out data/manifests/retrieval_mask_lampung.csv
# tier C tiles: same pattern (papua_barat 130,-6,135,-1 · maluku 125,-8,130,-3 ·
# jawa 107,-8,112,-3 · bengkulu_barat 100,-5,103,-2)
```

## 4. Science chain per tile (~2-5 min each, compact zero-fill is era-safe)

```bash
for aoi in kalbar kaltim papua_selatan sulsel ntt ntb sumut_aceh lampung papua_barat maluku jawa bengkulu_barat; do
  make reproduce AOI=$aoi
done
```

Honest statuses expected: tier-A tiles → `c03/c04 ok` (3 train years + 5.6 test years);
tier-C tiles with thin density → `insufficient_data`/`insufficient` climatology — recorded,
never padded.

## 5. Ship

```bash
make test
git add config/ artifacts/ docs/ && git commit -m "[C] wave-2 mosaics: 12 tiles reproduced, artifacts + evidence"
git push origin main
# dataset besar -> Azure Blob (privat):
az storage blob upload-batch -d emberline-data -s data/
```

## Guards (from the frozen protocol — unchanged by Azure)

- MAP_KEY only in per-clone `.env`; never in logs/images/repo; deallocate idle VMs.
- One owner per tile: never fetch the same tile from two machines simultaneously.
- Host recorded: timing/evidence from the VM says "measured on Azure VM".
- NRT never blended; SP era cap 2026-07-31 stands.
- `git clean -x/-X` FORBIDDEN in clones (deleted our processed tree once — raw survived,
  everything regenerable, but it cost an hour).
