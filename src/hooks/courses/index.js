import { useQuery, useMutation } from '@tanstack/react-query';
import { useQueryClient } from '@tanstack/react-query';
import { getCourses, addCourse } from '@/services/course.service';
import { toast } from 'sonner';

export const useAddCourse = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (course) => addCourse(course),
    mutationKey: ['add-course'],
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      toast.success('history created successfully');
    }
  });
};

export const useGetCourses = () => {
  return useQuery({
    queryKey: ['courses'],
    queryFn: () => getCourses(),
    staleTime: 5 * 60 * 1000,
    // gcTime: 10 * 60 * 1000,
    retry: 2
  });
};
