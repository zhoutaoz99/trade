import { fmtMoney } from '../../utils/format';

interface Props {
  value: string | number;
  className?: string;
}

export default function PriceLabel({ value, className = '' }: Props) {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  const color = n > 0 ? 'text-[var(--color-green-text)]' : n < 0 ? 'text-[var(--color-red-text)]' : 'text-[var(--color-text-muted)]';

  return <span className={`font-mono ${color} ${className}`}>{fmtMoney(n)}</span>;
}
