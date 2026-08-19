import type { ChartMode, Settings } from '../types.ts';

interface Props {
  settings: Settings;
  onPatch: (patch: Partial<Settings>) => void;
  onClearAll: () => void;
  canClear: boolean;
}

const MODES: { value: ChartMode; label: string }[] = [
  { value: 'line', label: 'Line' },
  { value: 'histogram', label: 'Histogram' },
  { value: 'schmidt', label: 'Schmidt no.' },
];

/** Empty input = "fit the data"; anything unparseable leaves the current bound alone. */
function boundPatch(text: string): number | null | undefined {
  if (text.trim() === '') return null;
  const value = Number(text);
  return Number.isFinite(value) ? value : undefined;
}

export function GlobalControls({ settings, onPatch, onClearAll, canClear }: Props) {
  const floorValid = Number.isFinite(Number(settings.zeroFloorText)) && Number(settings.zeroFloorText) > 0;
  // The Schmidt-number chart has no E_t axis, so the bound controls have nothing to act on.
  const showBoundControls = settings.chartMode !== 'schmidt';

  return (
    <section className="controls">
      <div className="control">
        <span className="control__label">Chart type</span>
        <div className="segmented">
          {MODES.map((mode) => (
            <button
              key={mode.value}
              className={settings.chartMode === mode.value ? 'is-selected' : ''}
              onClick={() => onPatch({ chartMode: mode.value })}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {showBoundControls && (
        <label className="control control--check">
          <input
            type="checkbox"
            checked={settings.showUpperBound}
            onChange={(e) => onPatch({ showUpperBound: e.target.checked })}
          />
          <span>Show upper bound</span>
        </label>
      )}

      <label className="control control--check">
        <input
          type="checkbox"
          checked={settings.showSeparable}
          onChange={(e) => onPatch({ showSeparable: e.target.checked })}
        />
        <span>
          Show separable states
          <em className="control__hint">
            off = drops certified-separable points; inconclusive ones stay
          </em>
        </span>
      </label>

      {showBoundControls && (
        <label className="control">
          <span className="control__label">Value used for zero</span>
          <input
            className={`text-input${floorValid ? '' : ' is-invalid'}`}
            type="text"
            inputMode="decimal"
            value={settings.zeroFloorText}
            onChange={(e) => {
              const text = e.target.value;
              const value = Number(text);
              // Keep the last valid number so a half-typed "1e-" does not blank the plot.
              onPatch(
                Number.isFinite(value) && value > 0
                  ? { zeroFloorText: text, zeroFloor: value }
                  : { zeroFloorText: text },
              );
            }}
          />
          <em className="control__hint">
            the log axis cannot draw 0, so anything ≤ 0 is pinned here (default 1e-6)
          </em>
        </label>
      )}

      <div className="control">
        <span className="control__label">X-axis range</span>
        <div className="control__pair">
          <input
            className="text-input"
            type="number"
            step={0.05}
            placeholder="auto"
            aria-label="X-axis start"
            value={settings.xMin ?? ''}
            onChange={(e) => {
              const xMin = boundPatch(e.target.value);
              if (xMin !== undefined) onPatch({ xMin });
            }}
          />
          <span className="control__pair-sep">to</span>
          <input
            className="text-input"
            type="number"
            step={0.05}
            placeholder="auto"
            aria-label="X-axis end"
            value={settings.xMax ?? ''}
            onChange={(e) => {
              const xMax = boundPatch(e.target.value);
              if (xMax !== undefined) onPatch({ xMax });
            }}
          />
        </div>
        <em className="control__hint">
          empty = fit the loaded sweeps, which cover very different ranges of p
        </em>
      </div>

      <button
        className="clear-button"
        disabled={!canClear}
        onClick={() => {
          if (confirm('Remove all files and reset settings?')) onClearAll();
        }}
      >
        Clear all
      </button>
    </section>
  );
}
