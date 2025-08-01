from django.contrib import admin
from .models import Course, Question, TestSession, GroupTest, Material, EmailMessage
from django.utils.html import format_html
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import logging
import os

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

    def send_emails(self, request, queryset):
        # Create a single connection for all emails
        connection = mail.get_connection()
        connection.open()
        
        total_sent = 0
        total_emails = 0
        
        for email in queryset:
            if email.sent_at:
                self.message_user(
                    request,
                    f"Email '{email.subject}' was already sent",
                    level='WARNING'
                )
                continue
                
            # Optimized query to only get needed fields
            users = User.objects.filter(is_active=True).exclude(email='').only('email')
            total_emails += len(users)
            success_count = 0
            
            # Send emails in batches
            batch_size = 20
            for i in range(0, len(users), batch_size):
                batch_users = users[i:i+batch_size]
                email_messages = []
                
                for user in batch_users:
                    try:
                        # Prepare context
                        context = {
                            'user': user,
                            'content': email.content,
                            'button_text': email.button_text,
                            'button_link': email.button_link,
                            'subject': email.subject,
                            'FRONTEND_DOMAIN': settings.FRONTEND_DOMAIN
                        }
                        
                        # Render template with fallback
                        try:
                            html_content = render_to_string('email/email_template.html', context)
                        except Exception as render_error:
                            logger.error(f"Template render error: {render_error}")
                            html_content = f"""
                            <html>
                            <body>
                                <h2>{email.subject}</h2>
                                <div>{email.content}</div>
                                {f'<a href="{email.button_link}">{email.button_text}</a>' if email.button_text else ''}
                                <p>Sent by Petrox Assessment Platform</p>
                            </body>
                            </html>
                            """
                        
                        # Create plain text version
                        text_content = f"{email.subject}\n\n{email.content}\n\n"
                        if email.button_text and email.button_link:
                            text_content += f"{email.button_text}: {email.button_link}\n\n"
                        text_content += f"Unsubscribe: {settings.FRONTEND_DOMAIN}/unsubscribe"
                        
                        # Create email message
                        msg = mail.EmailMultiAlternatives(
                            subject=email.subject,
                            body=text_content,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[user.email],
                            connection=connection  # Use shared connection
                        )
                        msg.attach_alternative(html_content, "text/html")
                        email_messages.append(msg)
                        
                    except Exception as e:
                        logger.error(f"Email preparation failed: {e}")
                        self.message_user(
                            request,
                            f"Failed to prepare email for {user.email}: {str(e)}",
                            level='ERROR'
                        )
                
                # Send the batch
                try:
                    connection.send_messages(email_messages)
                    success_count += len(email_messages)
                    total_sent += len(email_messages)
                except Exception as e:
                    logger.error(f"Email sending failed: {e}")
                    self.message_user(
                        request,
                        f"Failed to send batch: {str(e)}",
                        level='ERROR'
                    )
            
            # Update sent status
            email.sent_at = timezone.now()
            email.save()
            
            self.message_user(
                request,
                f"Sent '{email.subject}' to {success_count}/{len(users)} users",
                level='SUCCESS'
            )
        
        # Close the connection
        connection.close()
        
        self.message_user(
            request,
            f"Total: Sent {total_sent} emails out of {total_emails} recipients",
            level='INFO'
        )
    
    send_emails.short_description = "Send selected emails to all users"
    
    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only after sending
        if obj and obj.sent_at:
            return [f.name for f in self.model._meta.fields] + ['status_display']
        return super().get_readonly_fields(request, obj)
