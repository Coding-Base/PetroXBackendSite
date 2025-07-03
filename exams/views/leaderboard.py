from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import FloatField, F, ExpressionWrapper, Sum
from django.contrib.auth.models import User
from ..models import Question, TestSession

class LeaderboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.annotate(
            total_score=Sum('testsession__score'),
            total_questions=Sum('testsession__question_count')
        ).filter(
            total_questions__isnull=False,
            total_questions__gt=0
        ).annotate(
            avg_score=ExpressionWrapper(
                F('total_score') * 100.0 / F('total_questions'),
                output_field=FloatField()
            )
        ).order_by('-avg_score')[:10]

        data = [{
            'id': user.id,
            'username': user.username,
            'avg_score': user.avg_score,
            'tests_taken': user.testsession_set.count()
        } for user in users]

        return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_rank(request):
    users = User.objects.annotate(
        total_score=Sum('testsession__score'),
        total_questions=Sum('testsession__question_count')
    ).filter(
        total_questions__isnull=False,
        total_questions__gt=0
    ).annotate(
        avg_score=ExpressionWrapper(
            F('total_score') * 100.0 / F('total_questions'),
            output_field=FloatField()
        )
    ).order_by('-avg_score', 'id')
    
    ranked_users = list(users.values_list('id', flat=True))
    
    try:
        rank = ranked_users.index(request.user.id) + 1
    except ValueError:
        rank = None
        
    return Response({'rank': rank})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_upload_stats(request):
    approved_count = Question.objects.filter(
        uploaded_by=request.user,
        status='approved'
    ).count()
    
    return Response({
        'approved_uploads': approved_count
    })