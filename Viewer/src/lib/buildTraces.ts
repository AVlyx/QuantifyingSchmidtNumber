import type { DataFile, Record1D, Settings, Verdict } from "../types.ts";
import { VERDICT_LABEL } from "../types.ts";
import { componentCount } from "./parseJsonl.ts";

/** Loose Plotly shapes — `plotly.js-dist-min` ships no types and we only ever hand these straight to it. */
export type Trace = Record<string, unknown>;
export type Layout = Record<string, unknown>;

export interface Figure {
  data: Trace[];
  layout: Layout;
  /** Legend labels of visible files left with nothing to draw after the separable filter. */
  emptyAfterFilter: string[];
  /** Verdicts actually drawn, ascending — the marker key lists these and only these. */
  verdicts: Verdict[];
}

const SURFACE = "#ffffff";
const INK = "#1c1c1a";
const INK_MUTED = "#6b6b66";
const GRID = "#e6e6e2";

/**
 * Marker style per separability verdict. All three points of a series share its color, so the
 * shape carries the verdict on its own: a filled disc, a hollow diamond and a cross are told
 * apart at a glance, where the old circle/hexagon pair read as the same dot at marker size.
 */
export interface VerdictStyle {
  symbol: string;
  size: number;
  /** Stroke-only symbols need the series color to be visible at all; filled ones take a
   *  surface-colored ring so overlapping series stay separable. */
  outline: "series" | "surface";
  outlineWidth: number;
}

export const VERDICT_STYLE: Record<Verdict, VerdictStyle> = {
  0: { symbol: "circle", size: 8, outline: "surface", outlineWidth: 1.5 },
  1: { symbol: "diamond-open", size: 11, outline: "series", outlineWidth: 2 },
  2: { symbol: "x-thin", size: 10, outline: "series", outlineWidth: 2 },
};

/**
 * A file testing Schmidt number r carries r - 1 lower bounds, one per t. They share the
 * file's color, so the line pattern separates them; `dash` is left to the upper bounds.
 */
const COMPONENT_DASH = ["solid", "dot", "longdashdot", "dashdot"];

const sortedVerdicts = (seen: Set<Verdict>): Verdict[] =>
  ([0, 1, 2] as Verdict[]).filter((v) => seen.has(v));

/** Legend name for one t component; unadorned when the file only has the one. */
function seriesName(file: DataFile, index: number, total: number): string {
  return total > 1 ? `${file.label} · E<sub>${index + 1}</sub>` : file.label;
}

/**
 * The notebook's `zero_at` substitution, now user-settable: a log axis cannot draw
 * non-positive values, so they are pinned to the floor.
 */
export function floorValue(v: number | null, zeroFloor: number): number {
  return v === null || v <= 0 ? zeroFloor : v;
}

/** True (pre-floor) value as shown in tooltips, so the substitution is never mistaken for data. */
function fmt(v: number | null): string {
  if (v === null) return "n/a";
  if (v <= 0) return "0";
  if (v >= 1e-3 && v < 1e4) return v.toPrecision(5).replace(/\.?0+$/, "");
  return v.toExponential(4);
}

/** Compact form for bar labels, where a full-precision number is just noise. */
function fmtShort(v: number | null): string {
  if (v === null) return "n/a";
  if (v <= 0) return "0";
  return v >= 1e-3 && v < 1e4 ? String(Number(v.toPrecision(3))) : v.toExponential(2);
}

/** Records kept for plotting; when `showSeparable` is off, certified-separable points are dropped. */
function isKept(rec: Record1D, settings: Settings): boolean {
  return settings.showSeparable || rec.separability !== 2;
}

/**
 * Records within the chosen x window, plus the one immediately outside each end so the curve
 * still enters from the edge. Without this the y axis auto-ranges over points the user has
 * scrolled past, and narrowing the window stops zooming the plot vertically.
 * Records are already sorted ascending by `p`.
 */
