import { api } from '@/api';

export const materialUpload = async (admin, signal) =>
  api.post('/materials/upload/', admin, { signal });
