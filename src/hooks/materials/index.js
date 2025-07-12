// materials/index.js

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { materialUpload } from '@/services/material.service';
import { toast } from 'sonner';

export const useUploadMaterial = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ['material-upload'],
    mutationFn: payload => materialUpload(payload).then(res => res), // ensure promise
    onSuccess: () => {
      // Invalidate any material‐related caches if you have them
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      toast.success('Material uploaded successfully');
    },
    onError: err => {
      toast.error(
        err.response?.data?.detail || 'Failed to upload material'
      );
    }
  });
};

