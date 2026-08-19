/**
 * Default legend name for a result file: drop the extension, turn `_`/`-` into spaces and
 * spell a `_lam<digits>` suffix as the partition it encodes.
 *
 *   c3c3_Horodecki.jsonl              -> "c3c3 Horodecki"
 *   convex_Chessboard_Tiles_lam21.jsonl -> "convex Chessboard Tiles λ=(2,1)"
 */
export function prettyLabel(fileName: string): string {
  const stem = fileName.replace(/\.(jsonl|json)$/i, '');

  const lam = /_lam(\d+)$/i.exec(stem);
  const base = (lam ? stem.slice(0, lam.index) : stem).replace(/[_-]+/g, ' ').trim();
  const suffix = lam ? ` λ=(${lam[1].split('').join(',')})` : '';

  return (base + suffix).trim() || fileName;
}
