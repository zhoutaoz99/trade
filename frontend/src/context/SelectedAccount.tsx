import { createContext, useContext, useState, type ReactNode } from 'react';

interface Ctx {
  selectedAccountId: string | null;
  setSelectedAccountId: (id: string) => void;
}

const C = createContext<Ctx>({ selectedAccountId: null, setSelectedAccountId: () => {} });

export function SelectedAccountProvider({ children }: { children: ReactNode }) {
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  return <C.Provider value={{ selectedAccountId, setSelectedAccountId }}>{children}</C.Provider>;
}

export function useSelectedAccount() {
  return useContext(C);
}
