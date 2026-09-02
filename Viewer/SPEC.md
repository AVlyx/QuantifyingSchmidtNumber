# SDP Results Viewer — Specification

An interactive, fully client-side viewer for the SDP sweep results in
`../sdp_results/`. It replaces the one-off matplotlib cells in `notebook_utils/plot_results.py`
/ `sdp.ipynb`: tick sweeps in the sidebar, rename them for the legend, recolor them, and
read the plot. `sdp_results/` ships with the app, so it opens with every sweep already
listed; a file that is not committed yet can still be dropped in by hand.

Stack: Vite + React + TypeScript, Plotly.js for rendering. No backend; the only network
calls fetch the bundled result files from the app's own origin.

---

## 1. Data contract

### 1.1 Accepted format

JSONL — one compact JSON object per line, no header, no trailing commas. Blank lines are
ignored. `.json` files containing a JSON array of the same records are also accepted.

The schema is `SdpResult` from `notebook_utils/load_store_results.py`, written by
`save_result`:

```json
{"p":0.02,"separability":0,"minSchmidtNumber":2,"objective":9.1e-05,"Et_lower":[9.1e-05],"objective_max":0.0778,"Et_upper":[0.085]}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `p` | `number` | The x-axis parameter. **Neither end is fixed** — `Ncomms6297_with_noise` spans [0, 0.06], `c2c2_Isotropic` spans [0.333, 0.983], the `convex_*` files span [0, 1]. For `c3c3_Horodecki` it is the Horodecki parameter `a`. |
| `separability` | `0 \| 1 \| 2` | Verdict from `toqito`'s `is_separable`. **0 = entangled, 1 = inconclusive, 2 = separable.** Note the inversion: `2`, not `1`, means separable. |
| `minSchmidtNumber` | `number` | Schmidt number certified at this point: the sweep's `SN_tested_for` when the SDP certified entanglement, otherwise `1`. |
| `objective` | `number \| null` | Raw SDP optimum. May be slightly negative (numerical noise). Not plotted; shown in the tooltip. |
| `Et_lower` | `(number \| null)[]` | Lower bounds on `E_t` — **the plotted quantity**. One entry per `t`, **index `i` holding `t = i + 1`**, so a sweep testing Schmidt number `r` carries `r - 1` of them. `0.0` means "not certified entangled by the SDP". |
| `objective_max` | `number \| null` | Intermediate quantity, computed only when `compute_upper` was on (k = 2). Not plotted. |
| `Et_upper` | `(number \| null)[]` | Upper bounds on `E_t`, indexed like `Et_lower`. `[null]` throughout every `*_lam21` file, since `SDP_max` is not implemented for those. |

`null` on disk is the encoding of NaN.

In the current data every file carries a single `Et_lower` entry except
`c3c3_isotropicSN3.jsonl`, which tests Schmidt number 3 and so carries two (`t = 1` and
`t = 2`). Every `Et_upper` is length 1.

### 1.2 Rejected formats

- The old record schema (`{p, obj, separable, Etl, obj_max, Etu}`) is rejected by name with
  *"Old result schema (Etl/Etu) — rerun the sweep to get Et_lower/Et_upper"*, rather than
  silently drawing an empty plot.
- A 2-D schema (`{x, y, …}` with no `p`) produces *"2-D result files are not supported"*.

Both are red error rows in the sidebar — never a crash.

### 1.3 Parsing rules

1. Split on newlines, skip blanks, `JSON.parse` each line.
2. If a record has `x` and `y` but no `p` → reject the whole file as 2-D.
3. If a record lacks a numeric `p`, or lacks an `Et_lower` key → reject the file with a
   message naming the offending line number (or the stale-schema message of §1.2).
4. `objective`, `objective_max` and every entry of `Et_lower` / `Et_upper` are normalised
   to `number | null`; a bare number in place of a list is accepted as a one-element list.
   `null` is kept distinct from `0` in the data model; both are floored at plot time (§3.1).
5. `separability` is coerced to `0 | 1 | 2`; anything else → `1` (inconclusive).
6. Records are **sorted ascending by `p`** after parsing, as the notebook sorts them too.
7. A file that parses to zero records is rejected.

Files hold 1–61 records. `Piani_with_noise` and `Smolin_with_noise` hold a single
separable point each, with `Et_lower: [0]` — such a series must render fine, one marker on
the floor line.

### 1.4 Default legend name

Derived from the filename:

1. strip the `.jsonl` / `.json` extension
2. peel off a trailing `_lam<digits>` and re-spell it as the partition it encodes
3. replace `_` and `-` with spaces

`convex_Chessboard_Tiles_lam21.jsonl` → `convex Chessboard Tiles λ=(2,1)`.

---

## 2. Application state

```ts
type Verdict = 0 | 1 | 2;              // 0 entangled, 1 inconclusive, 2 separable

