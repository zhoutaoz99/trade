import axios from 'axios';
import { toast } from 'sonner';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Request failed';
    toast.error(msg);
    return Promise.reject(error);
  },
);

export default apiClient;