function visibleSlice(records: Record1D[], settings: Settings): Record1D[] {
  const { xMin, xMax } = settings;
  if (xMin === null && xMax === null) return records;

  const lo = xMin ?? -Infinity;
  const hi = xMax ?? Infinity;
  const first = records.findIndex((r) => r.p >= lo);
  if (first === -1) return [];
  let last = -1;
  for (let i = records.length - 1; i >= 0; i--) {
    if (records[i].p <= hi) {
      last = i;
      break;
    }
  }
  if (last < first) return [];
  return records.slice(Math.max(0, first - 1), Math.min(records.length, last + 2));
}

/** Span of `p` actually present, used to fit the axis and to stretch the floor line. */
function dataExtent(files: DataFile[]): [number, number] | null {
  let lo = Infinity;
  let hi = -Infinity;
  for (const file of files) {
    for (const rec of file.records) {
      if (rec.p < lo) lo = rec.p;
      if (rec.p > hi) hi = rec.p;
    }
  }
  return lo <= hi ? [lo, hi] : null;
}

/**
 * The x axis. Sweeps span wildly different ranges — `Ncomms6297_with_noise` stops at
 * p = 0.06 where the convex-combination files run to 1 — so an unset bound fits the data
 * instead of defaulting to [0, 1] and squashing the short sweeps into the left edge.
 */
function xAxis(files: DataFile[], settings: Settings): Layout {
  const extent = dataExtent(files);
  const base: Layout = {
    title: { text: "p", font: { size: 13, color: INK_MUTED } },
    gridcolor: GRID,
    griddash: "dash",
    zeroline: false,
    linecolor: GRID,
    ticks: "outside",
    tickcolor: GRID,
    tickfont: { color: INK_MUTED },
  };

  if ((settings.xMin === null && settings.xMax === null) || !extent) {
    return { ...base, autorange: true };
  }
  const [lo, hi] = [settings.xMin ?? extent[0], settings.xMax ?? extent[1]];
  return { ...base, range: lo < hi ? [lo, hi] : [lo, lo + 1e-6] };
}