interface Record1D {
  p: number;
  separability: Verdict;
  minSchmidtNumber: number | null;
  objective: number | null;
  Et_lower: (number | null)[];   // index i holds t = i + 1
  objective_max: number | null;
  Et_upper: (number | null)[];
}

interface DataFile {
  id: string;          // "<folder>/<name>" for a catalog file, crypto.randomUUID() for an upload
  source: 'catalog' | 'upload';
  folder: string;      // sdp_results/ folder, or UPLOADS_FOLDER ("Added by you")
  fileName: string;    // original filename, shown as the row subtitle
  label: string;       // editable legend name, defaults to prettyLabel(fileName)
  color: string;       // hex, cycled from the palette when the file is added
  visible: boolean;    // the per-file "show its content" checkbox
  records: Record1D[]; // sorted ascending by p; empty when error is set or not loaded yet
  error?: string;      // set instead of records when parsing or fetching failed
  loaded: boolean;     // false for a catalog file whose records are still being fetched
}

interface Settings {
  chartMode: 'line' | 'histogram' | 'schmidt';
  showUpperBound: boolean;   // default false
  showSeparable: boolean;    // default true
  zeroFloor: number;         // default 1e-6
  zeroFloorText: string;     // raw input text, so typing "1e-" does not destroy state
  xMin: number | null;       // null = fit the data
  xMax: number | null;       // null = fit the data
}
```

### 2.1 Persistence

State (files, settings, and which folder sections are collapsed) is written to
`localStorage` under the key `sdp-viewer-v3`, debounced ~300 ms, and restored on load, so
the chosen sweeps and their names/colors survive a page reload. Writes are wrapped in
`try/catch`: on a quota error the app shows a non-blocking warning rather than crashing.

Catalog files are stored **without** their records (`records: []`, `loaded: false`): the
data is already served with the app, so an effect in `App.tsx` re-fetches every unloaded
catalog file on mount, guarded by an in-flight set so each is fetched once. Uploaded files
have no other home and are stored whole.

The key is versioned: a `v2` payload has no `source`/`folder`/`loaded` on its files, so
bumping the key drops it instead of restoring rows this build cannot interpret.

"Clear all" (with confirmation) empties both the view and the stored state.

---

## 3. Plotting

### 3.1 The zero floor

The y axis is **log scale**, so non-positive values cannot be drawn. Following the
notebook's `zero_at`:

```
floor(v) = (v === null || v <= 0) ? zeroFloor : v
```

`zeroFloor` defaults to `1e-6` and is user-editable (§4.2). It applies to both `Et_lower`
and `Et_upper`. The tooltip always reports the *true* pre-floor value, printing `0` for a
floored point, so the substitution is never mistaken for real data.

A dotted gray guide line is drawn across the plot at `zeroFloor`, labelled *"values ≤ 0
pinned here"*, so a series lying flat on it reads as pinned rather than as data. Note
that a value can be genuinely positive and still fall *below* the floor (`Et_lower ≈ 1e-7`
happens near `p = 1` in `c3c3_Horodecki`); only values `≤ 0` are moved.

### 3.2 The "show separable states" toggle

- **On** (default): every record is plotted, with the verdict encoded in the marker
  symbol.
- **Off**: records with `separability === 2` are removed — inconclusive points stay.

Removed points become `y = null` **in place** rather than being deleted, and traces set
`connectgaps: false`. The connecting line therefore **breaks at the gaps**, showing
honestly where data was filtered out instead of bridging across it.

### 3.3 Encoding

Because per-file color inputs are a hard requirement, **color identifies the file** (not
the verdict, as the notebook did). The verdict moves to the **marker symbol**:

| `separability` | Meaning | Symbol |
| --- | --- | --- |
| 0 | entangled | `circle` ● |
| 1 | inconclusive | `diamond-open` ◇ |
| 2 | separable | `x-thin` ✕ |

A small static key sits under the plot in line and Schmidt-number mode. Its glyphs are
inline SVG, not unicode characters — no unicode glyph matches the plotly symbols closely
enough to be read as the same mark.

Where a file carries several `Et_lower` entries, all of them keep the file's color and are
told apart by **line pattern** (`solid`, `dot`, `longdashdot`, …) with the legend name
suffixed `· E₁`, `· E₂`. Plain `dash` is reserved for upper bounds.

Default series colors are **not** matplotlib tab10: that set fails a colorblind-separation
check, with `#ff7f0e` and `#2ca02c` collapsing to ΔE 0.7 under protanopia.
`src/lib/palette.ts` uses an Okabe-Ito-derived order that passes lightness, chroma, CVD and
normal-vision separation on a light surface. Every color is user-overridable regardless.

