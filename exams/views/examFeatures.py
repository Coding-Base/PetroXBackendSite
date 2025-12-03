from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import SpecialCourse, SpecialEnrollment, SpecialQuestion, SpecialChoice, SpecialAnswer
from ..serializers import SpecialCourseSerializer, EnrollmentSerializer, QuestionSerializer, SubmitExamSerializer
from django.db import transaction
from django.http import HttpResponse
import io
try:
    import pandas as pd
except Exception:
    pd = None

class SpecialCourseList(generics.ListAPIView):
    serializer_class = SpecialCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = SpecialCourse.objects.all().order_by('-start_time')
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_enrolled_courses(request):
    """Get all courses the user has enrolled for, with pagination."""
    enrollments = SpecialEnrollment.objects.filter(user=request.user).select_related('course').order_by('-enrolled_at')
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = enrollments.count()
    paginated_enrollments = enrollments[start:end]
    
    data = {
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': []
    }
    
    for enrollment in paginated_enrollments:
        course = enrollment.course
        data['results'].append({
            'id': enrollment.id,
            'course': SpecialCourseSerializer(course).data,
            'enrolled_at': enrollment.enrolled_at,
            'started': enrollment.started,
            'submitted': enrollment.submitted,
            'score': enrollment.score,
        })
    
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_course(request, course_id):
    course = get_object_or_404(SpecialCourse, id=course_id)
    enrollment, created = SpecialEnrollment.objects.get_or_create(user=request.user, course=course)
    serializer = EnrollmentSerializer(enrollment)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def enrollment_detail(request, enrollment_id):
    e = get_object_or_404(SpecialEnrollment, id=enrollment_id, user=request.user)
    data = {
        'id': e.id,
        'course': SpecialCourseSerializer(e.course).data,
        'started': e.started,
        'submitted': e.submitted,
    }
    if e.course.has_started() and not e.submitted:
        questions = SpecialQuestion.objects.filter(course=e.course).prefetch_related('choices')
        data['questions'] = QuestionSerializer(questions, many=True).data
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_exam(request, enrollment_id):
    e = get_object_or_404(SpecialEnrollment, id=enrollment_id, user=request.user)
    if e.course.has_finished():
        return Response({'detail': 'Exam already finished.'}, status=status.HTTP_400_BAD_REQUEST)
    e.started = True
    e.save()
    return Response({'ok': True})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def submit_exam(request, enrollment_id):
    e = get_object_or_404(SpecialEnrollment, id=enrollment_id, user=request.user)
    if e.submitted:
        return Response({'detail': 'Already submitted.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = SubmitExamSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    answers = serializer.validated_data['answers']
    total_score = 0
    total_possible = 0
    for a in answers:
        q = get_object_or_404(SpecialQuestion, id=a['question'])
        selected_choice = None
        if a.get('choice'):
            selected_choice = SpecialChoice.objects.filter(id=a['choice'], question=q).first()
        SpecialAnswer.objects.update_or_create(enrollment=e, question=q, defaults={'choice': selected_choice})
        total_possible += q.mark
        if selected_choice and selected_choice.is_correct:
            total_score += q.mark
    e.score = (total_score / total_possible) * 100 if total_possible else 0
    e.submitted = True
    e.submitted_at = timezone.now()
    e.save()
    return Response({'ok': True, 'score': e.score})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def finalize_due_exams(request):
    now = timezone.now()
    finalized = []
    due_courses = SpecialCourse.objects.filter(end_time__lt=now)
    for c in due_courses:
        enrollments = SpecialEnrollment.objects.filter(course=c, submitted=False)
        for e in enrollments:
            total_possible = 0
            total_score = 0
            for q in c.questions.all():
                total_possible += q.mark
                ans = e.answers.filter(question=q).first()
                if ans and ans.choice and ans.choice.is_correct:
                    total_score += q.mark
            e.score = (total_score / total_possible) * 100 if total_possible else 0
            e.submitted = True
            e.submitted_at = now
            e.save()
            finalized.append(e.id)
    return Response({'finalized_count': len(finalized)})

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def export_course_results(request, course_id):
    if pd is None:
        return Response({'detail':'pandas/openpyxl not installed on server'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    enrollments = SpecialEnrollment.objects.filter(course_id=course_id, submitted=True).select_related('user', 'user__profile')
    rows = []
    for e in enrollments:
        profile = getattr(e.user, 'profile', None)
        rows.append({
            'name': e.user.get_full_name() or str(e.user),
            'registration_number': getattr(profile, 'registration_number', '') if profile else '',
            'department': getattr(profile, 'department', '') if profile else '',
            'score': e.score,
        })
    df = pd.DataFrame(rows).sort_values(['department', 'name'])
    buffer = io.BytesIO()
    writer = pd.ExcelWriter(buffer, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='results')
    writer.save(); buffer.seek(0)
    resp = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename=results_{course_id}.xlsx'
    return resp
