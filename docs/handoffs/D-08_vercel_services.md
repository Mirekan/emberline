# D-08 Vercel services deploy — live at https://www.emberline.earth

One Vercel project now serves both halves of the repository: the FastAPI API under
`/api/*` and the Vite SPA everywhere else. Deployment `dpl_A35QnWMSD492fH39ozZgMUTVaKQV`,
`READY`, target `production`, aliased to `www.emberline.earth`; `emberline.earth` 308-redirects to it.

## Configuration

`vercel.json` (repository root):

- service `api`: `root` `.`, `framework` `fastapi`, `entrypoint` `app.py`. Rooted at the repository
  root on purpose — `api/app.py:31` computes `ROOT = Path(__file__).resolve().parents[1]`, so a
  service rooted at `api/` (the former `emberline-u6pu` setting) resolves `artifacts/` and
  `config/aois.yaml` outside the bundle. That was the D-07 failure; the root `app.py` shim keeps
  `parents[1]` correct.
- service `web`: `root` `web`, `framework` `vite`.
- rewrites, most specific first: `/api/(.*)` → `api`, `/(.*)` → `web`. The catch-all must target
  `web`: the API has no `/` route (`api/app.py` routes are all `/api/*`), so a catch-all to `api`
  returns a JSON 404 for the SPA's pages.
- no `bindings`. Bindings inject an internal URL into a function at runtime; the only cross-service
  caller here is browser code, which cannot read them, and the API calls no sibling service. Same
  origin plus the `/api/*` rewrite is the correct wiring, so `web/src/api.ts` now fetches relative
  paths instead of the old absolute `https://emberline-u6pu.vercel.app`.

`web/src/api.ts`: `API_BASE_URL` constant deleted, `fetch(API_BASE_URL + path)` → `fetch(path)`.
The two POST calls were already relative. Vite's dev proxy (`127.0.0.1:8300`) is unaffected.

`.vercelignore` (new) keeps `api/target` (295M of Rust build output), `web/dist`, `node_modules`,
`data`, and `.env*` out of the upload. Without it, `vercel deploy` uploaded `api/target`.

Project `emberline` dashboard settings changed via API (not visible in git): `rootDirectory`,
`framework`, `buildCommand`, `outputDirectory`, `installCommand`, `devCommand` all cleared. They
were `web` + `Vite`, which overrides `vercel.json` and would have deployed the SPA alone.

## Verification (observed, production)

- `https://www.emberline.earth/` → 200 `text/html`; `/assets/index-D-jlzGBx.js` → 200, 1,674,843 B.
- Deployed JS contains `"/api/health"`, `"/api/aoi/presets"`, `"/api/ai/analyze-hotspot"` and zero
  occurrences of `emberline-u6pu` — the old hardcoded host is not in the shipped bundle.
- `/api/health` → 200, 16 AOIs with artifacts; `/api/aoi/presets` → 200, 4,225 B.
- `/api/aoi/riau/{calendar,windows,grid}` → 200 (917,895 / 1,804 / 250,571 B).
- `/api/aoi/nope/calendar` → 404 with the application's own message; rewrites pass `/api` through
  unchanged, so the backend keeps its `/api/*` route prefix.
- CORS preflight (`OPTIONS /api/aoi/analyze`, `Origin: https://example.com`,
  `Access-Control-Request-Headers: content-type`) → 200, `access-control-allow-origin: *`;
  normal GET also returns `*`. `allow_credentials` stays false, which is the only safe pairing for
  a wildcard.
- `POST /api/ai/analyze-hotspot` with a synthetic hotspot → 200, `provider: "heuristic"`. That is
  the proof `api/.env` did not ship: with a key present `_get_grok_key` would have selected
  `groq`/`grok` and spent quota. `GROK_API_KEY` is deliberately NOT set on the project.

Verified locally before deploy: `npm run build` (tsc + vite) clean; root entrypoint serves
`/api/health`, `/api/aoi/presets`, `/api/aoi/riau/{calendar,windows,grid}`, `/api/method?aoi=riau`
all 200 and `/` 404.

## Outstanding

- Repository changes were committed as `fa6cb83` and pushed. The project is git-connected
  (`iwansal64/emberline`, production branch `main`), so pushes deploy automatically. A git
  deployment of a commit lacking `vercel.json` fails with
  `STATIC_BUILD_NO_OUT_DIR: No Output Directory named "public" found after the Build completed` —
  with no services config Vercel falls back to a static build and looks for `public/`. `vercel.json`
  must stay committed at the repository root.
- Project `emberline-u6pu` still exists with `rootDirectory: api`, is git-connected to the same
  repository, and rebuilds on every push, serving the D-07 broken build. Nothing references it;
  delete or disconnect it deliberately.