### 3.4 Line mode

Per **visible** file, per `Et_lower` component `t`, up to two traces:

- **Lower bound** — `mode: 'lines+markers'`, the file's color, line pattern per component
  (§3.3), per-point marker symbols per §3.3, `connectgaps: false`. The tooltip carries the
  true `Et_lower`, `objective`, `minSchmidtNumber` and the verdict.
- **Upper bound** — drawn only when the global "show upper bound" toggle is on, and only
  for components that have at least one non-null `Et_upper` (so the `*_lam21` files draw
  none). Same x values, `floor(Et_upper[t])` as y, **dashed** line in the same file color,
  `triangle-up` markers. It shares a `legendgroup` with its lower-bound trace and sets
  `showlegend: false`, so the legend keeps one entry per curve and clicking it toggles both.

Layout:

- `yaxis`: `type: 'log'`, title `E_t bound (log scale)`, autoranged, ticks as powers of
  ten (`exponentformat: 'power'`) rather than Plotly's default SI prefixes.
- `xaxis`: `[xMin, xMax]`, each end falling back to the extent of the loaded data when left
  unset (§4.2). Series are **trimmed** to the window (keeping the one record immediately
  outside each end so the curve still enters from the edge). Without the trim, Plotly
  auto-ranges y over points scrolled past, and narrowing the window stops zooming the plot
  vertically.
- Dashed grid on both axes, `hovermode: 'closest'`, `uirevision` set so redraws caused by
  a settings change do not reset a manual zoom.

### 3.5 Histogram mode

One **vertical bar per visible file and `Et_lower` component**, at that component's
**largest value** over its records *after* the separable filter (§3.2) is applied, floored
per §3.1. Log y axis, decades only (`dtick: 1`), powers-of-ten ticks.

- Bar color = the file's color; x-axis category label = the file's legend label, suffixed
  `· E1` / `· E2` only when the file has more than one component (the category axis takes
  plain text, not the `<sub>` markup the legend accepts).
- Every bar carries its value as a label above it; a bar whose true maximum is `<= 0`
  reads `0`. The y range is padded a third of a decade below the floor so a floored bar
  still shows a labelled stub.
- When "show upper bound" is on, a second grouped bar per component shows `Et_upper` **at
  the record that attained the maximum**. It is drawn hatched (`pattern.shape: '/'`) on
  white, because both bars of a pair share the file's color and the legend swatches would
  otherwise be identical.
- The x window is **ignored** here — the histogram has no `p` axis for it to mean anything,
  so the maximum is always taken over the whole sweep.
- Files left with no records after filtering are skipped, with a note in the sidebar.

### 3.6 Schmidt-number mode

The viewer's version of `plot_schmidt_number`: `minSchmidtNumber` against `p`, one series
per visible file in its color, markers carrying the verdict exactly as in line mode and a
thin connecting line. The y axis is **linear with `dtick: 1`** and padded half a step at
each end, so an integer-valued quantity never lands on the frame or draws a `1.5` tick.
The x axis and the separable filter behave as in line mode; the zero floor and the upper
bound have nothing to act on here, and their controls are hidden.

---

## 4. User interface

Two-column layout: a fixed ~320 px sidebar on the left, the plot filling the remaining
width on the right and resizing with the window.

### 4.1 Sidebar — the `sdp_results/` catalog

Below the global controls, one collapsible section per folder in
`sdp_results/manifest.json`, in the manifest's order (`noise`, `vertex`, `lam21`, `convex`,
`SN3`, `Parametric`, `test`, then any other folder alphabetically, with loose files at the
root shown as *ungrouped*). Each header carries a caret, the folder name, and either the
file count or `shown/total` once something in it is on screen; clicking toggles the section
and the choice persists.

An untouched file is one compact line: checkbox, name, size. Ticking it fetches
`sdp_results/<folder>/<name>` and expands the row into the full controls of section 4.3.

Files the user drops in appear in a final **"Added by you"** section, built from the series
themselves since they have no manifest entry.

### 4.1.1 Sidebar — add your own

A `<details>` at the bottom of the sidebar holding a dashed drop area. Accepts a multi-file
drag-and-drop, highlights on drag-over, and is also clickable to open a file picker
(`<input type="file" multiple accept=".jsonl,.json">`). Files are read in the browser
with `File.text()` and never leave the machine.

### 4.2 Sidebar — global controls

