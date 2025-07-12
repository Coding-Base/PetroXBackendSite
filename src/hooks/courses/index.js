// hooks/useCourses.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getCourses, addCourse } from '@/services/course.service';

export const useGetCourses = () =>
  useQuery({
    queryKey: ['courses'],
    queryFn: getCourses,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

export const useAddCourse = () => {
  const qc = useQueryClient();
  return useMutation(addCourse, {
    mutationKey: ['add-course'],
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['courses'] });
      toast.success('Course created successfully');
    },
    onError: err => {
      toast.error(err.response?.data?.detail || 'Failed to create course');
    },
  });
};
