# SDP Results Viewer — Specification

An interactive, fully client-side viewer for the SDP sweep results in
`../sdp_results/`. It replaces the one-off matplotlib cells in `sdp_graphs.ipynb` /
`sdp.ipynb`: drop result files in, tick the ones to show, rename them for the legend,
recolor them, and read the plot.

Stack: Vite + React + TypeScript, Plotly.js for rendering. No backend, no network calls.

---

## 1. Data contract

### 1.1 Accepted format

JSONL — one compact JSON object per line, no header, no trailing commas. Blank lines are
ignored. `.json` files containing a JSON array of the same records are also accepted.

The **1-D schema** is the only supported one:

```json
{"p": 0.75, "obj": -1.62e-08, "separable": 1, "Etl": 0.0, "obj_max": 0.3333, "Etu": 1.0}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `p` | `number` in [0, 1] | The x-axis parameter (mixing weight of the convex combination). **Does not always start at 0** — e.g. `chessboard_maxmixed_m3_k2.jsonl` spans [0.75, 1.0]. For `C3C3_horodecki` it is the Horodecki parameter `a`. |
| `obj` | `number \| null` | Raw SDP optimum. May be slightly negative (numerical noise). Not plotted; shown in the tooltip. |
| `separable` | `0 \| 1 \| 2` | Verdict from `toqito`'s `is_separable`. **0 = entangled, 1 = inconclusive, 2 = separable.** Note the inversion: `2`, not `1`, means separable. |
| `Etl` | `number ≥ 0 \| null` | Lower bound on `E_t`. **This is the plotted quantity.** `0.0` means "not certified entangled by the SDP". |
| `obj_max` | `number \| null` | Intermediate quantity (k = 2 only). Not plotted. |
| `Etu` | `number \| null` | Upper bound on `E_t` (k = 2 only). Is `1.0` for nearly every point in the current data — a flat upper-bound line at 1 is expected, not a bug. |

`null` on disk is the encoding of NaN.

### 1.2 Rejected format

The `*_2d.jsonl` files use a different schema (`{x, y, obj, separable, Etl}`) and are
**out of scope**. Dropping one produces a red error row in the sidebar reading
*"2-D result files are not supported"* — never a crash.

### 1.3 Parsing rules

1. Split on newlines, skip blanks, `JSON.parse` each line.
2. If a record has `x` and `y` but no `p` → reject the whole file as 2-D.
3. If a record lacks a numeric `p`, or lacks an `Etl` key → reject the file with a
   message naming the offending line number.
4. `obj`, `Etl`, `obj_max`, `Etu` are normalised to `number | null`. `null` is kept
   distinct from `0` in the data model; both are floored at plot time (§3.1).
5. `separable` is coerced to `0 | 1 | 2`; anything else → `1` (inconclusive).
6. Records are **sorted ascending by `p`** after parsing. The notebook does the same,
   noting the sweep is not necessarily stored in ascending order.
7. A file that parses to zero records is rejected.

Files hold 11–101 records. Some files are entirely `Etl == 0` (`random_PPT_m3_k2`,
`pianni_maxmixed_m4_k2`) — such a series must render fine, flat on the floor line.

### 1.4 Default legend name

Derived from the filename, mirroring `_pretty_label` in the notebook:

1. strip the `.jsonl` / `.json` extension
2. strip a trailing `_2d`
3. strip a trailing `_m<digits>_k<digits>`
4. replace `_` and `-` with spaces

`C3C3_horodecki_m3_k2.jsonl` → `C3C3 horodecki`.

---

## 2. Application state

```ts
type Verdict = 0 | 1 | 2;              // 0 entangled, 1 inconclusive, 2 separable

interface Record1D {
  p: number;
  obj: number | null;
  separable: Verdict;
  Etl: number | null;
  obj_max: number | null;
  Etu: number | null;
}

interface DataFile {
  id: string;          // crypto.randomUUID()
  fileName: string;    // original filename, shown as the row subtitle
  label: string;       // editable legend name, defaults to prettyLabel(fileName)
  color: string;       // hex, cycled from the palette when the file is added
  visible: boolean;    // the per-file "show its content" checkbox
  records: Record1D[]; // sorted ascending by p; empty when error is set
  error?: string;      // set instead of records when parsing failed
}

