import type { DataFile, Settings } from '../types.ts';
import { DropZone } from './DropZone.tsx';
import { FileRow } from './FileRow.tsx';
import { GlobalControls } from './GlobalControls.tsx';

interface Props {
  files: DataFile[];
  settings: Settings;
  storageError: string | null;
  emptyAfterFilter: string[];
  onFiles: (files: File[]) => void;
  onPatchFile: (id: string, patch: Partial<DataFile>) => void;
  onRemoveFile: (id: string) => void;
  onPatchSettings: (patch: Partial<Settings>) => void;
  onClearAll: () => void;
}

export function Sidebar({
  files,
  settings,
  storageError,
  emptyAfterFilter,
  onFiles,
  onPatchFile,
  onRemoveFile,
  onPatchSettings,
  onClearAll,
}: Props) {
  return (
    <aside className="sidebar">
      <h1 className="sidebar__title">SDP results viewer</h1>

      <DropZone onFiles={onFiles} />

      <GlobalControls
        settings={settings}
        onPatch={onPatchSettings}
        onClearAll={onClearAll}
        canClear={files.length > 0}
      />

      {storageError && <p className="notice notice--warn">{storageError}</p>}

      {files.length > 0 && (
        <>
          <h2 className="sidebar__heading">Files</h2>
          <ul className="file-list">
            {files.map((file) => (
              <FileRow
                key={file.id}
                file={file}
                onPatch={(patch) => onPatchFile(file.id, patch)}
                onRemove={() => onRemoveFile(file.id)}
              />
            ))}
          </ul>
        </>
      )}

      {emptyAfterFilter.length > 0 && (
        <p className="notice">
          Nothing to plot for {emptyAfterFilter.join(', ')} — every point is either filtered out by
          “show separable states” or lies left of the x-axis start.
        </p>
      )}
    </aside>
  );
}
