import { useState, useRef, useEffect } from 'react';
import { Search } from 'lucide-react';

const POPULAR_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
  'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT',
];

interface Props {
  value: string;
  onChange: (symbol: string) => void;
}

export default function SymbolSelector({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = POPULAR_SYMBOLS.filter((s) =>
    s.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-lg px-4 py-2.5 text-white font-mono font-semibold text-lg hover:border-blue-500/50 transition-colors cursor-pointer w-full text-left flex items-center justify-between"
      >
        {value}
        <span className="text-gray-500 text-sm">▼</span>
      </button>
      {open && (
        <div className="absolute top-full mt-1 w-full bg-[#1a1d2e] border border-[#2a2e3f] rounded-lg shadow-xl z-50 max-h-64 overflow-hidden">
          <div className="p-2 border-b border-[#2a2e3f]">
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search symbol..."
                className="w-full bg-[#0f1117] border border-[#2a2e3f] rounded pl-8 pr-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
                autoFocus
              />
            </div>
          </div>
          <div className="overflow-y-auto max-h-48">
            {filtered.map((s) => (
              <button
                key={s}
                onClick={() => {
                  onChange(s);
                  setOpen(false);
                  setSearch('');
                }}
                className={`w-full text-left px-4 py-2 text-sm hover:bg-white/5 transition-colors cursor-pointer font-mono ${
                  s === value ? 'text-blue-400 bg-blue-600/10' : 'text-gray-300'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
