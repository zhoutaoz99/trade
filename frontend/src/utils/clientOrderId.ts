export function generateClientOrderId(symbol: string): string {
  const ts = Date.now();
  const rand = Math.random().toString(36).substring(2, 8);
  return `sim-${symbol.toLowerCase()}-${ts}-${rand}`;
}
