interface Props {
  symbol: string;
}

export default function PriceBar({ symbol }: Props) {
  // In v1, we show a placeholder. Real-time prices would require a WebSocket
  // connection or polling to the backend market data endpoint.
  return (
    <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-4 flex items-center gap-6">
      <div>
        <div className="text-xs text-gray-500 mb-0.5">Symbol</div>
        <div className="text-white font-mono font-semibold">{symbol}</div>
      </div>
      <div>
        <div className="text-xs text-gray-500 mb-0.5">Market Status</div>
        <div className="text-green-400 text-sm font-medium">● Live</div>
      </div>
      <div className="ml-auto text-xs text-gray-500">
        Prices via Binance WebSocket · Real-time
      </div>
    </div>
  );
}
