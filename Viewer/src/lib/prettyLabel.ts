/**
 * Default legend name for a result file, mirroring `_pretty_label` in the notebooks:
 * strip the extension, a trailing `_2d`, and a trailing `_m<d>_k<d>`, then
 * turn `_`/`-` into spaces.
 *
 *   C3C3_horodecki_m3_k2.jsonl -> "C3C3 horodecki"
 */
export function prettyLabel(fileName: string): string {
  const stem = fileName
    .replace(/\.(jsonl|json)$/i, '')
    .replace(/_2d$/i, '')
    .replace(/_m\d+_k\d+$/i, '');
  return stem.replace(/[_-]+/g, ' ').trim() || fileName;
}
