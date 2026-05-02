interface Props {
  variant?: 'green' | 'red' | 'yellow' | 'gray' | 'blue';
  children: React.ReactNode;
}

const classes: Record<string, string> = {
  green: 'bg-[var(--color-green-bg)] text-[var(--color-green-text)] border-[var(--color-green-border)]',
  red: 'bg-[var(--color-red-bg)] text-[var(--color-red-text)] border-[var(--color-red-border)]',
  yellow: 'bg-[var(--color-yellow-bg)] text-[var(--color-yellow-text)] border-[var(--color-yellow-border)]',
  gray: 'bg-[var(--color-hover-item)] text-[var(--color-text-muted)] border-[var(--color-border)]',
  blue: 'bg-[var(--color-blue-bg)] text-[var(--color-blue-text)] border-[var(--color-blue-border)]',
};

export default function Badge({ variant = 'gray', children }: Props) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${classes[variant]}`}>
      {children}
    </span>
  );
}
