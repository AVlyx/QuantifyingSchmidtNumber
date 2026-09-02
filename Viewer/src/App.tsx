import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { PlotView } from './components/PlotView.tsx';
import { Sidebar } from './components/Sidebar.tsx';
import { buildFigure } from './lib/buildTraces.ts';
import { fetchCatalog, fetchResultFile, type Catalog, type CatalogFile } from './lib/catalog.ts';
import { nextColor } from './lib/palette.ts';
import { parseResultFile } from './lib/parseJsonl.ts';
import { prettyLabel } from './lib/prettyLabel.ts';
import { usePersistedState } from './lib/usePersistedState.ts';
import { UPLOADS_FOLDER, VERDICT_LABEL, type DataFile, type Verdict } from './types.ts';

/** Drawn rather than typed, one per `VERDICT_STYLE` entry: no unicode glyph matches the
 *  plotly symbols closely enough to be read as the same mark. */
const SYMBOL_KEY: Record<Verdict, ReactNode> = {
  0: <circle cx="7" cy="7" r="4.5" />,
  1: (
    <polygon points="7,1 12.5,7 7,13 1.5,7" fill="none" stroke="currentColor" strokeWidth="1.8" />
  ),
  2: <path d="M3 3 L11 11 M11 3 L3 11" stroke="currentColor" strokeWidth="1.8" fill="none" />,
};

export default function App() {
  const [state, dispatch, storageError] = usePersistedState();
  const { files, settings, collapsed } = state;

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  const figure = useMemo(() => buildFigure(files, settings), [files, settings]);

  useEffect(() => {
    let live = true;
    fetchCatalog().then(
      (c) => live && setCatalog(c),
      (e: Error) =>
        live && setCatalogError(`Could not load the sdp_results index — ${e.message}`),
    );
    return () => {
      live = false;
    };
  }, []);

  // Catalog files are persisted without their records, so a restored session (and every
  // newly ticked file) arrives here unloaded and gets fetched exactly once.
  const fetching = useRef(new Set<string>());
  useEffect(() => {
    for (const file of files) {
      if (file.source !== 'catalog' || file.loaded || file.error) continue;
      if (fetching.current.has(file.id)) continue;
      fetching.current.add(file.id);
      fetchResultFile(file.id).then(({ records, error }) => {
        fetching.current.delete(file.id);
        dispatch({ type: 'updateFile', id: file.id, patch: { records, error, loaded: true } });
      });
    }
  }, [files, dispatch]);

  const handleToggleCatalogFile = useCallback(
    (folder: string, entry: CatalogFile, on: boolean) => {
      const existing = files.find((f) => f.id === entry.path);
      if (existing) {
        dispatch({ type: 'updateFile', id: existing.id, patch: { visible: on } });
        return;
      }
      dispatch({
        type: 'addFiles',
        files: [
          {
            id: entry.path,
            source: 'catalog',
            folder,
            fileName: entry.name,
            label: prettyLabel(entry.name),
            color: nextColor(files.map((f) => f.color)),
            visible: on,
            records: [],
            loaded: false,
          },
        ],
      });
    },
    [files, dispatch],
  );

  const handleFiles = useCallback(
    async (incoming: File[]) => {
      const used = files.map((f) => f.color);
      const added: DataFile[] = [];

      for (const file of incoming) {
        const { records, error } = parseResultFile(await file.text());
        const color = nextColor([...used, ...added.map((f) => f.color)]);
        added.push({
          id: crypto.randomUUID(),
          source: 'upload',
          folder: UPLOADS_FOLDER,
          fileName: file.name,
          label: prettyLabel(file.name),
          color,
          visible: true,
          records,
          error,
          loaded: true,
        });
      }

      if (added.length > 0) dispatch({ type: 'addFiles', files: added });
    },
    [files, dispatch],
  );

  const hasPlottable = files.some((f) => f.visible && !f.error && f.records.length > 0);
  // Listed whenever markers are on screen — with the separable filter on, the plot still
  // mixes entangled and inconclusive points, which is exactly when the key is needed.
  const showSymbolKey = settings.chartMode !== 'histogram' && figure.verdicts.length > 0;

  return (
    <div className="app">
      <Sidebar
        catalog={catalog}
        catalogError={catalogError}
        files={files}
        collapsed={collapsed}
        settings={settings}
        storageError={storageError}
        emptyAfterFilter={figure.emptyAfterFilter}
        onToggleFile={handleToggleCatalogFile}
        onFiles={handleFiles}
        onPatchFile={(id, patch) => dispatch({ type: 'updateFile', id, patch })}
        onRemoveFile={(id) => dispatch({ type: 'removeFile', id })}
        onToggleFolder={(folder) => dispatch({ type: 'toggleFolder', folder })}
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
                {figure.verdicts.map((verdict) => (
                  <span key={verdict} className="symbol-key__item">
                    <svg viewBox="0 0 14 14" width="13" height="13" fill="currentColor" aria-hidden>
                      {SYMBOL_KEY[verdict]}
                    </svg>
                    {VERDICT_LABEL[verdict]}
                  </span>
                ))}
                {settings.showUpperBound && settings.chartMode === 'line' && (
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
              Tick sweeps in the sidebar to plot them — they come from{' '}
              <code>sdp_results/</code>.
            </p>
            {files.length > 0 && (
              <p className="empty-state__hint">Nothing is currently ticked to show.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
