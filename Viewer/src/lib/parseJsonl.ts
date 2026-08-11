import type { Record1D, Verdict } from '../types.ts';

export interface ParseResult {
  records: Record1D[];
  error?: string;
}

/** `null` on disk is the encoding of NaN; anything non-finite collapses back to null. */
function num(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return value;
}

function verdict(value: unknown): Verdict {
  return value === 0 || value === 2 ? value : 1;
}

/**
 * Parse a 1-D sweep file from `sdp_results/`.
 *
 * Accepts JSONL (one record per line) or a `.json` array of the same records.
 * Rejects the 2-D schema (`{x, y, obj, separable, Etl}`) outright — it is out of scope.
 * Records come back sorted ascending by `p`; the notebooks sort defensively too, since
 * the sweep is not necessarily stored in ascending order.
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
    if (!('Etl' in rec)) {
      return { records: [], error: `Record ${i + 1} has no "Etl" field.` };
    }

    records.push({
      p: rec.p,
      obj: num(rec.obj),
      separable: verdict(rec.separable),
      Etl: num(rec.Etl),
      obj_max: num(rec.obj_max),
      Etu: num(rec.Etu),
    });
  }

  records.sort((a, b) => a.p - b.p);
  return { records };
}
