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
];

export function GlobalControls({ settings, onPatch, onClearAll, canClear }: Props) {
  const floorValid = Number.isFinite(Number(settings.zeroFloorText)) && Number(settings.zeroFloorText) > 0;

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

      <label className="control control--check">
        <input
          type="checkbox"
          checked={settings.showUpperBound}
          onChange={(e) => onPatch({ showUpperBound: e.target.checked })}
        />
        <span>Show upper bound</span>
      </label>

      <label className="control control--check">
        <input
          type="checkbox"
          checked={settings.showSeparable}
          onChange={(e) => onPatch({ showSeparable: e.target.checked })}
        />
        <span>
          Show separable states
          <em className="control__hint">off = only certified-entangled points</em>
        </span>
      </label>

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

      <label className="control">
        <span className="control__label">X-axis start</span>
        <input
          className="text-input"
          type="number"
          min={0}
          max={0.99}
          step={0.05}
          value={settings.xMin}
          onChange={(e) => {
            const value = Number(e.target.value);
            if (Number.isFinite(value)) onPatch({ xMin: Math.min(Math.max(value, 0), 0.99) });
          }}
        />
        <em className="control__hint">ends at 1</em>
      </label>

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
