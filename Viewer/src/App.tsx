import { useCallback, useMemo } from 'react';
import { PlotView } from './components/PlotView.tsx';
import { Sidebar } from './components/Sidebar.tsx';
import { buildFigure } from './lib/buildTraces.ts';
import { nextColor } from './lib/palette.ts';
import { parseResultFile } from './lib/parseJsonl.ts';
import { prettyLabel } from './lib/prettyLabel.ts';
import { usePersistedState } from './lib/usePersistedState.ts';
import type { DataFile } from './types.ts';

/** Drawn rather than typed: the hexagon has no reliable unicode glyph across fonts. */
const SYMBOL_KEY = [
  { label: 'entangled', shape: <circle cx="7" cy="7" r="5" /> },
  { label: 'inconclusive', shape: <polygon points="7,1.8 12,4.6 12,9.4 7,12.2 2,9.4 2,4.6" /> },
  {
    label: 'separable',
    shape: <path d="M3 3 L11 11 M11 3 L3 11" stroke="currentColor" strokeWidth="1.8" fill="none" />,
  },
];

export default function App() {
  const [state, dispatch, storageError] = usePersistedState();
  const { files, settings } = state;

  const figure = useMemo(() => buildFigure(files, settings), [files, settings]);

  const handleFiles = useCallback(
    async (incoming: File[]) => {
      const used = files.map((f) => f.color);
      const added: DataFile[] = [];

      for (const file of incoming) {
        const { records, error } = parseResultFile(await file.text());
        const color = nextColor([...used, ...added.map((f) => f.color)]);
        added.push({
          id: crypto.randomUUID(),
          fileName: file.name,
          label: prettyLabel(file.name),
          color,
          visible: true,
          records,
          error,
        });
      }

      if (added.length > 0) dispatch({ type: 'addFiles', files: added });
    },
    [files, dispatch],
  );

  const hasPlottable = files.some((f) => f.visible && !f.error && f.records.length > 0);
  const showSymbolKey = settings.chartMode === 'line' && settings.showSeparable && hasPlottable;

  return (
    <div className="app">
      <Sidebar
        files={files}
        settings={settings}
        storageError={storageError}
        emptyAfterFilter={figure.emptyAfterFilter}
        onFiles={handleFiles}
        onPatchFile={(id, patch) => dispatch({ type: 'updateFile', id, patch })}
        onRemoveFile={(id) => dispatch({ type: 'removeFile', id })}
        onPatchSettings={(patch) => dispatch({ type: 'updateSettings', patch })}
        onClearAll={() => dispatch({ type: 'clearAll' })}
      />

      <main className="main">
        {hasPlottable ? (
          <>
            <PlotView figure={figure} />
            {showSymbolKey && (
              <div className="symbol-key">
                <span className="symbol-key__title">Marker shape:</span>
                {SYMBOL_KEY.map((entry) => (
                  <span key={entry.label} className="symbol-key__item">
                    <svg viewBox="0 0 14 14" width="13" height="13" fill="currentColor" aria-hidden>
                      {entry.shape}
                    </svg>
                    {entry.label}
                  </span>
                ))}
                {settings.showUpperBound && (
                  <span className="symbol-key__item">
                    <svg viewBox="0 0 26 14" width="26" height="13" aria-hidden>
                      <path
                        d="M0 7 H26"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeDasharray="5 3"
                        fill="none"
                      />
                    </svg>
                    upper bound
                  </span>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <p>
              Drop <code>.jsonl</code> files from <code>sdp_results/</code> to begin.
            </p>
            {files.length > 0 && <p className="empty-state__hint">Nothing is currently ticked to show.</p>}
          </div>
        )}
      </main>
    </div>
  );
}
