import { useMemo } from 'react';
import type { Catalog, CatalogFile } from '../lib/catalog.ts';
import { UPLOADS_FOLDER, type DataFile, type Settings } from '../types.ts';
import { DropZone } from './DropZone.tsx';
import { FolderSection } from './FolderSection.tsx';
import { GlobalControls } from './GlobalControls.tsx';

interface Props {
  catalog: Catalog | null;
  catalogError: string | null;
  files: DataFile[];
  collapsed: string[];
  settings: Settings;
  storageError: string | null;
  emptyAfterFilter: string[];
  onToggleFile: (folder: string, entry: CatalogFile, on: boolean) => void;
  onFiles: (files: File[]) => void;
  onPatchFile: (id: string, patch: Partial<DataFile>) => void;
  onRemoveFile: (id: string) => void;
  onToggleFolder: (folder: string) => void;
  onPatchSettings: (patch: Partial<Settings>) => void;
  onClearAll: () => void;
}

/** Files at the root of `sdp_results/` have no folder of their own to sit under. */
const ROOT_FOLDER_LABEL = 'ungrouped';

export function Sidebar({
  catalog,
  catalogError,
  files,
  collapsed,
  settings,
  storageError,
  emptyAfterFilter,
  onToggleFile,
  onFiles,
  onPatchFile,
  onRemoveFile,
  onToggleFolder,
  onPatchSettings,
  onClearAll,
}: Props) {
  const picked = useMemo(() => new Map(files.map((f) => [f.id, f])), [files]);

  // Dropped files get their own section at the bottom, built from the series themselves
  // since they have no manifest entry.
  const uploads = files.filter((f) => f.source === 'upload');

  return (
    <aside className="sidebar">
      <h1 className="sidebar__title">SDP results viewer</h1>

      <GlobalControls
        settings={settings}
        onPatch={onPatchSettings}
        onClearAll={onClearAll}
        canClear={files.length > 0}
      />

      {storageError && <p className="notice notice--warn">{storageError}</p>}

      <h2 className="sidebar__heading">sdp_results</h2>

      {catalogError && <p className="notice notice--warn">{catalogError}</p>}
      {!catalog && !catalogError && <p className="notice">Loading the result index…</p>}

      {catalog?.folders.map((folder) => (
        <FolderSection
          key={folder.name}
          name={folder.name || ROOT_FOLDER_LABEL}
          entries={folder.files}
          picked={picked}
          open={!collapsed.includes(folder.name)}
          onToggleOpen={() => onToggleFolder(folder.name)}
          onToggleFile={(entry, on) => onToggleFile(folder.name, entry, on)}
          onPatchFile={onPatchFile}
          onRemoveFile={onRemoveFile}
        />
      ))}

      {catalog?.folders.length === 0 && (
        <p className="notice">
          No <code>.jsonl</code> files found in <code>sdp_results/</code>.
        </p>
      )}

      {uploads.length > 0 && (
        <FolderSection
          name={UPLOADS_FOLDER}
          entries={uploads.map((f) => ({ path: f.id, name: f.fileName }))}
          picked={picked}
          open={!collapsed.includes(UPLOADS_FOLDER)}
          onToggleOpen={() => onToggleFolder(UPLOADS_FOLDER)}
          onToggleFile={(entry, on) => onPatchFile(entry.path, { visible: on })}
          onPatchFile={onPatchFile}
          onRemoveFile={onRemoveFile}
        />
      )}

      <details className="add-files">
        <summary>Add a file of your own</summary>
        <DropZone onFiles={onFiles} />
      </details>

      {emptyAfterFilter.length > 0 && (
        <p className="notice">
          Nothing to plot for {emptyAfterFilter.join(', ')} — every point is either filtered out by
          “show separable states” or lies left of the x-axis start.
        </p>
      )}
    </aside>
  );
}
