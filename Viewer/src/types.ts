/** Separability verdict from toqito's `is_separable`. Note the inversion: 2 (not 1) means separable. */
export type Verdict = 0 | 1 | 2;

export const VERDICT_LABEL: Record<Verdict, string> = {
  0: 'entangled',
  1: 'inconclusive',
  2: 'separable',
};

/**
 * One line of a `*.jsonl` sweep in `sdp_results/`, matching `SdpResult` in
 * `notebook_utils/load_store_results.py` field for field.
 */
export interface Record1D {
  /** Sweep parameter. Does not always start at 0, and often stops well short of 1. */
  p: number;
  separability: Verdict;
  /** Schmidt number certified at this point — 1 when the SDP did not certify entanglement. */
  minSchmidtNumber: number | null;
  objective: number | null;
  /**
   * Lower bounds on E_t — the plotted quantity. One entry per t, index i holding t = i + 1,
   * so a sweep testing Schmidt number r carries r - 1 of them. 0 means "not certified".
   */
  Et_lower: (number | null)[];
  objective_max: number | null;
  /** Upper bounds on E_t, indexed like `Et_lower`. Only ever computed for k = 2. */
  Et_upper: (number | null)[];
}

export type ChartMode = 'line' | 'histogram' | 'schmidt';

export interface Settings {
  chartMode: ChartMode;
  showUpperBound: boolean;
  /** When false, records with `separability === 2` are filtered out of the plot. */
  showSeparable: boolean;
  /** Substituted for any value <= 0 so it can be drawn on the log axis (the notebook's `zero_at`). */
  zeroFloor: number;
  /** Raw text of the zero-floor input, so typing "1e-" does not destroy the value. */
  zeroFloorText: string;
  /** Start of the x axis; null fits the data. Sweeps span very different ranges of p. */
  xMin: number | null;
  /** End of the x axis; null fits the data. */
  xMax: number | null;
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
  xMin: null,
  xMax: null,
};

export type Action =
  | { type: 'addFiles'; files: DataFile[] }
  | { type: 'removeFile'; id: string }
  | { type: 'updateFile'; id: string; patch: Partial<DataFile> }
  | { type: 'updateSettings'; patch: Partial<Settings> }
  | { type: 'clearAll' };
