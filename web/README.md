# web/ — frontend (owner: E)

React/TypeScript + Vite; charts via ECharts; MapLibre only where needed.
Builds against **frozen payload examples** in [`../contracts/`](../contracts/)
with clearly-labeled dev fixtures until D-07 serves real artifacts.

- Every screen: loading / failure / empty / `insufficient_data` / `unsupported` states.
- Uncertainty, gaps, `zero_returned_signal`, and non-leap Feb 29 must render
  **visually distinct** (protocol F-9/F-18).
- Persistent "How to read this" panel; "historical/descriptive, not predictive".
- Accessible at 360px, keyboard-first, target Lighthouse a11y ≥ 90.
- Status: pending — owner tasks E-01…E-06.
