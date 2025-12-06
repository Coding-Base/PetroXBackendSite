# exams/admin.py
import os
import json
import logging
import time
import socket
import ssl
import requests
import gc
import io

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

from .models import Course, Question, TestSession, GroupTest, Material

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


# --- Below: SpecialCourse / SpecialQuestion / SpecialChoice / SpecialEnrollment Admins ---
# The original file repeated imports and then declared these; preserved here.

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
        try:
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

            # Use context manager to correctly flush/close writer (no writer.save())
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='results')

            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=exam_results.xlsx'
            return response
        except Exception as exc:
            logger.exception("Failed to export selected enrollments: %s", exc)
            self.message_user(request, f"Failed to generate export: {str(exc)}", level=messages.ERROR)
            return

    export_results.short_description = 'Export selected enrollments to Excel'


@admin.register(SpecialAnswer)
class SpecialAnswerAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'question', 'choice', 'answered_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_number', 'department', 'created_at')
    search_fields = ('user__username', 'registration_number', 'department')
