import { useState } from 'react';
import Button from '../ui/Button';

interface Props {
  currentLeverage: number;
  onSetLeverage: (leverage: number) => void;
  isSetting: boolean;
}

const PRESETS = [1, 2, 3, 5, 10, 20, 50, 100, 125];

export default function LeverageSettings({ currentLeverage, onSetLeverage, isSetting }: Props) {
  const [value, setValue] = useState(currentLeverage);

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--color-text-heading)]">Leverage</h3>
        <span className="text-xs text-[var(--color-text-dim)]">Current: {currentLeverage}x</span>
      </div>

      <div className="flex items-center gap-3 mb-3">
        <input
          type="range"
          min={1}
          max={125}
          value={value}
          onChange={(e) => setValue(parseInt(e.target.value))}
          className="flex-1 accent-blue-500"
        />
        <span className="text-[var(--color-text-heading)] font-mono font-bold text-lg w-12 text-right">{value}x</span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {PRESETS.map((p) => (
          <button
            key={p}
            onClick={() => setValue(p)}
            className={`px-2 py-0.5 text-xs rounded border transition-colors cursor-pointer ${
              value === p
                ? 'border-blue-500 text-[var(--color-blue-text)] bg-[var(--color-blue-bg)]'
                : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-dim)]'
            }`}
          >
            {p}x
          </button>
        ))}
      </div>

      <Button
        variant="primary"
        size="sm"
        className="w-full"
        onClick={() => onSetLeverage(value)}
        loading={isSetting}
        disabled={value === currentLeverage}
      >
        Set to {value}x
      </Button>
    </div>
  );
}
