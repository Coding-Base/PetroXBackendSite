from django.urls import path
from .views.auth import RegisterUserAPIView
from .views.courses import CourseListAPIView
from .views.materials import (
    MaterialUploadView, 
    MaterialDownloadView, 
    MaterialSearchView
)
from .views.questions import (
    AddQuestionAPIView,
    QuestionApprovalView,
    PreviewPassQuestionsView,
    UploadPassQuestionsView
)
from .views.sessions import (
    StartTestAPIView,
    SubmitTestAPIView,
    TestHistoryAPIView,
    TestSessionDetailAPIView
)
from .views.group_tests import CreateGroupTestAPIView, GroupTestDetailAPIView
from .views.leaderboard import LeaderboardAPIView, user_rank, user_upload_stats
# exams/urls.py

# from .views import (
#     RegisterUserAPIView,
#     CourseListAPIView,
#     MaterialUploadView,
#     MaterialDownloadView,
#     MaterialSearchView,
#     AddQuestionAPIView,
#     StartTestAPIView,
#     SubmitTestAPIView,
#     TestHistoryAPIView,
#     TestSessionDetailAPIView,
#     CreateGroupTestAPIView,
#     GroupTestDetailAPIView,
#     LeaderboardAPIView,
#     user_rank,
#     PreviewPassQuestionsView,
#     UploadPassQuestionsView,
#     QuestionApprovalView,
#     user_upload_stats
# )

urlpatterns = [
    path('users/', RegisterUserAPIView.as_view(), name='register-user'),
    path('materials/upload/', MaterialUploadView.as_view(), name='material-upload'),
    path('materials/download/<int:pk>/', MaterialDownloadView.as_view(), name='material-download'),
    path('materials/search/', MaterialSearchView.as_view(), name='material-search'),
    path('/api/courses/', CourseListAPIView.as_view(), name='course-list'),
    path('admin/add-question/', AddQuestionAPIView.as_view(), name='add-question'),
    path('start-test/', StartTestAPIView.as_view(), name='start-test'),
    path('submit-test/<int:session_id>/', SubmitTestAPIView.as_view(), name='submit-test'),
    path('history/', TestHistoryAPIView.as_view(), name='test-history'),
    path('test-session/<int:id>/', TestSessionDetailAPIView.as_view(), name='test-session-detail'),
    path('create-group-test/', CreateGroupTestAPIView.as_view(), name='create-group-test'),
    path('group-test/<int:pk>/', GroupTestDetailAPIView.as_view(), name='group-test-detail'),
    path('leaderboard/', LeaderboardAPIView.as_view(), name='leaderboard'),
    path('user/rank/', user_rank, name='user-rank'),
    path('upload-pass-questions/', UploadPassQuestionsView.as_view(), name='upload-pass-questions'),
    path('questions/pending/', QuestionApprovalView.as_view(), name='pending-questions'),
    path('questions/<int:question_id>/status/', QuestionApprovalView.as_view(), name='update-question-status'),
    path('user/upload-stats/', user_upload_stats, name='user-upload-stats'),
    path('preview-pass-questions/', PreviewPassQuestionsView.as_view(), name='preview-pass-questions'),
]
