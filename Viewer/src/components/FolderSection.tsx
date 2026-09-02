import type { CatalogFile } from '../lib/catalog.ts';
import type { DataFile } from '../types.ts';
import { FileRow } from './FileRow.tsx';

interface Props {
  /** Folder name as it appears under `sdp_results/`. */
  name: string;
  entries: CatalogFile[];
  /** Series already picked from this folder, keyed by `CatalogFile.path`. */
  picked: Map<string, DataFile>;
  open: boolean;
  onToggleOpen: () => void;
  onToggleFile: (entry: CatalogFile, on: boolean) => void;
  onPatchFile: (id: string, patch: Partial<DataFile>) => void;
  onRemoveFile: (id: string) => void;
}

/** One collapsible `sdp_results/` folder in the sidebar. */
export function FolderSection({
  name,
  entries,
  picked,
  open,
  onToggleOpen,
  onToggleFile,
  onPatchFile,
  onRemoveFile,
}: Props) {
  const shown = entries.filter((e) => picked.get(e.path)?.visible).length;

  return (
    <section className="folder">
      <button
        className="folder__header"
        onClick={onToggleOpen}
        aria-expanded={open}
        title={open ? 'Collapse' : 'Expand'}
      >
        <span className={`folder__caret${open ? ' folder__caret--open' : ''}`} aria-hidden>
          ▸
        </span>
        <span className="folder__name">{name}</span>
        <span className="folder__count">{shown > 0 ? `${shown}/${entries.length}` : entries.length}</span>
      </button>

      {open && (
        <ul className="file-list">
          {entries.map((entry) => (
            <FileRow
              key={entry.path}
              name={entry.name}
              bytes={entry.bytes}
              file={picked.get(entry.path)}
              onToggle={(on) => onToggleFile(entry, on)}
              onPatch={(patch) => onPatchFile(entry.path, patch)}
              onRemove={() => onRemoveFile(entry.path)}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
