/** Separability verdict from toqito's `is_separable`. Note the inversion: 2 (not 1) means separable. */
export type Verdict = 0 | 1 | 2;

export const VERDICT_LABEL: Record<Verdict, string> = {
  0: 'entangled',
  1: 'inconclusive',
  2: 'separable',
};

/** One line of a 1-D `*.jsonl` sweep in `sdp_results/`. */
export interface Record1D {
  /** Sweep parameter, in [0, 1]. Does not always start at 0. */
  p: number;
  obj: number | null;
  separable: Verdict;
  /** Lower bound on E_t — the plotted quantity. 0 means "not certified entangled". */
  Etl: number | null;
  obj_max: number | null;
  /** Upper bound on E_t (k = 2 only). 1.0 for nearly every point in the current data. */
  Etu: number | null;
}

export interface DataFile {
  id: string;
  fileName: string;
  /** Editable legend name. */
  label: string;
  color: string;
  visible: boolean;
  /** Sorted ascending by `p`. Empty when `error` is set. */
  records: Record1D[];
  error?: string;
}

export type ChartMode = 'line' | 'histogram';

export interface Settings {
  chartMode: ChartMode;
  showUpperBound: boolean;
  /** When false, records with `separable !== 0` are filtered out of the plot. */
  showSeparable: boolean;
  /** Substituted for any value <= 0 so it can be drawn on the log axis (the notebook's `eps`). */
  zeroFloor: number;
  /** Raw text of the zero-floor input, so typing "1e-" does not destroy the value. */
  zeroFloorText: string;
  /** Start of the x axis. The end is always 1. */
  xMin: number;
}

export interface AppState {
  files: DataFile[];
  settings: Settings;
}

export const DEFAULT_SETTINGS: Settings = {
  chartMode: 'line',
  showUpperBound: false,
  showSeparable: true,
  zeroFloor: 1e-6,
  zeroFloorText: '1e-6',
  xMin: 0,
};

export type Action =
  | { type: 'addFiles'; files: DataFile[] }
  | { type: 'removeFile'; id: string }
  | { type: 'updateFile'; id: string; patch: Partial<DataFile> }
  | { type: 'updateSettings'; patch: Partial<Settings> }
  | { type: 'clearAll' };
