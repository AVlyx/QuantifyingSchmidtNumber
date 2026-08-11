import { useEffect, useReducer, useRef, useState } from 'react';
import type { Action, AppState } from '../types.ts';
import { DEFAULT_SETTINGS } from '../types.ts';

export const STORAGE_KEY = 'sdp-viewer-v1';

const EMPTY: AppState = { files: [], settings: DEFAULT_SETTINGS };

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
    case 'clearAll':
      return EMPTY;
  }
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
    };
  } catch {
    return EMPTY;
  }
}

/**
 * The app reducer, mirrored into localStorage so dropped files and their names, colors
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
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        setStorageError(null);
      } catch {
        setStorageError('Could not save to local storage — this session will not survive a reload.');
      }
    }, 300);
    return () => window.clearTimeout(timer.current);
  }, [state]);

  return [state, dispatch, storageError];
}
