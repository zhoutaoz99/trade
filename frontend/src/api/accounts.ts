import apiClient from './client';
import type { Account, CreateAccountRequest } from '../types';

export const createAccount = async (data: CreateAccountRequest): Promise<Account> => {
  const res = await apiClient.post('/api/v1/accounts', data);
  return res.data;
};

export const getAccount = async (id: string): Promise<Account> => {
  const res = await apiClient.get(`/api/v1/accounts/${id}`);
  return res.data;
};
