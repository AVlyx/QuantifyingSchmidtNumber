import { parseResultFile, type ParseResult } from './parseJsonl.ts';

/** One sweep file bundled with the app, from `sdp_results/manifest.json`. */
export interface CatalogFile {
  /** `<folder>/<name>`. Stable across reloads, so it doubles as the `DataFile` id. */
  path: string;
  name: string;
  /** On-disk size. Absent for the pseudo-entries the sidebar makes for uploaded files. */
  bytes?: number;
}

export interface CatalogFolder {
  /** `""` for files sitting at the root of `sdp_results/`. */
  name: string;
  files: CatalogFile[];
}

export interface Catalog {
  folders: CatalogFolder[];
}

/**
 * URL of a path under `sdp_results/`. `BASE_URL` is `/` in dev and `/<repo>/` on GitHub
 * Pages; segments are escaped one by one because some sweeps have a space in the name.
 */
function resultUrl(relative: string): string {
  const escaped = relative.split('/').map(encodeURIComponent).join('/');
  return `${import.meta.env.BASE_URL}sdp_results/${escaped}`;
}

/** The bundled `sdp_results/` index, written by the `sdp-results` Vite plugin. */
export async function fetchCatalog(): Promise<Catalog> {
  const res = await fetch(resultUrl('manifest.json'));
  if (!res.ok) throw new Error(`manifest.json — HTTP ${res.status}`);
  const parsed = (await res.json()) as Partial<Catalog>;
  if (!Array.isArray(parsed.folders)) throw new Error('manifest.json has no folder list.');
  return { folders: parsed.folders };
}

/** Fetch and parse one bundled sweep. Network failures come back as a `ParseResult` error. */
export async function fetchResultFile(path: string): Promise<ParseResult> {
  try {
    const res = await fetch(resultUrl(path));
    if (!res.ok) return { records: [], error: `Could not load — HTTP ${res.status}.` };
    return parseResultFile(await res.text());
  } catch (e) {
    return { records: [], error: `Could not load — ${(e as Error).message}` };
  }
}
