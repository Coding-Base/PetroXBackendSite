"""
Lecturer Dashboard API Views
Handles course management, question creation, and results export for lecturers
"""
import csv
from datetime import datetime

from django.http import HttpResponse
from django.db.models import Count, Q, Avg, Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView

from ..models import SpecialCourse, SpecialQuestion, SpecialChoice, SpecialEnrollment, SpecialAnswer, UserProfile
from ..serializers import SpecialCourseSerializer, LecturerQuestionSerializer, EnrollmentSerializer

# IMPORT THE LECTURER ACCOUNT MODEL
from lecturer_dashboard.models import LecturerAccount 


class IsLecturer(permissions.BasePermission):
    """Permission class to ensure user is a lecturer"""
    def has_permission(self, request, view):
        # Check if the user exists in the LecturerAccount table
        return LecturerAccount.objects.filter(user=request.user).exists()


class LecturerCourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lecturer to manage their special courses
    """
    serializer_class = SpecialCourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    # JSONParser added to support JSON payloads if needed, alongside file uploads
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
        """Export course results to CSV, grouped by department"""
        course = self.get_object()
        
        # Fetch submitted enrollments with related user and profile data
        # Ordering by department first ensures grouping in the CSV
        enrollments = SpecialEnrollment.objects.filter(
            course=course,
            submitted=True
        ).select_related('user', 'user__profile').order_by('user__profile__department', 'user__last_name')

        response = HttpResponse(content_type='text/csv')
        filename = f"course_{course.id}_results_{datetime.now().strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        
        # Updated Header
        writer.writerow(['Full Name', 'Reg Number', 'Department', 'Email', 'Score', 'Submitted At', 'Course Title'])
        
        # Write data rows
        for enrollment in enrollments:
            # Safely get profile data
            profile = getattr(enrollment.user, 'profile', None)
            reg_number = getattr(profile, 'registration_number', 'N/A') if profile else 'N/A'
            department = getattr(profile, 'department', 'N/A') if profile else 'N/A'
            
            # Prefer Full Name over Username
            full_name = enrollment.user.get_full_name() or enrollment.user.username

            writer.writerow([
                full_name,
                reg_number,
                department,
                enrollment.user.email,
                enrollment.score,
                enrollment.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if enrollment.submitted_at else '',
                course.title
            ])

        return response


class LecturerQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lecturer to manage questions in their courses
    """
    # Use the serializer that includes 'is_correct' field
    serializer_class = LecturerQuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturer]
    # JSONParser is CRITICAL here for bulk_create to work from the frontend
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
            
            created_questions.append(LecturerQuestionSerializer(question).data)

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
        return EnrollmentSerializer

    @action(detail=False, methods=['get'])
    def course_enrollments(self, request):
        """Get enrollments by course with statistics and nested User info"""
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

        # Fetch enrollments with user profile data
        enrollments = SpecialEnrollment.objects.filter(course=course).select_related('user', 'user__profile')
        
        # Calculate Total Marks for the Course to calculate raw scores
        # Sum of all question marks in this course
        total_marks = SpecialQuestion.objects.filter(course=course).aggregate(Sum('mark'))['mark__sum'] or 0

        # Manually construct response data to include nested profile info
        # This replaces the EnrollmentSerializer for this specific view to avoid "user": ID issues
        enrollment_data = []
        for env in enrollments:
            profile = getattr(env.user, 'profile', None)
            
            enrollment_data.append({
                "id": env.id,
                "score": env.score,
                "submitted": env.submitted,
                "enrolled_at": env.enrolled_at,
                "started": env.started,
                "user": {
                    "username": env.user.username,
                    "email": env.user.email,
                    "first_name": env.user.first_name,
                    "last_name": env.user.last_name,
                    "profile": {
                        "department": getattr(profile, 'department', 'N/A'),
                        "registration_number": getattr(profile, 'registration_number', 'N/A')
                    }
                }
            })
        
        return Response({
            'course': SpecialCourseSerializer(course).data,
            'enrollments': enrollment_data,
            'total_marks': total_marks,  # Send total marks so frontend can show "10/15"
            'total': enrollments.count(),
            'submitted': enrollments.filter(submitted=True).count(),
            'pending': enrollments.filter(submitted=False).count(),
        })


class LecturerProfileView(APIView):
    """API view to get lecturer profile - DEPRECATED"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {'error': 'Endpoint deprecated. Use /api/lecturer/profile/ instead'},
            status=status.HTTP_410_GONE
)
