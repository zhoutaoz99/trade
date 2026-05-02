import { Inbox } from 'lucide-react';

interface Props {
  title: string;
  description?: string;
}

export default function EmptyState({ title, description }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Inbox size={48} className="text-gray-600 mb-4" />
      <h3 className="text-lg font-medium text-gray-400">{title}</h3>
      {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
    </div>
  );
}