interface Settings {
  chartMode: 'line' | 'histogram';
  showUpperBound: boolean;  // default false
  showSeparable: boolean;   // default true
  zeroFloor: number;        // default 1e-6
  zeroFloorText: string;    // raw input text, so typing "1e-" does not destroy state
  xMin: number;             // default 0; the x axis always ends at 1
}
```

### 2.1 Persistence

The whole state (files, including their parsed records, plus settings) is written to
`localStorage` under the key `sdp-viewer-v1`, debounced ~300 ms. It is restored on load,
so dropped files and their names/colors survive a page reload. Writes are wrapped in
`try/catch`: on a quota error the app shows a non-blocking warning rather than crashing.
All 48 result files together are well under 1 MB, comfortably inside the ~5 MB budget.

"Clear all" (with confirmation) empties both the view and the stored state.

---

## 3. Plotting

### 3.1 The zero floor

The y axis is **log scale**, so non-positive values cannot be drawn. Following the
notebook's `eps = 1e-6`:

```
floor(v) = (v === null || v <= 0) ? zeroFloor : v
```

`zeroFloor` defaults to `1e-6` and is user-editable (§4.2). It applies to both `Etl` and
`Etu`. The tooltip always reports the *true* pre-floor value, printing `0` for a floored
point, so the substitution is never mistaken for real data.

A dotted gray guide line is drawn across the plot at `zeroFloor`, labelled *"values ≤ 0
pinned here"*, so a series lying flat on it reads as pinned rather than as data. Note
that a value can be genuinely positive and still fall *below* the floor (`Etl ≈ 1e-7`
happens near `p = 1` in `C3C3_horodecki`); only values `≤ 0` are moved.

### 3.2 The "show separable states" toggle

- **On** (default): every record is plotted, with the verdict encoded in the marker
  symbol.
- **Off**: records with `separable !== 0` are removed — only certified-entangled points
  remain.

Removed points become `y = null` **in place** rather than being deleted, and traces set
`connectgaps: false`. The connecting line therefore **breaks at the gaps**, showing
honestly where data was filtered out instead of bridging across it.

### 3.3 Encoding

Because per-file color inputs are a hard requirement, **color identifies the file** (not
the verdict, as the notebook did). The verdict moves to the **marker symbol**, keeping
the three shapes matplotlib used:

| `separable` | Meaning | Symbol |
| --- | --- | --- |
| 0 | entangled | `circle` ● |
| 1 | inconclusive | `hexagon` ⬡ |
| 2 | separable | `x-thin` ✕ |

A small static key sits under the plot, shown only in line mode with "show separable
states" on. Its glyphs are inline SVG, not unicode characters — the hexagon has no
reliable glyph across fonts.

Default series colors are **not** the notebook's `_OVERLAY_COLORS` (matplotlib tab10):
that set fails a colorblind-separation check, with `#ff7f0e` and `#2ca02c` collapsing to
ΔE 0.7 under protanopia. `src/lib/palette.ts` uses an Okabe-Ito-derived order that passes
lightness, chroma, CVD and normal-vision separation on a light surface. Every color is
user-overridable regardless.

### 3.4 Line mode

Per **visible** file, up to two traces:

- **Lower bound** — `mode: 'lines+markers'`, solid line in the file's color, per-point
  marker symbols per §3.3, `name` = the file's legend label, `connectgaps: false`.
- **Upper bound** — drawn only when the global "show upper bound" toggle is on, and only
  for files that have at least one non-null `Etu`. Same x values, `floor(Etu)` as y,
  **dashed** line in the same file color, `triangle-up` markers. It shares a
  `legendgroup` with the lower-bound trace and sets `showlegend: false`, so the legend
  keeps one entry per file and clicking it toggles both curves together.

Layout:

- `yaxis`: `type: 'log'`, title `E_t bound (log scale)`, autoranged, ticks as powers of
  ten (`exponentformat: 'power'`) rather than Plotly's default SI prefixes.
- `xaxis`: `range: [xMin, 1]` — the end is always 1; only the start is configurable.
  Series are **trimmed** to `p ≥ xMin` (keeping the one record immediately to the left so
  the curve still enters from the edge). Without the trim, Plotly auto-ranges y over
  points scrolled past, and raising the x start stops zooming the plot vertically.
- Dashed grid on both axes, `hovermode: 'closest'`, `uirevision` set so redraws caused by
  a settings change do not reset a manual zoom.

### 3.5 Histogram mode

One **vertical bar per visible file**, at that file's **largest `Etl`** over its records
*after* the separable filter (§3.2) is applied, floored per §3.1. Log y axis, decades
only (`dtick: 1`), powers-of-ten ticks.

- Bar color = the file's color; x-axis category label = the file's legend label.
- Every bar carries its value as a label above it; a bar whose true maximum is `<= 0`
  reads `0` (as `plot_Etl_points` does in the notebook). The y range is padded a third
  of a decade below the floor so a floored bar still shows a labelled stub.
