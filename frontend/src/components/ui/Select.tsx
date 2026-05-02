import type { SelectHTMLAttributes } from 'react';

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export default function Select({ label, options, className = '', id, ...props }: Props) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={selectId} className="text-xs text-gray-400 font-medium">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`bg-[#1a1d2e] border border-[#2a2e3f] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors cursor-pointer ${className}`}
        {...props}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
