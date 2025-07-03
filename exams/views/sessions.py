import random
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import Course, Question, TestSession
from ..serializers import TestSessionSerializer

class StartTestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get('course_id')
        count = int(request.data.get('question_count', 0))
        duration = int(request.data.get('duration', 0))

        course = get_object_or_404(Course, id=course_id)
        questions = list(course.questions.filter(status='approved').all())
        if count > len(questions):
            return Response(
                {'error': 'Not enough questions in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        chosen = random.sample(questions, count)
        session = TestSession.objects.create(
            user=request.user,
            course=course,
            duration=duration,
            question_count=len(chosen))
        session.questions.set(chosen)
        serializer = TestSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SubmitTestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(
            TestSession, id=session_id, user=request.user
        )
        answers = request.data.get('answers', {})
        score = 0
        for q in session.questions.all():
            if str(answers.get(str(q.id), '')).upper() == q.correct_option.upper():
                score += 1

        session.score = score
        session.end_time = timezone.now()
        session.save()

        serializer = TestSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TestHistoryAPIView(generics.ListAPIView):
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestSession.objects.filter(
            user=self.request.user
        ).order_by('-start_time')

class TestSessionDetailAPIView(generics.RetrieveAPIView):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer
    lookup_field = 'id' 