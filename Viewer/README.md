# SDP results viewer

Interactive viewer for the SDP sweep results in [`../sdp_results/`](../sdp_results),
replacing the one-off matplotlib cells in `notebook_utils/plot_results.py` / `sdp.ipynb`.

Drop `.jsonl` files in, tick the ones to show, rename them for the legend, recolor them,
and read the plot. Everything runs in the browser — no backend, no network, no upload.

## Run

```bash
npm install && npm run dev
```

Then open the printed URL and drop files from `sdp_results/` onto the sidebar.

```bash
npm run build
```

## What it does

- **Line mode** — `Et_lower` against `p` on a log y axis, one series per file, markers
  shaped by separability verdict (● entangled, ◇ inconclusive, ✕ separable). A sweep
  testing Schmidt number *r* carries *r − 1* bounds and draws one curve per *t*, in the
  file's color, told apart by line pattern.
- **Histogram mode** — one bar per curve at its largest `Et_lower`, log y.
- **Schmidt no. mode** — `minSchmidtNumber` against `p`, the viewer's version of
  `plot_schmidt_number`.
- **Show upper bound** — overlays `Et_upper` as a dashed curve in the same color, for the
  files that have one (the `*_lam21` sweeps do not).
- **Show separable states** — off keeps entangled and inconclusive points only; the line
  breaks at the gaps rather than bridging them.
- **Value used for zero** — the log axis cannot draw 0, so anything ≤ 0 is pinned to this
  value (the notebook's `zero_at`, now editable). A dotted guide line marks it.
- **X-axis range** — both ends optional; left empty they fit the loaded sweeps, which
  cover very different ranges of `p` (`Ncomms6297_with_noise` stops at 0.06, the `convex_*`
  files run to 1). The y axis rescales to what is in view.
- Files, legend names, colors and settings persist in `localStorage` across reloads.

The record schema is `SdpResult` from `notebook_utils/load_store_results.py`
(`{p, separability, minSchmidtNumber, objective, Et_lower[], objective_max, Et_upper[]}`).
Files still written in the old `{obj, separable, Etl, Etu}` schema are rejected with a
visible error row, as are 2-D `{x, y}` files.

[`SPEC.md`](SPEC.md) has the full data contract and behavior spec.

## Layout

`src/lib/buildTraces.ts` holds all the plotting logic as a pure
`(files, settings) → figure` function that imports nothing from Plotly.
`src/components/PlotView.tsx` is the only Plotly-aware component.
