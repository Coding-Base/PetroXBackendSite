# exams/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from django.utils import timezone

User = settings.AUTH_USER_MODEL

class UserProfile(models.Model):
    """Extended user profile with registration number and department."""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    registration_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"


class SpecialCourse(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=0, help_text='Optional duration override')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def has_started(self):
        return timezone.now() >= self.start_time

    def has_finished(self):
        return timezone.now() > self.end_time

    def __str__(self):
        return self.title

class SpecialQuestion(models.Model):
    course = models.ForeignKey(SpecialCourse, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    mark = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)

    def __str__(self):
        return f"Q{self.id} - {self.course.title}"

class SpecialChoice(models.Model):
    question = models.ForeignKey(SpecialQuestion, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=1024)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Choice {self.id} for Q{self.question.id}"

class SpecialEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(SpecialCourse, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default=False)
    submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} -> {self.course}"

class SpecialAnswer(models.Model):
    enrollment = models.ForeignKey(SpecialEnrollment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SpecialQuestion, on_delete=models.CASCADE)
    choice = models.ForeignKey(SpecialChoice, on_delete=models.SET_NULL, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'question')



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

    # store Cloudinary (public) URL directly
    file = models.URLField(max_length=1000, blank=True)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def file_url(self):
        """
        Return a safe URL for the frontend:
        - if file is an absolute URL string -> return it
        - otherwise return '' (we don't attempt to read FieldFile from storage here)
        """
        f = getattr(self, "file", None)
        if not f:
            return ""
        if isinstance(f, str):
            return f
        # defensive fallback
        try:
            return f.url
        except Exception:
            return ""