| Control | Type | Default | Notes |
| --- | --- | --- | --- |
| Chart type | segmented: Line / Histogram / Schmidt no. | Line | |
| Show upper bound | checkbox | off | Global; applies to every visible file. Hidden in Schmidt-number mode |
| Show separable states | checkbox | on | Help text: *off = drops certified-separable points; inconclusive ones stay* |
| Value used for zero | text input | `1e-6` | Accepts `1e-6` or `0.000001`. Invalid input outlines the field red and keeps the last valid value. Hidden in Schmidt-number mode |
| X-axis range | two number inputs, step 0.05 | empty / empty | Empty = fit the loaded sweeps. Each end is independent |
| Clear all | button | — | Confirms, then wipes files and `localStorage` |

### 4.3 Sidebar — a picked file's row

One row per ticked file:

- visibility checkbox — "show its content"
- text input — the legend name (editable, defaults per §1.4)
- color input (`<input type="color">`) — the series color
- remove (×) button — for a catalog file this drops the row's name/color back to the
  defaults and unticks it; the file itself stays listed in its folder
- a muted second line with the source filename, the record count, and — for a file with
  more than one `Et_lower` entry — the range of `t` it covers

A file that failed to parse renders as a red row showing the message and only the ×
button.

### 4.4 Plot area

The Plotly chart, the symbol key (§3.3), and — when nothing has been added — the empty
state: *"Tick sweeps in the sidebar to plot them — they come from `sdp_results/`."*

Styling is plain CSS with a system font stack; no CSS framework.

---

## 5. Module layout

```
Viewer/
  SPEC.md  README.md  index.html  package.json  vite.config.ts  tsconfig*.json
  plugins/
    sdpResults.ts                serves ../sdp_results in dev, emits it into dist on build
  src/
    main.tsx  App.tsx  styles.css  plotly.d.ts
    types.ts                     Record1D, DataFile, Settings, AppState, Action
    lib/
      catalog.ts                 manifest + result-file fetching, BASE_URL-aware
      parseJsonl.ts              text -> records, plus componentCount
      prettyLabel.ts             filename -> default legend name
      palette.ts                 series colors
      buildTraces.ts             (files, settings) -> { data, layout }   [pure]
      usePersistedState.ts       localStorage-backed reducer wrapper
    components/
      Sidebar.tsx  FolderSection.tsx  DropZone.tsx
      GlobalControls.tsx  FileRow.tsx  PlotView.tsx
```

### 5.1 Serving `sdp_results/`

`sdp_results/` sits outside `Viewer/`, so it cannot be a `public/` asset. The `sdp-results`
plugin covers both halves:

- **dev** — a `configureServer` middleware answers `/sdp_results/manifest.json` by scanning
  the folder per request (a sweep written while the server runs appears on the next reload)
  and streams `/sdp_results/<folder>/<name>.jsonl` off disk, rejecting anything that walks
  out of the folder or is not a `.jsonl`.
- **build** — `buildStart` emits the same manifest and every `.jsonl` into
  `dist/sdp_results/`, so the GitHub Pages bundle is self-contained.

The client builds URLs from `import.meta.env.BASE_URL` (`/` in dev, `/<repo>/` on Pages)
and escapes each path segment, since one sweep has a space in its name.

`buildTraces.ts` holds all the plotting logic and imports nothing from Plotly, so it
stays a pure, testable function. `PlotView.tsx` is the only Plotly-aware component: it
calls `Plotly.react` in an effect keyed on the computed traces, `Plotly.purge` on
unmount, and drives `Plotly.Plots.resize` from a `ResizeObserver`.

---

## 6. Verification

```bash
npm install && npm run dev
```

Tick these files in the sidebar; each targets a different edge case.

| File | What it checks |
| --- | --- |
| `c3c3_isotropicSN3.jsonl` | The only file with two `Et_lower` entries. It must draw **two** curves in one color, the second dotted, legended `· E₁` and `· E₂`, and give **two** bars in histogram mode. |
| `Ncomms6297_with_noise.jsonl` | Stops at `p = 0.06`. On its own the x axis must fit that span; shown alongside a `convex_*` file (which runs to 1) it must shrink to the left of a full-width axis, and typing an explicit range must override both. |
| `c3c3_Horodecki.jsonl` | The only file with non-trivial `Et_upper` (7 points below 1.0, at `p ≤ 0.12`). Toggling the upper bound must show a dashed curve that is *not* flat at 1. |
| `c3c3_Horodecki_lam21.jsonl` | `Et_upper` is `[null]` throughout — the upper-bound toggle must add nothing for it, silently, while still working for the file above. |
| `Piani_with_noise.jsonl` | A single separable point with `Et_lower: [0]` — one marker on the floor line, which disappears when "show separable states" is turned off. |

Also confirm: Schmidt-number mode draws integer ticks with no `1.5` label and hides the
zero-floor and upper-bound controls; the y axis rescales when the x range is narrowed;
renaming and recoloring a file updates the legend and all of its traces; a page reload
restores files, names, colors and settings; "Clear all" empties everything.

```bash
npm run build
```
