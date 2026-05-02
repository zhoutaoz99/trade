const nf = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const nfPrecise = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nfCrypto = new Intl.NumberFormat('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 6 });

export function fmtMoney(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '$0.00';
  return '$' + nf.format(n);
}

export function fmtMoneyPrecise(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '$0.00';
  return '$' + nfPrecise.format(n);
}

export function fmtCrypto(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '0';
  return nfCrypto.format(n);
}

export function fmtNumber(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '0';
  return nf.format(n);
}

export function fmtPnl(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '$0.00';
  const prefix = n >= 0 ? '+' : '';
  return prefix + '$' + nfPrecise.format(Math.abs(n));
}
