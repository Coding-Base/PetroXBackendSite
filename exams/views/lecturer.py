"""
Lecturer Dashboard API Views
Handles course management, question creation, and results export for lecturers
"""
import csv
from io import BytesIO
from datetime import datetime

from django.http import HttpResponse
from django.db.models import Count, Q, Avg
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework.views import APIView

from ..models import SpecialCourse, SpecialQuestion, SpecialChoice, SpecialEnrollment, SpecialAnswer, UserProfile
from ..serializers import SpecialCourseSerializer, QuestionSerializer

# IMPORT THE LECTURER ACCOUNT MODEL
from lecturer_dashboard.models import LecturerAccount 


class IsLecturer(permissions.BasePermission):
    """Permission class to ensure user is a lecturer"""
    def has_permission(self, request, view):
        # FIX: Check if the user exists in the LecturerAccount table
        return LecturerAccount.objects.filter(user=request.user).exists()


class IsLecturerOwner(permissions.BasePermission):
    """Permission class to ensure lecturer can only manage their own courses"""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class LecturerCourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lecturer to manage their special courses
    """
    serializer_class = SpecialCourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        """Lecturers can only see their own courses"""
        return SpecialCourse.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """Automatically set created_by to current user"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Ensure lecturer can only update their own courses"""
        course = self.get_object()
        if course.created_by != self.request.user:
            raise permissions.PermissionDenied("You can only update your own courses.")
        serializer.save()

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get analytics for a specific course"""
        course = self.get_object()
        enrollments = SpecialEnrollment.objects.filter(course=course)
        
        total_students = enrollments.count()
        submitted_count = enrollments.filter(submitted=True).count()
        scores = enrollments.filter(submitted=True).values_list('score', flat=True)
        
        if submitted_count > 0:
            avg_score = sum(scores) / submitted_count
            # Assuming 50% is passing score
            passed = sum(1 for s in scores if s >= 50)
            failed = submitted_count - passed
            success_rate = (passed / submitted_count) * 100
            failure_rate = (failed / submitted_count) * 100
        else:
            avg_score = 0
            passed = 0
            failed = 0
            success_rate = 0
            failure_rate = 0

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
        """Export course results to Excel"""
        course = self.get_object()
        enrollments = SpecialEnrollment.objects.filter(
            course=course,
            submitted=True
        ).select_related('user')

        # Create CSV in memory
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Student Name', 'Username', 'Email', 'Score', 'Submitted At', 'Course Title'])
        
        # Write data
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
        response['Content-Disposition'] = f'attachment; filename="course_{course.id}_results_{datetime.now().strftime("%Y%m%d")}.csv"'
        return response


class LecturerQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lecturer to manage questions in their courses
    """
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    parser_classes = (MultiPartParser, FormParser,JSONParser)

    def get_queryset(self):
        """Get questions for lecturer's courses only"""
        lecturer_courses = SpecialCourse.objects.filter(created_by=self.request.user)
        return SpecialQuestion.objects.filter(course__in=lecturer_courses)

    def perform_create(self, serializer):
        """Create a question (course must belong to lecturer)"""
        course_id = self.request.data.get('course')
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=self.request.user)
        except SpecialCourse.DoesNotExist:
            raise permissions.PermissionDenied("You can only add questions to your own courses.")
        
        serializer.save()

    def perform_update(self, serializer):
        """Update a question (must belong to lecturer's course)"""
        question = self.get_object()
        if question.course.created_by != self.request.user:
            raise permissions.PermissionDenied("You can only update questions in your own courses.")
        serializer.save()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create questions from JSON array"""
        questions_data = request.data.get('questions', [])
        course_id = request.data.get('course_id')
        
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=request.user)
        except SpecialCourse.DoesNotExist:
            return Response(
                {'error': 'Course not found or you do not have permission'},
                status=status.HTTP_404_NOT_FOUND
            )

        created_questions = []
        for q_data in questions_data:
            question = SpecialQuestion.objects.create(
                course=course,
                text=q_data.get('text'),
                mark=q_data.get('mark', 1)
            )
            
            # Create choices
            for choice_data in q_data.get('choices', []):
                SpecialChoice.objects.create(
                    question=question,
                    text=choice_data.get('text'),
                    is_correct=choice_data.get('is_correct', False)
                )
            
            created_questions.append(QuestionSerializer(question).data)

        return Response({
            'created': len(created_questions),
            'questions': created_questions
        }, status=status.HTTP_201_CREATED)


class LecturerEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Lecturer to view enrollments in their courses
    """
    permission_classes = [permissions.IsAuthenticated, IsLecturer]

    def get_queryset(self):
        """Get enrollments for lecturer's courses only"""
        lecturer_courses = SpecialCourse.objects.filter(created_by=self.request.user)
        return SpecialEnrollment.objects.filter(course__in=lecturer_courses)

    def get_serializer_class(self):
        from ..serializers import EnrollmentSerializer
        return EnrollmentSerializer

    @action(detail=False, methods=['get'])
    def course_enrollments(self, request):
        """Get enrollments by course with statistics"""
        course_id = request.query_params.get('course_id')
        
        if not course_id:
            return Response(
                {'error': 'course_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            course = SpecialCourse.objects.get(id=course_id, created_by=request.user)
        except SpecialCourse.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

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
    """API view to get lecturer profile - DEPRECATED
    Use /api/lecturer/profile/ from lecturer_dashboard app instead
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Return redirect message
        return Response(
            {'error': 'Endpoint deprecated. Use /api/lecturer/profile/ instead'},
            status=status.HTTP_410_GONE
        )

