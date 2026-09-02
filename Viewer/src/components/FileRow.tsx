import { componentCount } from '../lib/parseJsonl.ts';
import type { DataFile } from '../types.ts';

interface Props {
  /** File name as it appears in `sdp_results/`. */
  name: string;
  /** On-disk size, shown until the file is picked and a point count can replace it. */
  bytes?: number;
  /** The loaded series, once the file has been ticked. Absent means "not picked yet". */
  file?: DataFile;
  onToggle: (on: boolean) => void;
  onPatch: (patch: Partial<DataFile>) => void;
  onRemove: () => void;
}

function formatBytes(bytes: number): string {
  return bytes < 1024 ? `${bytes} B` : `${Math.round(bytes / 1024)} kB`;
}

export function FileRow({ name, bytes, file, onToggle, onPatch, onRemove }: Props) {
  // Untouched file: one compact line, so a folder of 12 sweeps still scans at a glance.
  if (!file) {
    return (
      <li className="file-row file-row--idle">
        <label className="file-row__main">
          <input
            type="checkbox"
            checked={false}
            onChange={(e) => onToggle(e.target.checked)}
            aria-label={`Plot ${name}`}
          />
          <span className="file-row__name">{name}</span>
          {bytes !== undefined && <span className="file-row__size">{formatBytes(bytes)}</span>}
        </label>
      </li>
    );
  }

  if (file.error) {
    return (
      <li className="file-row file-row--error">
        <div className="file-row__main">
          <span className="file-row__name">{name}</span>
          <button className="icon-button" onClick={onRemove} title="Remove" aria-label="Remove">
            ×
          </button>
        </div>
        <div className="file-row__sub">{file.error}</div>
      </li>
    );
  }

  // A sweep testing Schmidt number r carries r - 1 bounds and so draws r - 1 curves.
  const components = componentCount(file.records);

  return (
    <li className="file-row">
      <div className="file-row__main">
        <input
          type="checkbox"
          checked={file.visible}
          onChange={(e) => onToggle(e.target.checked)}
          title="Show this file"
          aria-label={`Show ${file.label}`}
        />
        <input
          className="file-row__label"
          type="text"
          value={file.label}
          placeholder="Legend name"
          onChange={(e) => onPatch({ label: e.target.value })}
        />
        <input
          className="file-row__color"
          type="color"
          value={file.color}
          onChange={(e) => onPatch({ color: e.target.value })}
          title="Series color"
          aria-label={`Color for ${file.label}`}
        />
        <button
          className="icon-button"
          onClick={onRemove}
          title="Reset name and color"
          aria-label={`Reset ${file.label}`}
        >
          ×
        </button>
      </div>
      <div className="file-row__sub">
        {file.loaded ? (
          <>
            {name} · {file.records.length} points
            {components > 1 && ` · E_t for t = 1…${components}`}
          </>
        ) : (
          <>{name} · loading…</>
        )}
      </div>
    </li>
  );
}
