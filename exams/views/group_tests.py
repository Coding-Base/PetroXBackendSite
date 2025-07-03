from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ..models import Course, Question, TestSession, GroupTest, User
import random

class CreateGroupTestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        required_fields = [
            'name', 'course', 'question_count',
            'duration_minutes', 'invitees', 'scheduled_start'
        ]
        if not all(field in request.data for field in required_fields):
            return Response(
                {'error': 'Missing required fields. All fields are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        name = request.data['name']
        course_id = request.data['course']
        question_count = request.data['question_count']
        duration_minutes = request.data['duration_minutes']
        invitees_list = request.data['invitees']
        raw_sched = request.data['scheduled_start']

        dt = parse_datetime(raw_sched)
        if dt is None:
            return Response(
                {'error': 'Invalid scheduled_start format. Use ISO‐UTC string.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=timezone.utc)

        scheduled_start = dt

        try:
            group_test = GroupTest.objects.create(
                name=name,
                course_id=course_id,
                question_count=question_count,
                duration_minutes=duration_minutes,
                created_by=request.user,
                invitees=",".join(invitees_list),
                scheduled_start=scheduled_start
            )
        except Exception as e:
            return Response(
                {'error': f'Error creating group test: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invitees_list:
            try:
                subject = f"Invitation to Group Test: {group_test.name}"
                context = {
                    'test_name': group_test.name,
                    'course': group_test.course.name,
                    'inviter': request.user.username,
                    'question_count': group_test.question_count,
                    'duration': group_test.duration_minutes,
                    'scheduled_start': group_test.scheduled_start,
                    'domain': settings.FRONTEND_DOMAIN,
                    'test_id': group_test.id
                }

                html_message = render_to_string('email/group_test_invite.html', context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject,
                    plain_message,
                    settings.EMAIL_HOST_USER,
                    invitees_list,
                    html_message=html_message,
                    fail_silently=False
                )
            except Exception as e:
                print(f"Error sending emails: {e}")

        return Response({
            'id': group_test.id,
            'name': group_test.name,
            'course': group_test.course.name,
            'scheduled_start': group_test.scheduled_start
        }, status=status.HTTP_201_CREATED)
    
class GroupTestDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        group_test = get_object_or_404(GroupTest, pk=pk)
        now = timezone.now()

        data = {
            'id': group_test.id,
            'name': group_test.name,
            'course': {
                'id': group_test.course.id,
                'name': group_test.course.name
            },
            'question_count': group_test.question_count,
            'duration_minutes': group_test.duration_minutes,
            'scheduled_start': group_test.scheduled_start,
        }

        if now >= group_test.scheduled_start:
            questions_qs = list(group_test.course.questions.filter(status='approved').all())
            if len(questions_qs) < group_test.question_count:
                return Response(
                    {'error': 'Not enough questions in this course.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            chosen = random.sample(questions_qs, group_test.question_count)
            session = TestSession.objects.create(
                user=request.user,
                course=group_test.course,
                duration=group_test.duration_minutes * 60,
                question_count=group_test.question_count
            )
            session.questions.set(chosen)

            q_list = []
            for q in chosen:
                q_list.append({
                    'id': q.id,
                    'question_text': q.question_text,
                    'option_a': q.option_a,
                    'option_b': q.option_b,
                    'option_c': q.option_c,
                    'option_d': q.option_d,
                })

            data['questions'] = q_list
            data['session_id'] = session.id
        else:
            data['questions'] = []
            data['session_id'] = None

        return Response(data)