# SDP results viewer

Interactive viewer for the SDP sweep results in [`../sdp_results/`](../sdp_results),
replacing the one-off matplotlib cells in `sdp_graphs.ipynb` / `sdp.ipynb`.

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

- **Line mode** — `Etl` against `p` on a log y axis, one series per file, markers shaped
  by separability verdict (● entangled, ⬡ inconclusive, ✕ separable).
- **Histogram mode** — one bar per file at its largest `Etl`, log y.
- **Show upper bound** — overlays each file's `Etu` as a dashed curve in the same color.
- **Show separable states** — off keeps only certified-entangled points; the line breaks
  at the gaps rather than bridging them.
- **Value used for zero** — the log axis cannot draw 0, so anything ≤ 0 is pinned to this
  value (the notebook's `eps = 1e-6`, now editable). A dotted guide line marks it.
- **X-axis start** — the window always ends at 1; the y axis rescales to what is in view.
- Files, legend names, colors and settings persist in `localStorage` across reloads.

Only the 1-D schema (`{p, obj, separable, Etl, obj_max, Etu}`) is supported. The three
`*_2d.jsonl` files are rejected with a visible error row.

[`SPEC.md`](SPEC.md) has the full data contract and behavior spec.

## Layout

`src/lib/buildTraces.ts` holds all the plotting logic as a pure
`(files, settings) → figure` function that imports nothing from Plotly.
`src/components/PlotView.tsx` is the only Plotly-aware component.
