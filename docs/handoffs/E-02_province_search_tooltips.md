Task ID: E-02 / O-02 bug fixes; owner: E implementation; reviewer: D / A (requested, not independently reviewed)
deliverable/path: web/src/screens/FireMap.tsx, tests/test_fire_map_provinces.py, tests/test_fire_map_tooltips.py
run/version ID: integrated with origin/main 9ab536e723736874f78751659f04e88dbb3ec8d7; input hashes: not applicable (UI-only changes)

Changes:
- Completed REGIONS and ISLANDS with all 38 provinces, including Jawa Barat. Preserved five existing analysis preset mappings and Papua Selatan (Merauke). Corrected Kepulauan Bangka Belitung.
- Checked province membership against https://wilayah.id/api/provinces.json, preserving the app's DI Yogyakarta label. New approximate navigation centers checked against Indonesia administrative-level-1 rows in https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/states.json.
- Removed the full-grid background tooltip; heat-cell tooltips remain anchored, not cursor-following. Heat-cell and empty-grid click inspection remain.
- Shared the existing canvas between grid and dots: separate canvases accumulated during rerenders and intermittently intercepted heat-cell input.
- Integrated on a clean worktree based on the latest remote main. Preserved remote AI analyzer features; excluded unrelated local backend/environment changes. No secret files read or staged.

Verification evidence:
- Regression checks failed before the relevant fixes: incomplete province catalog, background tooltip, multiple canvas creation sites. All pass afterward with python3 tests/test_fire_map_provinces.py and python3 tests/test_fire_map_tooltips.py.
- npm run build: exit 0; TypeScript/Vite production build succeeds, existing large-chunk warning remains.
- Firefox headless WebDriver BiDi against the merged frontend at http://127.0.0.1:5174/: all 38 provinces searchable, mixed-case jAwA bArAt matches, selection pans to Jawa Barat. Real pointer hover opens an anchored heat-cell tooltip and closes it on exit; empty grid has no tooltip. Real pointer clicks on heat cells and empty grid open the inspector; repeating clicks clears selection. One map canvas after repeated grid rerenders. Browser error logs: []. Temporary harness: /home/akirametakunai/.hermes/cache/scratch/emberline-bidi.mjs.
- git diff --check: exit 0.
- PYTHONDONTWRITEBYTECODE=1 make test PYTHON=/home/akirametakunai/Projects/emberline/.venv/bin/python: API tests 3/3, protocol checks 64/64, grid/matching checks 29/29 pass. Stops at baseline leakage 12/13 because data/processed/riau/c02/matched_pairs.csv is absent in the clean checkout, as in the original local checkout. No fabricated cache, no science artifacts regenerated.

limitations: Full science suite blocked by missing processed data. Browser QA used the already-running local artifact API, not a deployed environment; it verifies interaction, not scientific validity. Province navigation does not establish province-wide science coverage. No deployment or independent reviewer approval claimed. Existing artifact API labels some presets FIXTURE_SYNTHETIC.
requested reviewer action: D / A verify province list, heat-cell hover/click behavior and preservation of newer remote features; next dependency: restore processed Riau data for full science suite and follow normal release/deployment review.