- When "show upper bound" is on, a second grouped bar per file shows `Etu` **at the
  record that attained the maximum `Etl`**. It is drawn hatched (`pattern.shape: '/'`)
  on white, because both bars of a pair share the file's color and the legend swatches
  would otherwise be identical.
- The `xMin` setting is **ignored** here — the histogram has no `p` axis for that window
  to mean anything, so the maximum is always taken over the whole sweep.
- Files left with no records after filtering are skipped, with a note in the sidebar.

---

## 4. User interface

Two-column layout: a fixed ~320 px sidebar on the left, the plot filling the remaining
width on the right and resizing with the window.

### 4.1 Sidebar — file drop

A dashed rounded drop area at the top. Accepts a multi-file drag-and-drop, highlights on
drag-over, and is also clickable to open a file picker
(`<input type="file" multiple accept=".jsonl,.json">`). Files are read in the browser
with `File.text()` and never leave the machine.

### 4.2 Sidebar — global controls

| Control | Type | Default | Notes |
| --- | --- | --- | --- |
| Chart type | segmented: Line / Histogram | Line | |
| Show upper bound | checkbox | off | Global; applies to every visible file |
| Show separable states | checkbox | on | Help text: *off = only certified-entangled points* |
| Zero floor | text input | `1e-6` | Accepts `1e-6` or `0.000001`. Invalid input outlines the field red and keeps the last valid value |
| X-axis start | number input, step 0.05, range 0–0.99 | `0` | Help text: *ends at 1* |
| Clear all | button | — | Confirms, then wipes files and `localStorage` |

### 4.3 Sidebar — file list

One row per added file:

- visibility checkbox — "show its content"
- text input — the legend name (editable, defaults per §1.4)
- color input (`<input type="color">`) — the series color
- remove (×) button
- a muted second line with the source filename and record count

A file that failed to parse renders as a red row showing the message and only the ×
button.

### 4.4 Plot area

The Plotly chart, the symbol key (§3.3), and — when nothing has been added — the empty
state: *"Drop `.jsonl` files from `sdp_results/` to begin."*

Styling is plain CSS with a system font stack; no CSS framework.

---

## 5. Module layout

```
Viewer/
  SPEC.md  README.md  index.html  package.json  vite.config.ts  tsconfig*.json
  src/
    main.tsx  App.tsx  styles.css  plotly.d.ts
    types.ts                     Record1D, DataFile, Settings, AppState, Action
    lib/
      parseJsonl.ts              text + filename -> DataFile
      prettyLabel.ts             filename -> default legend name
      palette.ts                 series colors (the notebook's _OVERLAY_COLORS)
      buildTraces.ts             (files, settings) -> { data, layout }   [pure]
      usePersistedState.ts       localStorage-backed reducer wrapper
    components/
      Sidebar.tsx  DropZone.tsx  GlobalControls.tsx  FileRow.tsx  PlotView.tsx
```

`buildTraces.ts` holds all the plotting logic and imports nothing from Plotly, so it
stays a pure, testable function. `PlotView.tsx` is the only Plotly-aware component: it
calls `Plotly.react` in an effect keyed on the computed traces, `Plotly.purge` on
unmount, and drives `Plotly.Plots.resize` from a `ResizeObserver`.

---

## 6. Verification

```bash
npm install && npm run dev
```

Drop these four files from `../sdp_results/`; each targets a different edge case.

| File | What it checks |
| --- | --- |
| `C3C3_horodecki_m3_k2.jsonl` | The only file with non-trivial `Etu` (14 points below 1.0, at `p ≤ 0.13`). Toggling the upper bound must show a dashed curve that is *not* flat at 1. |
| `chessboard_maxmixed_m3_k2.jsonl` | Starts at `p = 0.75`; its line must begin mid-axis, not be stretched or error. |
| `random_PPT_m3_k2.jsonl` | Every `Etl` is 0 — the series sits flat on the floor line; changing the floor to `1e-8` moves it; turning off "show separable states" makes it vanish entirely (it is 100 % `separable == 1`). |
| `yu_oh_m3_k2_2d.jsonl` | Must produce the red "2-D result files are not supported" row. |

Also confirm: the y axis rescales when the x-axis start is raised; renaming and recoloring a file updates the legend and both its traces;
setting the x-axis start to 0.5 clips the axis without dropping data; histogram mode
gives one log-scaled bar per file with `random_PPT` at the floor labelled `0`; a page
reload restores files, names, colors and settings; "Clear all" empties everything.

```bash
npm run build
```
