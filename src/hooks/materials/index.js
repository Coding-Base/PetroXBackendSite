import { useQuery, useMutation } from '@tanstack/react-query';
import { useQueryClient } from '@tanstack/react-query';
import { materialUpload } from '@/services/material.service';
import { toast } from 'sonner';

export const useUploadMaterial = () => {
  // const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => materialUpload(payload),
    mutationKey: ['material'],
    onSuccess: () => {
      //   queryClient.invalidateQueries({ queryKey: ['courses'] });
      toast.success('Material Uploaded successfully');
    }
  });
};