const baseLayout = (settings: Settings): Layout => ({
  paper_bgcolor: SURFACE,
  plot_bgcolor: SURFACE,
  font: { family: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", size: 13, color: INK },
  margin: { l: 76, r: 28, t: 16, b: 96 },
  hovermode: "closest",
  showlegend: true,
  // Below the plot rather than inside it: an in-plot legend sits exactly where the
  // high-E_t end of these curves lives and hides them.
  legend: {
    orientation: "h",
    x: 0,
    xanchor: "left",
    y: -0.16,
    yanchor: "top",
    font: { size: 12 },
  },
  // Keeps a manual zoom across the redraws caused by settings changes, but resets it
  // when the mode or the x range changes, where a stale zoom would be confusing.
  uirevision: `${settings.chartMode}:${settings.xMin}:${settings.xMax}`,
});

/** Per-point marker spec carrying the verdict as a shape, in the file's color. */
function verdictMarker(records: Record1D[], color: string): Trace {
  return {
    color,
    size: records.map((r) => VERDICT_STYLE[r.separability].size),
    symbol: records.map((r) => VERDICT_STYLE[r.separability].symbol),
    line: {
      color: records.map((r) =>
        VERDICT_STYLE[r.separability].outline === "series" ? color : SURFACE,
      ),
      width: records.map((r) => VERDICT_STYLE[r.separability].outlineWidth),
    },
  };
}

function buildLineFigure(files: DataFile[], settings: Settings): Figure {
  const emptyAfterFilter: string[] = [];
  const data: Trace[] = [];
  const verdicts = new Set<Verdict>();

  for (const file of files) {
    const records = visibleSlice(file.records, settings);
    const kept = records.filter((r) => isKept(r, settings));
    if (kept.length === 0) {
      emptyAfterFilter.push(file.label);
      continue;
    }
    for (const rec of kept) verdicts.add(rec.separability);

    const x = records.map((r) => r.p);
    const total = componentCount(records);

    for (let t = 0; t < total; t++) {
      // Filtered-out points stay in place as nulls so `connectgaps: false` breaks the line
      // exactly where data was dropped, instead of bridging across the hole.
      const y = records.map((r) =>
        isKept(r, settings) ? floorValue(r.Et_lower[t] ?? null, settings.zeroFloor) : null,
      );

      data.push({
        type: "scatter",
        mode: "lines+markers",
        name: seriesName(file, t, total),
        legendgroup: `${file.id}:${t}`,
        x,
        y,
        connectgaps: false,
        line: { color: file.color, width: 2, dash: COMPONENT_DASH[t % COMPONENT_DASH.length] },
        marker: verdictMarker(records, file.color),
        customdata: records.map((r) => [
          fmt(r.Et_lower[t] ?? null),
          VERDICT_LABEL[r.separability],
          fmt(r.objective),
          r.minSchmidtNumber === null ? "n/a" : String(r.minSchmidtNumber),
        ]),
        hovertemplate:
          "<b>%{fullData.name}</b><br>p = %{x}<br>E<sub>t</sub> lower = %{customdata[0]}" +
          "<br>objective = %{customdata[2]}<br>Schmidt number ≥ %{customdata[3]}" +
          "<br>%{customdata[1]}<extra></extra>",
      });

      if (settings.showUpperBound && records.some((r) => (r.Et_upper[t] ?? null) !== null)) {
        data.push({
          type: "scatter",
          mode: "lines+markers",
          name: `${seriesName(file, t, total)} (upper)`,
          legendgroup: `${file.id}:${t}`,
          showlegend: false,
          x,
          y: records.map((r) => {
            const v = r.Et_upper[t] ?? null;
            return isKept(r, settings) && v !== null ? floorValue(v, settings.zeroFloor) : null;
          }),
          connectgaps: false,
          line: { color: file.color, width: 2, dash: "dash" },
          marker: { color: file.color, size: 7, symbol: "triangle-up" },
          opacity: 0.85,
          customdata: records.map((r) => [fmt(r.Et_upper[t] ?? null)]),
          hovertemplate:
            "<b>%{fullData.name}</b><br>p = %{x}<br>E<sub>t</sub> upper = %{customdata[0]}<extra></extra>",
        });
      }
    }
  }

  // A visible floor line, so a series lying flat on it reads as "pinned", not as data.
  // Drawn as a trace rather than a layout shape: shape coordinates on a log axis are
  // ambiguous between data and log10 units, and get the autorange badly wrong.
  const extent = dataExtent(files);
  if (data.length > 0 && extent) {
    data.unshift({
      type: "scatter",
      mode: "lines+text",
      x: [settings.xMin ?? extent[0], settings.xMax ?? extent[1]],
      y: [settings.zeroFloor, settings.zeroFloor],
      line: { color: INK_MUTED, width: 1, dash: "dot" },
      text: ["", "values ≤ 0 pinned here"],
      textposition: "top left",
      textfont: { size: 10, color: INK_MUTED },
      hoverinfo: "skip",
      showlegend: false,
    });
  }

  return {
    data,
    emptyAfterFilter,
    verdicts: sortedVerdicts(verdicts),
    layout: {
      ...baseLayout(settings),
      xaxis: xAxis(files, settings),
      yaxis: {
        title: { text: "E<sub>t</sub> bound (log scale)", font: { size: 13, color: INK_MUTED } },
        type: "log",
        autorange: true,
        // Powers of ten, not SI prefixes — "10⁻⁶" beats Plotly's default "1µ" here.
        exponentformat: "power",
        showexponent: "all",
        gridcolor: GRID,
        griddash: "dash",
        zeroline: false,
        linecolor: GRID,
        ticks: "outside",
        tickcolor: GRID,
        tickfont: { color: INK_MUTED },
      },
    },
  };
}

/**
 * `minSchmidtNumber` against p — the viewer's version of `plot_schmidt_number`. An integer
 * axis, so the connecting line is thin and the markers carry the verdict as everywhere else.
 */
function buildSchmidtFigure(files: DataFile[], settings: Settings): Figure {
  const emptyAfterFilter: string[] = [];
  const data: Trace[] = [];
  const verdicts = new Set<Verdict>();
  let maxSn = 2;

  for (const file of files) {
    const records = visibleSlice(file.records, settings);
    const kept = records.filter((r) => isKept(r, settings));
    if (kept.length === 0) {
      emptyAfterFilter.push(file.label);
      continue;
    }
    for (const rec of kept) {
      verdicts.add(rec.separability);
      if (rec.minSchmidtNumber !== null) maxSn = Math.max(maxSn, rec.minSchmidtNumber);
    }

    data.push({
      type: "scatter",
      mode: "lines+markers",
      name: file.label,
      x: records.map((r) => r.p),
      y: records.map((r) => (isKept(r, settings) ? r.minSchmidtNumber : null)),
      connectgaps: false,
      line: { color: file.color, width: 1.2 },
      marker: verdictMarker(records, file.color),
      customdata: records.map((r) => [VERDICT_LABEL[r.separability], fmt(r.objective)]),
      hovertemplate:
        "<b>%{fullData.name}</b><br>p = %{x}<br>Schmidt number ≥ %{y}" +
        "<br>objective = %{customdata[1]}<br>%{customdata[0]}<extra></extra>",
    });
  }

  return {
    data,
    emptyAfterFilter,
    verdicts: sortedVerdicts(verdicts),
    layout: {
      ...baseLayout(settings),
      xaxis: xAxis(files, settings),
      yaxis: {
        title: {
          text: "certified Schmidt number",
          font: { size: 13, color: INK_MUTED },
        },
        // Integer valued: fixed decade-free ticks and half-step padding, so the points do
        // not land on the frame and no 1.5 tick is ever drawn.
        dtick: 1,
        range: [0.5, maxSn + 0.5],
        gridcolor: GRID,
        griddash: "dash",
        zeroline: false,
        linecolor: GRID,
        ticks: "outside",
        tickcolor: GRID,
        tickfont: { color: INK_MUTED },
      },
    },
  };
}

function buildHistogramFigure(files: DataFile[], settings: Settings): Figure {
  const emptyAfterFilter: string[] = [];
  const labels: string[] = [];
  const colors: string[] = [];
  const lower: number[] = [];
  const lowerText: string[] = [];
  const lowerHover: string[][] = [];
  const upper: (number | null)[] = [];
  const upperHover: string[][] = [];
  const verdicts = new Set<Verdict>();

  for (const file of files) {
    // The whole sweep, not the x window: the histogram has no p axis for that window to mean anything.
    const kept = file.records.filter((r) => isKept(r, settings));
    if (kept.length === 0) {
      emptyAfterFilter.push(file.label);
      continue;
    }
    const total = componentCount(kept);

    for (let t = 0; t < total; t++) {
      // "Always take the largest value of Et_lower" — and report the upper bound at that same point.
      let best = kept[0];
      for (const rec of kept) {
        if ((rec.Et_lower[t] ?? -Infinity) > (best.Et_lower[t] ?? -Infinity)) best = rec;
      }
      const bestLower = best.Et_lower[t] ?? null;
      const bestUpper = best.Et_upper[t] ?? null;

      // The category axis takes plain text, not the `<sub>` markup the legend accepts.
      labels.push(total > 1 ? `${file.label} · E${t + 1}` : file.label);
      colors.push(file.color);
      verdicts.add(best.separability);
      lower.push(floorValue(bestLower, settings.zeroFloor));
      // A bar has no marker to carry the verdict, so anything short of a certified-entangled
      // winner is spelled out under the value rather than left to the tooltip.
      lowerText.push(
        best.separability === 0
          ? fmtShort(bestLower)
          : `${fmtShort(bestLower)}<br>(${VERDICT_LABEL[best.separability]})`,
      );
      lowerHover.push([fmt(bestLower), String(best.p), VERDICT_LABEL[best.separability]]);
      upper.push(bestUpper === null ? null : floorValue(bestUpper, settings.zeroFloor));
      upperHover.push([fmt(bestUpper), String(best.p)]);
    }
  }

  const data: Trace[] = [
    {
      type: "bar",
      name: "E<sub>t</sub> lower",
      x: labels,
      y: lower,
      marker: { color: colors, line: { color: SURFACE, width: 2 } },
      text: lowerText,
      textposition: "outside",
      textfont: { color: INK_MUTED, size: 11 },
      cliponaxis: false,
      customdata: lowerHover,
      hovertemplate:
        "<b>%{x}</b><br>max E<sub>t</sub> lower = %{customdata[0]}<br>at p = %{customdata[1]}" +
        "<br>%{customdata[2]}<extra></extra>",
    },
  ];

  if (settings.showUpperBound && upper.some((v) => v !== null)) {
    data.push({
      type: "bar",
      name: "E<sub>t</sub> upper",
      x: labels,
      y: upper,
      // Hatched as well as faded: both bars of a pair share the file's color, so the
      // legend swatches would otherwise be indistinguishable.
      marker: {
        color: colors,
        pattern: { shape: "/", size: 7, solidity: 0.4, bgcolor: SURFACE, fgcolor: colors },
        line: { color: colors, width: 1 },
      },
      customdata: upperHover,
      hovertemplate:
        "<b>%{x}</b><br>E<sub>t</sub> upper = %{customdata[0]}<br>at p = %{customdata[1]}<extra></extra>",
    });
  }

  // Explicit log range: bars pinned to the floor would otherwise have zero visible height.
  // A third of a decade of headroom under the floor leaves them a labelled stub.
  const maxValue = Math.max(
    settings.zeroFloor,
    ...lower,
    ...upper.filter((v): v is number => v !== null),
  );
  const bottom = Math.log10(settings.zeroFloor) - 0.35;
  const top = Math.log10(maxValue) + 0.35;

  return {
    data,
    emptyAfterFilter,
    verdicts: sortedVerdicts(verdicts),
    layout: {
      ...baseLayout(settings),
      barmode: "group",
      bargap: 0.35,
      showlegend: data.length > 1,
      margin: { l: 76, r: 28, t: 24, b: 130 },
      legend: {
        orientation: "h",
        x: 0,
        xanchor: "left",
        y: 1.06,
        yanchor: "bottom",
        font: { size: 12 },
      },
      xaxis: {
        type: "category",
        automargin: true,
        tickangle: labels.length > 4 ? -30 : 0,
        linecolor: GRID,
        tickcolor: GRID,
        tickfont: { color: INK_MUTED },
      },
      yaxis: {
        title: {
          text: "max E<sub>t</sub> lower (log scale)",
          font: { size: 13, color: INK_MUTED },
        },
        type: "log",
        range: [bottom, top],
        exponentformat: "power",
        showexponent: "all",
        dtick: 1, // decades only; the padded range otherwise draws 2/5 minor labels

        gridcolor: GRID,
        griddash: "dash",
        zeroline: false,
        linecolor: GRID,
        ticks: "outside",
        tickcolor: GRID,
        tickfont: { color: INK_MUTED },
      },
    },
  };
}

/** Pure: turns the current files and settings into a Plotly figure. Imports nothing from Plotly. */
export function buildFigure(files: DataFile[], settings: Settings): Figure {
  const visible = files.filter((f) => f.visible && !f.error && f.records.length > 0);
  switch (settings.chartMode) {
    case "histogram":
      return buildHistogramFigure(visible, settings);
    case "schmidt":
      return buildSchmidtFigure(visible, settings);
    default:
      return buildLineFigure(visible, settings);
  }
}
