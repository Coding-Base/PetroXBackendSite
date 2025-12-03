# exams/admin.py
import os
import json
import logging
import time
import socket
import ssl
import requests
import gc

from django.contrib import admin, messages
from django.utils.html import format_html
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import path, reverse

import django_rq

from .models import Course, Question, TestSession, GroupTest, Material, EmailMessage

logger = logging.getLogger(__name__)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'course', 'uploaded_by', 'uploaded_at', 'download_link')
    search_fields = ('name', 'course__name', 'tags')
    list_filter = ('course', 'uploaded_at')
    readonly_fields = ('uploaded_by', 'uploaded_at')
    exclude = ('file_url',)

    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file_url)
        return "-"
    download_link.short_description = 'File'


@admin.register(GroupTest)
class GroupTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'course', 'created_by', 'scheduled_start', 'invitee_count')
    search_fields = ('name', 'course__name', 'created_by__username')
    list_filter = ('course', 'created_by', 'scheduled_start')
    readonly_fields = ('created_at', 'invitee_list')

    def invitee_count(self, obj):
        return len(obj.invitees.split(',')) if obj.invitees else 0
    invitee_count.short_description = 'Invitees'

    def invitee_list(self, obj):
        return format_html('<br>'.join(obj.invitees.split(','))) if obj.invitees else '-'
    invitee_list.short_description = 'Invitee List'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'question_count', 'status')
    search_fields = ('name',)
    list_filter = ('status',)

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'truncated_question',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'correct_option',
        'course',
        'status_badge',
        'uploaded_by',
        'source_file',
        'created_at_display'
    )
    list_filter = ('course', 'status', 'uploaded_by')
    search_fields = ('question_text', 'option_a', 'option_b', 'option_c', 'option_d')
    readonly_fields = ('uploaded_by', 'created_at', 'source_file')
    actions = ['approve_questions', 'reject_questions']
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('course', 'question_text', 'status')
        }),
        ('Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_option')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'source_file', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def truncated_question(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    truncated_question.short_description = 'Question'

    def status_badge(self, obj):
        color = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }.get(obj.status, 'gray')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
            color,
            obj.status.capitalize()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else '-'
    created_at_display.short_description = 'Uploaded'

    def approve_questions(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} question(s) approved")
    approve_questions.short_description = "Approve selected questions"

    def reject_questions(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} question(s) rejected")
    reject_questions.short_description = "Reject selected questions"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'course',
        'start_time',
        'end_time',
        'score_percentage',
        'duration_formatted'
    )
    list_filter = ('course', 'user', 'start_time')
    readonly_fields = ('start_time', 'end_time', 'score', 'user', 'course', 'questions_list')
    search_fields = ('user__username', 'course__name')

    def questions_list(self, obj):
        return format_html('<br>'.join([q.question_text[:100] for q in obj.questions.all()]))
    questions_list.short_description = 'Questions'

    def score_percentage(self, obj):
        if obj.score is not None and obj.question_count > 0:
            percentage = (obj.score / obj.question_count) * 100
            return f"{percentage:.1f}% ({obj.score}/{obj.question_count})"
        return '-'
    score_percentage.short_description = 'Score'

    def duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}m {seconds}s"
        return '-'
    duration_formatted.short_description = 'Duration'

    def has_add_permission(self, request):
        return False


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent_at', 'status_display')
    readonly_fields = ('created_at', 'sent_at', 'status_display')
    fields = (
        'subject',
        'content',
        'button_text',
        'button_link',
        'created_at',
        'sent_at',
        'status_display'
    )
    actions = ['send_emails']

    def status_display(self, obj):
        if obj.sent_at:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Sent</span>'
            )
        return format_html(
            '<span style="color: #cc0000; font-weight: bold;">✗ Not Sent</span>'
        )
    status_display.short_description = 'Status'

    # ---------------------------
    # Admin action: enqueue to RQ
    # ---------------------------
    def send_emails(self, request, queryset):
        """
        Enqueue selected EmailMessage objects to the RQ worker.
        The worker will run exams.tasks.send_emailmessage_task for each id.
        """
        queue = django_rq.get_queue('default')
        batch_size = int(getattr(settings, 'EMAIL_BATCH_SIZE', 20))
        pause = float(getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5))
        timeout = int(getattr(settings, 'EMAIL_TIMEOUT', getattr(settings, 'EMAIL_SMTP_TIMEOUT', 10)))

        for email_obj in queryset:
            if email_obj.sent_at:
                self.message_user(request, f"Email '{email_obj.subject}' (id={email_obj.id}) was already sent at {email_obj.sent_at}", level=messages.WARNING)
                continue

            # enqueue the task
            job = queue.enqueue(
                'exams.tasks.send_emailmessage_task',
                email_obj.id,
                batch_size,
                pause,
                timeout,
                None,  # test_to = None for real run
                job_timeout=int(getattr(settings, 'RQ_JOB_TIMEOUT', 7200))
            )

            # notify admin with job id and run info
            self.message_user(request, f"Enqueued '{email_obj.subject}' (id={email_obj.id}) as job {job.id}.", level=messages.SUCCESS)
            self.message_user(request, f"Run status / logs available in your worker logs. For local test: python manage.py send_emailmessage --id {email_obj.id} --test-to youremail@example.com", level=messages.INFO)
    send_emails.short_description = "Queue selected emails for background sending (RQ worker)"

    # ---------------------------
    # Admin: Render one-off trigger per-object
    # ---------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/trigger-render-send/', self.admin_site.admin_view(self.admin_trigger_send), name='exams_emailmessage_trigger'),
        ]
        return custom_urls + urls

    def admin_trigger_send(self, request, object_id, *args, **kwargs):
        """
        Admin-only endpoint that triggers a Render one-off job for the given EmailMessage id.
        Creates a Render job that runs:
          python manage.py send_emailmessage --id <object_id> --batch-size ... --pause ... --timeout ...
        """
        # Security check (admin_site.admin_view already ensures login + staff)
        try:
            email_obj = EmailMessage.objects.get(pk=object_id)
        except EmailMessage.DoesNotExist:
            self.message_user(request, "EmailMessage not found.", level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_changelist')))

        if email_obj.sent_at:
            self.message_user(request, f"'{email_obj.subject}' was already sent at {email_obj.sent_at}.", level=messages.WARNING)
            return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_change', args=[object_id])))

        # Build command and call Render API
        batch_size = int(getattr(settings, 'EMAIL_BATCH_SIZE', 20))
        pause = float(getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5))
        timeout = int(getattr(settings, 'EMAIL_TIMEOUT', getattr(settings, 'EMAIL_SMTP_TIMEOUT', 10)))

        service_id = os.getenv('RENDER_SERVICE_ID', 'srv-cujrrlogph6c73bl2t40')
        api_key = os.getenv('RENDER_API_KEY')
        if not api_key:
            self.message_user(request, "Render API key not configured (RENDER_API_KEY). Set env var and retry.", level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_change', args=[object_id])))

        if request.method == 'POST':
            # create startCommand
            start_cmd = f"python manage.py send_emailmessage --id {object_id} --batch-size {batch_size} --pause {pause} --timeout {timeout}"
            api_url = f"https://api.render.com/v1/services/{service_id}/jobs"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {"startCommand": start_cmd}

            try:
                resp = requests.post(api_url, headers=headers, json=body, timeout=15)
            except requests.RequestException as exc:
                logger.exception("Render API error for email_id=%s: %s", object_id, exc)
                self.message_user(request, f"Render API request failed: {exc}", level=messages.ERROR)
                return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_change', args=[object_id])))

            if resp.status_code >= 400:
                try:
                    jr = resp.json()
                except Exception:
                    jr = {"status_code": resp.status_code, "text": resp.text}
                self.message_user(request, format_html("Render API returned an error: <pre>{}</pre>", jr), level=messages.ERROR)
            else:
                try:
                    jr = resp.json()
                except Exception:
                    jr = {"status_code": resp.status_code, "text": resp.text}
                job_id = jr.get('id') or jr.get('jobId') or jr.get('job_id') or '(unknown)'
                self.message_user(request, format_html("Created Render job <strong>{}</strong>. Check Render dashboard jobs for logs.", job_id), level=messages.SUCCESS)

            return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_change', args=[object_id])))

        # If not POST, show clickable button as admin info message (admin-only)
        trigger_url = reverse('admin:exams_emailmessage_trigger', args=[object_id])
        # Use a small HTML form simulated link to POST via JS for convenience
        html = format_html(
            '<form style="display:inline" method="post" action="{}">'
            '{{% csrf_token %}}'
            '<button type="submit" class="button" style="background:#4CAF50;color:white;border:none;padding:6px 12px;border-radius:4px;">Trigger one-off send (Render job)</button>'
            '</form>',
            trigger_url
        )
        # Because we cannot render template tokens inside format_html, provide a normal link
        # The admin csrf token won't be present in this message; instead we show the POST URL and instruct the admin.
        info_html = format_html(
            'To trigger a Render one-off job for this EmailMessage, click the button (requires POST): '
            '<a href="{}" style="padding:6px 12px;background:#2196F3;color:white;border-radius:4px;text-decoration:none;">Trigger one-off send (create Render job)</a>'
            '<br><small>If you want a safer test, use the management command: <code>python manage.py send_emailmessage --id {}</code></small>',
            reverse('admin:exams_emailmessage_trigger', args=[object_id]),
            object_id
        )
        # Display the clickable link as an admin message (staff only will see it)
        self.message_user(request, info_html, level=messages.INFO)
        # Redirect back to change page so the admin message appears at top
        return redirect(request.META.get('HTTP_REFERER', reverse('admin:exams_emailmessage_change', args=[object_id])))

    # ---------------------------
    # readonly fields helper
    # ---------------------------
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent_at:
            return [f.name for f in self.model._meta.fields] + ['status_display']
        return super().get_readonly_fields(request, obj)


from django.contrib import admin
from .models import (
    SpecialCourse,
    SpecialQuestion,
    SpecialChoice,
    SpecialEnrollment,
    SpecialAnswer,
    UserProfile,
)
from django.http import HttpResponse
import io
try:
    import pandas as pd
except Exception:
    pd = None


# Inline to manage choices when editing a question
class ChoiceInline(admin.TabularInline):
    model = SpecialChoice
    extra = 1


# Inline to manage questions when editing a course
class QuestionInline(admin.StackedInline):
    model = SpecialQuestion
    extra = 1
    show_change_link = True


@admin.register(SpecialCourse)
class SpecialCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'created_by')
    search_fields = ('title', 'description')
    list_filter = ('start_time', 'end_time', 'created_by')
    inlines = [QuestionInline]


