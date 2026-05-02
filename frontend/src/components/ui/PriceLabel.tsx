import { fmtMoney } from '../../utils/format';

interface Props {
  value: string | number;
  className?: string;
}

export default function PriceLabel({ value, className = '' }: Props) {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  const color = n > 0 ? 'text-green-400' : n < 0 ? 'text-red-400' : 'text-gray-400';

  return <span className={`font-mono ${color} ${className}`}>{fmtMoney(n)}</span>;
}
