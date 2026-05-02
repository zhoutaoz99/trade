import { useState } from 'react';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Button from '../ui/Button';
import { useCreateAccount } from '../../hooks/useAccounts';
import type { AccountType, CreateAccountRequest } from '../../types';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function CreateAccountModal({ open, onClose }: Props) {
  const mutation = useCreateAccount();
  const [name, setName] = useState('');
  const [accountType, setAccountType] = useState<AccountType>('simulated');
  const [initialBalance, setInitialBalance] = useState('10000');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');

  const handleSubmit = () => {
    const payload: CreateAccountRequest = {
      name,
      account_type: accountType,
      quote_asset: 'USDT',
    };
    if (accountType === 'simulated') {
      payload.initial_balance = initialBalance;
    } else {
      payload.api_key = apiKey;
      payload.api_secret = apiSecret;
    }
    mutation.mutate(payload, {
      onSuccess: () => {
        setName('');
        setInitialBalance('10000');
        setApiKey('');
        setApiSecret('');
        onClose();
      },
    });
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Account">
      <div className="flex flex-col gap-4">
        <Input label="Account Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="my-trading-account" />
        <Select
          label="Account Type"
          value={accountType}
          onChange={(e) => setAccountType(e.target.value as AccountType)}
          options={[
            { value: 'simulated', label: 'Simulated (paper trading)' },
            { value: 'live', label: 'Live (Binance API)' },
          ]}
        />
        {accountType === 'simulated' ? (
          <Input label="Initial Balance (USDT)" value={initialBalance} onChange={(e) => setInitialBalance(e.target.value)} type="number" />
        ) : (
          <>
            <Input label="Binance API Key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="your-api-key" />
            <Input label="Binance API Secret" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} type="password" placeholder="your-api-secret" />
          </>
        )}
        <Button onClick={handleSubmit} loading={mutation.isPending} disabled={!name.trim()} className="mt-2">
          Create Account
        </Button>
      </div>
    </Modal>
  );
}
