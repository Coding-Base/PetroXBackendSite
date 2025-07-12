import { api } from '@/api';

export const materialUpload = async (admin, signal) =>
  api.post('/api/materials/upload/', admin, { signal });
