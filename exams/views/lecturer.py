import csv
from io import BytesIO
from datetime import datetime

from django.http import HttpResponse
from django.db.models import Count, Q, Avg
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView

from ..models import SpecialCourse, SpecialQuestion, SpecialChoice, SpecialEnrollment, SpecialAnswer, UserProfile
from ..serializers import SpecialCourseSerializer, LecturerQuestionSerializer 
from lecturer_dashboard.models import LecturerAccount 

class IsLecturer(permissions.BasePermission):
    def has_permission(self, request, view):
        return LecturerAccount.objects.filter(user=request.user).exists()

class LecturerCourseViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialCourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return SpecialCourse.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        course = self.get_object()
        if course.created_by != self.request.user:
            raise permissions.PermissionDenied("You can only update your own courses.")
        serializer.save()

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        course = self.get_object()
        enrollments = SpecialEnrollment.objects.filter(course=course)
        
        total_students = enrollments.count()
        submitted_count = enrollments.filter(submitted=True).count()
        scores = enrollments.filter(submitted=True).values_list('score', flat=True)
        
        if submitted_count > 0:
            avg_score = sum(scores) / submitted_count
            passed = sum(1 for s in scores if s >= 50)
            failed = submitted_count - passed
            success_rate = (passed / submitted_count) * 100
            failure_rate = (failed / submitted_count) * 100
        else:
            avg_score = 0; passed = 0; failed = 0; success_rate = 0; failure_rate = 0

        return Response({
            'total_students': total_students,
            'submitted': submitted_count,
            'not_submitted': total_students - submitted_count,
            'average_score': round(avg_score, 2),
            'passed': passed,
            'failed': failed,
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2),
        })

    @action(detail=True, methods=['get'])
    def export_results(self, request, pk=None):
        course = self.get_object()
        enrollments = SpecialEnrollment.objects.filter(course=course, submitted=True).select_related('user')
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(['Student Name', 'Username', 'Email', 'Score', 'Submitted At', 'Course Title'])
        for enrollment in enrollments:
            writer.writerow([
                enrollment.user.get_full_name() or enrollment.user.username,
                enrollment.user.username,
                enrollment.user.email,
                enrollment.score,
                enrollment.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if enrollment.submitted_at else '',
                course.title
            ])
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="course_{course.id}_results.csv"'
        return response

class LecturerQuestionViewSet(viewsets.ModelViewSet):
    # Use the serializer that includes 'is_correct'
    serializer_class = LecturerQuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    # Add JSONParser so bulk_create works
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        lecturer_courses = SpecialCourse.objects.filter(created_by=self.request.user)
        return SpecialQuestion.objects.filter(course__in=lecturer_courses)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=self.request.user)
        except SpecialCourse.DoesNotExist:
            raise permissions.PermissionDenied("You can only add questions to your own courses.")
        serializer.save()

    def perform_update(self, serializer):
        question = self.get_object()
        if question.course.created_by != self.request.user:
            raise permissions.PermissionDenied("You can only update questions in your own courses.")
        serializer.save()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        questions_data = request.data.get('questions', [])
        course_id = request.data.get('course_id')
        
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=request.user)
        except SpecialCourse.DoesNotExist:
            return Response({'error': 'Course not found or permission denied'}, status=status.HTTP_404_NOT_FOUND)

        created_questions = []
        for q_data in questions_data:
            question = SpecialQuestion.objects.create(
                course=course,
                text=q_data.get('text'),
                mark=q_data.get('mark', 1)
            )
            for choice_data in q_data.get('choices', []):
                SpecialChoice.objects.create(
                    question=question,
                    text=choice_data.get('text'),
                    is_correct=choice_data.get('is_correct', False)
                )
            created_questions.append(LecturerQuestionSerializer(question).data)

        return Response({'created': len(created_questions), 'questions': created_questions}, status=status.HTTP_201_CREATED)

class LecturerEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsLecturer]

    def get_queryset(self):
        lecturer_courses = SpecialCourse.objects.filter(created_by=self.request.user)
        return SpecialEnrollment.objects.filter(course__in=lecturer_courses)

    def get_serializer_class(self):
        from ..serializers import EnrollmentSerializer
        return EnrollmentSerializer

    @action(detail=False, methods=['get'])
    def course_enrollments(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'error': 'course_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=request.user)
        except SpecialCourse.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        enrollments = SpecialEnrollment.objects.filter(course=course)
        from ..serializers import EnrollmentSerializer
        serializer = EnrollmentSerializer(enrollments, many=True)
        
        return Response({
            'course': SpecialCourseSerializer(course).data,
            'enrollments': serializer.data,
            'total': enrollments.count(),
            'submitted': enrollments.filter(submitted=True).count(),
            'pending': enrollments.filter(submitted=False).count(),
        })

class LecturerProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response({'error': 'Endpoint deprecated.'}, status=status.HTTP_410_GONE)
