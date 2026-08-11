/**
 * Default series colors.
 *
 * Not the notebook's `_OVERLAY_COLORS` (matplotlib tab10) — that set fails a
 * colorblind-separation check, with `#ff7f0e` and `#2ca02c` collapsing to ΔE 0.7 under
 * protanopia. This is an Okabe-Ito-derived order that passes lightness, chroma, CVD and
 * normal-vision separation on a light surface. Every color is user-overridable anyway.
 */
export const PALETTE = [
  '#0072b2', // blue
  '#d55e00', // vermillion
  '#009e73', // bluish green
  '#7b5fd3', // violet
  '#8b6b00', // olive
  '#3aa6c9', // sky
  '#b4344e', // crimson
  '#cc79a7', // pink
];

/** Next color for a newly added file: first unused palette slot, else cycle. */
export function nextColor(usedColors: string[]): string {
  const used = new Set(usedColors.map((c) => c.toLowerCase()));
  const free = PALETTE.find((c) => !used.has(c));
  return free ?? PALETTE[usedColors.length % PALETTE.length];
}
