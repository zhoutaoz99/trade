import { Inbox } from 'lucide-react';

interface Props {
  title: string;
  description?: string;
}

export default function EmptyState({ title, description }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Inbox size={48} className="text-[var(--color-text-subtle)] mb-4" />
      <h3 className="text-lg font-medium text-[var(--color-text-muted)]">{title}</h3>
      {description && <p className="text-sm text-[var(--color-text-dim)] mt-1">{description}</p>}
    </div>
  );
}
