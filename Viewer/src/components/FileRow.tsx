import { componentCount } from '../lib/parseJsonl.ts';
import type { DataFile } from '../types.ts';

interface Props {
  file: DataFile;
  onPatch: (patch: Partial<DataFile>) => void;
  onRemove: () => void;
}

export function FileRow({ file, onPatch, onRemove }: Props) {
  // A sweep testing Schmidt number r carries r - 1 bounds and so draws r - 1 curves.
  const components = componentCount(file.records);
  if (file.error) {
    return (
      <li className="file-row file-row--error">
        <div className="file-row__main">
          <span className="file-row__name">{file.fileName}</span>
          <button className="icon-button" onClick={onRemove} title="Remove" aria-label="Remove">
            ×
          </button>
        </div>
        <div className="file-row__sub">{file.error}</div>
      </li>
    );
  }

  return (
    <li className="file-row">
      <div className="file-row__main">
        <input
          type="checkbox"
          checked={file.visible}
          onChange={(e) => onPatch({ visible: e.target.checked })}
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
        <button className="icon-button" onClick={onRemove} title="Remove" aria-label="Remove">
          ×
        </button>
      </div>
      <div className="file-row__sub">
        {file.fileName} · {file.records.length} points
        {components > 1 && ` · E_t for t = 1…${components}`}
      </div>
    </li>
  );
}
