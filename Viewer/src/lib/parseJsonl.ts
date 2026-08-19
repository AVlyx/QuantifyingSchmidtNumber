import type { Record1D, Verdict } from '../types.ts';

export interface ParseResult {
  records: Record1D[];
  error?: string;
}

/** `null` on disk is the encoding of NaN; anything non-finite collapses back to null. */
function num(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return value;
}

/**
 * `Et_lower` / `Et_upper` are lists, one entry per t. A bare number is accepted as a
 * one-element list so a hand-edited file still loads.
 */
function numList(value: unknown): (number | null)[] {
  if (Array.isArray(value)) return value.map(num);
  return [num(value)];
}

function verdict(value: unknown): Verdict {
  return value === 0 || value === 2 ? value : 1;
}

/**
 * Parse a sweep file from `sdp_results/`.
 *
 * Accepts JSONL (one record per line) or a `.json` array of the same records. The schema
 * is `SdpResult` from `notebook_utils/load_store_results.py`; the pre-`Et_lower` schema
 * (`obj`/`separable`/`Etl`/`Etu`) and the 2-D `{x, y}` schema are both rejected by name.
 * Records come back sorted ascending by `p`, as the notebook sorts them too.
 */
export function parseResultFile(text: string): ParseResult {
  let raw: unknown[];

  const trimmed = text.trim();
  if (trimmed.startsWith('[')) {
    try {
      const parsed = JSON.parse(trimmed);
      if (!Array.isArray(parsed)) return { records: [], error: 'Expected a JSON array of records.' };
      raw = parsed;
    } catch (e) {
      return { records: [], error: `Invalid JSON: ${(e as Error).message}` };
    }
  } else {
    raw = [];
    const lines = text.split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      try {
        raw.push(JSON.parse(line));
      } catch {
        return { records: [], error: `Line ${i + 1} is not valid JSON.` };
      }
    }
  }

  if (raw.length === 0) return { records: [], error: 'File contains no records.' };

  const records: Record1D[] = [];
  for (let i = 0; i < raw.length; i++) {
    const item = raw[i];
    if (typeof item !== 'object' || item === null || Array.isArray(item)) {
      return { records: [], error: `Record ${i + 1} is not a JSON object.` };
    }
    const rec = item as Record<string, unknown>;

    if (!('p' in rec) && 'x' in rec && 'y' in rec) {
      return { records: [], error: '2-D result files are not supported.' };
    }
    if (typeof rec.p !== 'number' || !Number.isFinite(rec.p)) {
      return { records: [], error: `Record ${i + 1} has no numeric "p" field.` };
    }
    if (!('Et_lower' in rec)) {
      const stale = 'Etl' in rec || 'Etu' in rec || 'separable' in rec;
      return {
        records: [],
        error: stale
          ? 'Old result schema (Etl/Etu) — rerun the sweep to get Et_lower/Et_upper.'
          : `Record ${i + 1} has no "Et_lower" field.`,
      };
    }

    records.push({
      p: rec.p,
      separability: verdict(rec.separability),
      minSchmidtNumber: num(rec.minSchmidtNumber),
      objective: num(rec.objective),
      Et_lower: numList(rec.Et_lower),
      objective_max: num(rec.objective_max),
      Et_upper: numList(rec.Et_upper),
    });
  }

  records.sort((a, b) => a.p - b.p);
  return { records };
}

/**
 * How many t components a file carries — the length of its longest `Et_lower`. A sweep
 * testing Schmidt number r has r - 1, so `c3c3_isotropicSN3` draws two curves and every
 * k = 2 sweep draws one.
 */
export function componentCount(records: Record1D[]): number {
  return records.reduce((n, r) => Math.max(n, r.Et_lower.length), 0);
}
