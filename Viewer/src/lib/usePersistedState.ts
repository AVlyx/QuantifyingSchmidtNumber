import { useEffect, useReducer, useRef, useState } from 'react';
import type { Action, AppState, DataFile } from '../types.ts';
import { DEFAULT_SETTINGS } from '../types.ts';

// v3: files gained `source`/`folder`/`loaded` when the bundled `sdp_results/` catalog
// replaced drag-and-drop as the way in. A v2 payload has none of them, so it is dropped.
export const STORAGE_KEY = 'sdp-viewer-v3';

const EMPTY: AppState = { files: [], settings: DEFAULT_SETTINGS, collapsed: [] };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'addFiles':
      return { ...state, files: [...state.files, ...action.files] };
    case 'removeFile':
      return { ...state, files: state.files.filter((f) => f.id !== action.id) };
    case 'updateFile':
      return {
        ...state,
        files: state.files.map((f) => (f.id === action.id ? { ...f, ...action.patch } : f)),
      };
    case 'updateSettings':
      return { ...state, settings: { ...state.settings, ...action.patch } };
    case 'toggleFolder':
      return {
        ...state,
        collapsed: state.collapsed.includes(action.folder)
          ? state.collapsed.filter((f) => f !== action.folder)
          : [...state.collapsed, action.folder],
      };
    case 'clearAll':
      return { ...EMPTY, collapsed: state.collapsed };
  }
}

/** A file is worth persisting only once it carries the user's own choices. */
function isCatalogFile(file: DataFile): boolean {
  return file.source === 'catalog';
}

/**
 * What goes to localStorage. Catalog records are megabytes of data already served with the
 * app, so only the user's choices about them are kept and the records are fetched again on
 * load. Uploaded files have no other home, so they are stored whole.
 */
function serialize(state: AppState): string {
  return JSON.stringify({
    ...state,
    files: state.files.map((f) =>
      isCatalogFile(f) ? { ...f, records: [], error: undefined, loaded: false } : f,
    ),
  });
}

function loadInitial(): AppState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const parsed = JSON.parse(raw) as Partial<AppState>;
    return {
      files: Array.isArray(parsed.files) ? parsed.files : [],
      // Merged with the defaults so a state saved by an older build stays loadable.
      settings: { ...DEFAULT_SETTINGS, ...(parsed.settings ?? {}) },
      collapsed: Array.isArray(parsed.collapsed) ? parsed.collapsed : [],
    };
  } catch {
    return EMPTY;
  }
}

/**
 * The app reducer, mirrored into localStorage so the chosen files and their names, colors
 * and settings survive a reload. Writes are debounced and never allowed to throw — a
 * full quota surfaces as a warning instead of taking the app down.
 */
export function usePersistedState(): [AppState, React.Dispatch<Action>, string | null] {
  const [state, dispatch] = useReducer(reducer, undefined, loadInitial);
  const [storageError, setStorageError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, serialize(state));
        setStorageError(null);
      } catch {
        setStorageError('Could not save to local storage — this session will not survive a reload.');
      }
    }, 300);
    return () => window.clearTimeout(timer.current);
  }, [state]);

  return [state, dispatch, storageError];
}
