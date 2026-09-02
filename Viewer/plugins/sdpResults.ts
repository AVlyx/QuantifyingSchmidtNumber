import { createReadStream } from 'node:fs';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Connect, Plugin } from 'vite';

/** `../sdp_results` relative to this file, i.e. the repo's result folder. */
const RESULTS_ROOT = fileURLToPath(new URL('../../sdp_results', import.meta.url));

/** Both the URL prefix the app fetches from and the folder name inside `dist/`. */
export const MOUNT = 'sdp_results';

const MANIFEST = `${MOUNT}/manifest.json`;

/** Folders listed first, in this order; anything else follows alphabetically. Mirrors
 *  `FOLDERS` in `notebook_utils/load_store_results.py`. */
const FOLDER_ORDER = ['noise', 'vertex', 'lam21', 'convex', 'SN3', 'Parametric', 'test'];

/** A sweep file, as the app sees it in the manifest. */
interface ManifestFile {
  /** `<folder>/<name>`, or just `<name>` for a file sitting at the root of `sdp_results/`. */
  path: string;
  name: string;
  bytes: number;
}

interface ManifestFolder {
  /** `""` for files at the root of `sdp_results/`. */
  name: string;
  files: ManifestFile[];
}

/** Every `*.jsonl` under `sdp_results/`, grouped by its immediate folder. */
async function scan(): Promise<{ folders: ManifestFolder[] }> {
  let entries: string[];
  try {
    entries = await fs.readdir(RESULTS_ROOT);
  } catch {
    return { folders: [] };
  }

  const byFolder = new Map<string, ManifestFile[]>();

  const collect = async (folder: string) => {
    const dir = folder ? path.join(RESULTS_ROOT, folder) : RESULTS_ROOT;
    const files: ManifestFile[] = [];
    for (const name of await fs.readdir(dir)) {
      if (!name.endsWith('.jsonl')) continue;
      const stat = await fs.stat(path.join(dir, name));
      if (!stat.isFile()) continue;
      files.push({ path: folder ? `${folder}/${name}` : name, name, bytes: stat.size });
    }
    if (files.length > 0) {
      files.sort((a, b) => a.name.localeCompare(b.name));
      byFolder.set(folder, files);
    }
  };

  await collect('');
  for (const entry of entries) {
    if ((await fs.stat(path.join(RESULTS_ROOT, entry))).isDirectory()) await collect(entry);
  }

  const rank = (name: string) => {
    const i = FOLDER_ORDER.indexOf(name);
    return i === -1 ? FOLDER_ORDER.length : i;
  };
  const folders = [...byFolder]
    .map(([name, files]): ManifestFolder => ({ name, files }))
    .sort((a, b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name));

  return { folders };
}

/**
 * Publishes the repo's `sdp_results/` to the app, so it opens with every sweep already
 * listed instead of waiting for a drag-and-drop.
 *
 * `sdp_results/` sits outside `Viewer/`, so it cannot be a plain `public/` asset. In dev a
 * middleware streams the files straight off disk (no copy to go stale); for a build they are
 * emitted into `dist/sdp_results/` so the GitHub Pages bundle is self-contained. Both expose
 * the same `sdp_results/manifest.json` index.
 */
export function sdpResults(): Plugin {
  return {
    name: 'sdp-results',

    configureServer(server) {
      const handler: Connect.NextHandleFunction = (req, res, next) => {
        const url = new URL(req.url ?? '/', 'http://localhost');
        const rel = decodeURIComponent(url.pathname).replace(/^\/+/, '');
        if (!rel.startsWith(`${MOUNT}/`)) return next();

        if (rel === MANIFEST) {
          scan().then(
            (manifest) => {
              res.setHeader('Content-Type', 'application/json');
              // Read off disk per request, so a sweep written while the server runs
              // shows up on the next reload.
              res.setHeader('Cache-Control', 'no-store');
              res.end(JSON.stringify(manifest));
            },
            (err: Error) => next(err),
          );
          return;
        }

        const target = path.resolve(RESULTS_ROOT, rel.slice(MOUNT.length + 1));
        // Refuse anything `..` walked out of the results folder.
        if (!target.startsWith(RESULTS_ROOT + path.sep) || !target.endsWith('.jsonl')) {
          res.statusCode = 404;
          res.end('Not found');
          return;
        }
        res.setHeader('Content-Type', 'application/x-ndjson');
        res.setHeader('Cache-Control', 'no-store');
        createReadStream(target)
          .on('error', () => {
            res.statusCode = 404;
            res.end('Not found');
          })
          .pipe(res);
      };
      server.middlewares.use(handler);
    },

    async buildStart() {
      const manifest = await scan();
      this.emitFile({ type: 'asset', fileName: MANIFEST, source: JSON.stringify(manifest) });
      for (const folder of manifest.folders) {
        for (const file of folder.files) {
          this.emitFile({
            type: 'asset',
            fileName: `${MOUNT}/${file.path}`,
            source: await fs.readFile(path.join(RESULTS_ROOT, file.path), 'utf8'),
          });
        }
      }
    },
  };
}
