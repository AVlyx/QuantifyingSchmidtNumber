import type { DataFile, Record1D, Settings, Verdict } from "../types.ts";
import { VERDICT_LABEL } from "../types.ts";

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

const sortedVerdicts = (seen: Set<Verdict>): Verdict[] =>
  ([0, 1, 2] as Verdict[]).filter((v) => seen.has(v));

/**
 * The notebook's `eps` substitution, now user-settable: a log axis cannot draw
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

/** Records kept for plotting; when `showSeparable` is off only certified-entangled points survive. */
function isKept(rec: Record1D, settings: Settings): boolean {
  return settings.showSeparable || rec.separable != 2;
}

/**
 * Records within the chosen x window, plus the one immediately to its left so the curve
 * still enters from the edge. Without this the y axis auto-ranges over points the user
 * has scrolled past, and raising the x start stops zooming the plot vertically.
 * Records are already sorted ascending by `p`.
 */
function visibleSlice(records: Record1D[], xMin: number): Record1D[] {
  if (xMin <= 0) return records;
  const first = records.findIndex((r) => r.p >= xMin);
  if (first === -1) return [];
  return records.slice(Math.max(0, first - 1));
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
  uirevision: `${settings.chartMode}:${settings.xMin}`,
});

function buildLineFigure(files: DataFile[], settings: Settings): Figure {
  const emptyAfterFilter: string[] = [];
  const data: Trace[] = [];
  const verdicts = new Set<Verdict>();

  for (const file of files) {
    const records = visibleSlice(file.records, settings.xMin);
    const kept = records.filter((r) => isKept(r, settings));
    if (kept.length === 0) {
      emptyAfterFilter.push(file.label);
      continue;
    }
    for (const rec of kept) verdicts.add(rec.separable);

    const x = records.map((r) => r.p);
    // Filtered-out points stay in place as nulls so `connectgaps: false` breaks the line
    // exactly where data was dropped, instead of bridging across the hole.
    const y = records.map((r) =>
      isKept(r, settings) ? floorValue(r.Etl, settings.zeroFloor) : null,
    );

    data.push({
      type: "scatter",
      mode: "lines+markers",
      name: file.label,
      legendgroup: file.id,
      x,
      y,
      connectgaps: false,
      line: { color: file.color, width: 2 },
      marker: {
        color: file.color,
        size: records.map((r) => VERDICT_STYLE[r.separable].size),
        symbol: records.map((r) => VERDICT_STYLE[r.separable].symbol),
        line: {
          color: records.map((r) =>
            VERDICT_STYLE[r.separable].outline === "series" ? file.color : SURFACE,
          ),
          width: records.map((r) => VERDICT_STYLE[r.separable].outlineWidth),
        },
      },
      customdata: records.map((r) => [fmt(r.Etl), VERDICT_LABEL[r.separable], fmt(r.obj)]),
      hovertemplate:
        "<b>%{fullData.name}</b><br>p = %{x}<br>E<sub>t</sub> lower = %{customdata[0]}" +
        "<br>obj = %{customdata[2]}<br>%{customdata[1]}<extra></extra>",
    });

    if (settings.showUpperBound && records.some((r) => r.Etu !== null)) {
      data.push({
        type: "scatter",
        mode: "lines+markers",
        name: `${file.label} (upper)`,
        legendgroup: file.id,
        showlegend: false,
        x,
        y: records.map((r) =>
          isKept(r, settings) && r.Etu !== null ? floorValue(r.Etu, settings.zeroFloor) : null,
        ),
        connectgaps: false,
        line: { color: file.color, width: 2, dash: "dash" },
        marker: { color: file.color, size: 7, symbol: "triangle-up" },
        opacity: 0.85,
        customdata: records.map((r) => [fmt(r.Etu)]),
        hovertemplate:
          "<b>%{fullData.name}</b><br>p = %{x}<br>E<sub>t</sub> upper = %{customdata[0]}<extra></extra>",
      });
    }
  }

  // A visible floor line, so a series lying flat on it reads as "pinned", not as data.
  // Drawn as a trace rather than a layout shape: shape coordinates on a log axis are
  // ambiguous between data and log10 units, and get the autorange badly wrong.
  if (data.length > 0) {
    data.unshift({
      type: "scatter",
      mode: "lines+text",
      x: [settings.xMin, 1],
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
      xaxis: {
        title: { text: "p", font: { size: 13, color: INK_MUTED } },
        range: [settings.xMin, 1],
        gridcolor: GRID,
        griddash: "dash",
        zeroline: false,
        linecolor: GRID,
        ticks: "outside",
        tickcolor: GRID,
        tickfont: { color: INK_MUTED },
      },
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

    // "Always take the largest value of Etl" — and report the upper bound at that same point.
    let best = kept[0];
    for (const rec of kept) {
      if ((rec.Etl ?? -Infinity) > (best.Etl ?? -Infinity)) best = rec;
    }

    labels.push(file.label);
    colors.push(file.color);
    verdicts.add(best.separable);
    lower.push(floorValue(best.Etl, settings.zeroFloor));
    // A bar has no marker to carry the verdict, so anything short of a certified-entangled
    // winner is spelled out under the value rather than left to the tooltip.
    lowerText.push(
      best.separable === 0
        ? fmtShort(best.Etl)
        : `${fmtShort(best.Etl)}<br>(${VERDICT_LABEL[best.separable]})`,
    );
    lowerHover.push([fmt(best.Etl), String(best.p), VERDICT_LABEL[best.separable]]);
    upper.push(best.Etu === null ? null : floorValue(best.Etu, settings.zeroFloor));
    upperHover.push([fmt(best.Etu), String(best.p)]);
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
  return settings.chartMode === "histogram"
    ? buildHistogramFigure(visible, settings)
    : buildLineFigure(visible, settings);
}