@admin.register(SpecialQuestion)
class SpecialQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'truncated_text', 'mark')
    search_fields = ('text',)
    list_filter = ('course',)
    inlines = [ChoiceInline]

    def truncated_text(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    truncated_text.short_description = 'Question'


@admin.register(SpecialChoice)
class SpecialChoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text', 'is_correct')
    search_fields = ('text',)


@admin.register(SpecialEnrollment)
class SpecialEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'started', 'submitted', 'score')
    actions = ['export_results']

    def export_results(self, request, queryset):
        """Export selected enrollments to Excel, grouped by department."""
        if pd is None:
            self.message_user(request, 'pandas/openpyxl not installed on server.', level=messages.ERROR)
            return
        rows = []
        for e in queryset.select_related('user'):
            profile = getattr(e.user, 'profile', None)
            rows.append({
                'name': e.user.get_full_name() or str(e.user),
                'registration_number': getattr(profile, 'registration_number', ''),
                'department': getattr(profile, 'department', ''),
                'score': e.score if e.score is not None else '',
            })
        df = pd.DataFrame(rows)
        df = df.sort_values(['department', 'name'])
        buffer = io.BytesIO()
        writer = pd.ExcelWriter(buffer, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='results')
        writer.save()
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=exam_results.xlsx'
        return response
    export_results.short_description = 'Export selected enrollments to Excel'


@admin.register(SpecialAnswer)
class SpecialAnswerAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'question', 'choice', 'answered_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_number', 'department', 'created_at')
    search_fields = ('user__username', 'registration_number', 'department')
