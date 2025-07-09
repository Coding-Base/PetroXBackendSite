from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='approved')

    def __str__(self):
        return self.name

class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    year =  models.CharField(max_length=255, default='2019')
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    correct_option = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ])
    source_file = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return self.question_text[:50]

class TestSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)
    question_count = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField()  # in seconds
    score = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.course.name}"

class GroupTest(models.Model):
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_count = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    invitees = models.TextField()  # Comma-separated emails
    scheduled_start = models.DateTimeField()
    
    def __str__(self):
        return self.name

class Material(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    tags = models.CharField(max_length=255, blank=True)
    file = models.FileField(
        upload_to='materials/',
        storage='exams.storage_backends.GoogleCloudMediaStorage'  # Fixed: use string path
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def file_url(self):
        return self.file.url if self.file else ''
