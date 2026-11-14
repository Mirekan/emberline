# web/ — EmberLine frontend (owner E)

Vite + React + TypeScript + Apache ECharts. Design language matches
`docs/ux/design_spec.md` and Figma sections 01–08 (dark instrument theme,
YlOrBr calendar ramp, ember accent, MOCK badge whenever `fixture` is set).

```bash
cd web
npm install
npm run dev        # http://localhost:5173 — /api proxied to 127.0.0.1:8300
npm run build      # production bundle (dist/)
```

The API must be running first: `python -m uvicorn api.app:app --port 8300`.

Payloads follow the frozen examples in [`../contracts/`](../contracts/) —
dev fixtures (FIXTURE_SYNTHETIC) until D-07 serves real artifacts; the
MOCK · SYNTHETIC badge shows whenever `mock: true`.

Screens: Overview · Calendar (366-day heatmap, five cell states —
pattern+text, never color alone) · Compare (raw vs harmonized + interval) ·
Seasons (climatology + critical windows with eligible-year denominators) ·
Method (+ persistent How-to-read drawer, boundary sentences).

Every screen: loading / failure / empty / `insufficient_data` / `unsupported`
states. Uncertainty, gaps, `zero_returned_signal`, and non-leap Feb 29 render
**visually distinct** (protocol F-9/F-18). Accessible at 360px, keyboard-first.
Status: E-01/E-02 shell + screens implemented; E-03…E-06 polish pending.
