import { fmtMoney } from '../../utils/format';

interface Props {
  symbol: string;
  price?: { ask_price: string; bid_price: string };
}

export default function PriceBar({ symbol, price }: Props) {
  const ask = price ? parseFloat(price.ask_price) : null;
  const bid = price ? parseFloat(price.bid_price) : null;
  const mid = ask && bid ? (ask + bid) / 2 : null;

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 flex items-center gap-6">
      <div>
        <div className="text-xs text-[var(--color-text-dim)] mb-0.5">Symbol</div>
        <div className="text-[var(--color-text-heading)] font-mono font-semibold">{symbol}</div>
      </div>
      {mid ? (
        <>
          <div>
            <div className="text-xs text-[var(--color-text-dim)] mb-0.5">Bid</div>
            <div className="text-[var(--color-red-text)] font-mono text-sm font-medium">{fmtMoney(bid!)}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--color-text-dim)] mb-0.5">Ask</div>
            <div className="text-[var(--color-green-text)] font-mono text-sm font-medium">{fmtMoney(ask!)}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--color-text-dim)] mb-0.5">Mid</div>
            <div className="text-[var(--color-text-heading)] font-mono text-sm font-medium">{fmtMoney(mid)}</div>
          </div>
        </>
      ) : (
        <div className="text-xs text-[var(--color-text-dim)]">Loading price...</div>
      )}
      <div className="ml-auto text-xs text-[var(--color-text-dim)]">
        Prices via Binance · Real-time
      </div>
    </div>
  );
}
