# exams/admin.py
from django.contrib import admin, messages
from .models import Course, Question, TestSession, GroupTest, Material, EmailMessage
from django.utils.html import format_html
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import logging
import time
from django.core.paginator import Paginator
import socket
import ssl

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
        """
        Batched email sender with resilient handling.

        - Uses django-anymail/SendGrid (HTTP) when settings.USE_SENDGRID is True.
        - Falls back to SMTP if USE_SENDGRID is False.
        - Sends in batches using settings.EMAIL_BATCH_SIZE and sleeps EMAIL_BATCH_PAUSE between batches.
        """
        # Config: batch size and pause
        batch_size = max(1, int(getattr(settings, 'EMAIL_BATCH_SIZE', 20)))
        pause_seconds = float(getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5))
        email_timeout = int(getattr(settings, 'EMAIL_TIMEOUT', getattr(settings, 'EMAIL_SMTP_TIMEOUT', 20)))
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)

        use_sendgrid = getattr(settings, 'USE_SENDGRID', True)

        # Build connection - for Anymail this will use HTTP API; for SMTP it will use socket
        try:
            connection = mail.get_connection(timeout=email_timeout)
        except TypeError:
            # older django versions: no timeout arg
            connection = mail.get_connection()

        # Try to open connection, but be tolerant and show admin-friendly messages
        try:
            connection.open()
        except Exception as e:
            # Provide helpful guidance depending on configuration
            logger.exception("Failed to open mail connection: %s", e)

            if use_sendgrid:
                # If using SendGrid via Anymail, likely cause is API key missing/invalid,
                # or provider rejected the request — but Anymail usually returns HTTP errors.
                # Render free-tier SMTP block doesn't apply for API, but network errors may still
                # occur if API key is wrong or outbound HTTPS restricted.
                self.message_user(
                    request,
                    (
                        "Failed to open mail connection (SendGrid/Anymail). "
                        "Check SENDGRID_API_KEY in environment, and check SendGrid dashboard for any blocks. "
                        f"Error: {e}"
                    ),
                    level=messages.ERROR
                )
            else:
                # Using SMTP: often caused by blocked outbound SMTP (e.g. Render free-tier) or wrong host/port.
                self.message_user(
                    request,
                    (
                        "Failed to open SMTP connection. This is commonly due to outbound SMTP ports "
                        "being blocked on cloud providers (Render free tier blocks ports 25/465/587) "
                        "or incorrect SMTP credentials/host. "
                        f"Error: {e}"
                    ),
                    level=messages.ERROR
                )
            # Abort sending
            return

        total_sent = 0

        # base queryset (only active users with email)
        users_qs = User.objects.filter(is_active=True).exclude(email='').order_by('id')
        total_emails = users_qs.count()

        if total_emails == 0:
            self.message_user(request, "No active users with email addresses found.", level=messages.WARNING)
            try:
                connection.close()
            except Exception:
                pass
            return

        # iterate through selected EmailMessage objects
        for email_obj in queryset:
            if email_obj.sent_at:
                self.message_user(request, f"Email '{email_obj.subject}' was already sent", level=messages.WARNING)
                continue

            success_count = 0
            paginator = Paginator(users_qs, batch_size)

            for page_num in paginator.page_range:
                try:
                    page = paginator.page(page_num)
                except Exception as e:
                    logger.exception("Failed to fetch page %s: %s", page_num, e)
                    continue

                email_messages = []
                for user in page.object_list:
                    if not user.email:
                        continue
                    try:
                        context = {
                            'user': user,
                            'content': email_obj.content,
                            'button_text': email_obj.button_text,
                            'button_link': email_obj.button_link,
                            'subject': email_obj.subject,
                            'FRONTEND_DOMAIN': getattr(settings, 'FRONTEND_DOMAIN', '')
                        }

                        # render template; fallback if it fails
                        try:
                            html_content = render_to_string('email/email_template.html', context)
                        except Exception as render_error:
                            logger.exception(
                                "Template render error for user %s: %s",
                                getattr(user, 'email', '<no email>'),
                                render_error
                            )
                            link_html = ''
                            if email_obj.button_text and email_obj.button_link:
                                link_html = '<a href="{0}">{1}</a>'.format(email_obj.button_link, email_obj.button_text)

                            html_content = (
                                '<html><body>'
                                '<h2>{subject}</h2>'
                                '<div>{content}</div>'
                                '{link_html}'
                                '<p>Sent by Petrox Assessment Platform</p>'
                                '</body></html>'
                            ).format(subject=email_obj.subject, content=email_obj.content, link_html=link_html)

                        # plain-text
                        text_content = "{}\n\n{}\n\n".format(email_obj.subject, email_obj.content)
                        if email_obj.button_text and email_obj.button_link:
                            text_content += "{}: {}\n\n".format(email_obj.button_text, email_obj.button_link)
                        text_content += "Unsubscribe: {}/unsubscribe".format(getattr(settings, 'FRONTEND_DOMAIN', '').rstrip('/'))

                        msg = mail.EmailMultiAlternatives(
                            subject=email_obj.subject,
                            body=text_content,
                            from_email=default_from,
                            to=[user.email],
                            connection=connection
                        )
                        msg.attach_alternative(html_content, "text/html")
                        email_messages.append(msg)

                    except Exception as e:
                        logger.exception("Email preparation failed for %s: %s", getattr(user, 'email', None), e)
                        # continue to next user

                # try to send the batch; handle socket/ssl timeouts explicitly
                try:
                    if email_messages:
                        sent_count = connection.send_messages(email_messages) or 0
                        # connection.send_messages may return integer or list - normalize:
                        if isinstance(sent_count, (list, tuple)):
                            sent_count = len(sent_count)
                        success_count += int(sent_count)
                        total_sent += int(sent_count)
                        logger.info("Sent batch %s/%s (%s emails)", page_num, paginator.num_pages, sent_count)
                except (socket.timeout, ssl.SSLError) as net_err:
                    logger.exception("Network/SMTP timeout or SSL error sending batch %s: %s", page_num, net_err)
                    self.message_user(request, f"Network error sending batch {page_num}: {net_err}", level=messages.ERROR)
                    # Skip this batch and continue — avoid crashing admin action
                except Exception as e:
                    # Log the detailed error and show a helpful admin message
                    logger.exception("Failed to send batch %s: %s", page_num, e)
                    # If using SendGrid/Anymail, include hint about API key / provider logs
                    hint = ""
                    if use_sendgrid:
                        hint = " (Check SENDGRID_API_KEY, SendGrid dashboard, and that Anymail is installed.)"
                    else:
                        hint = " (Check SMTP host/port/credentials and provider restrictions.)"

                    self.message_user(request, f"Failed to send batch {page_num}: {e}{hint}", level=messages.ERROR)

                # pause between batches to reduce spikes / respect rate limits
                try:
                    if pause_seconds:
                        time.sleep(pause_seconds)
                except Exception:
                    pass

            # mark email object as sent (this marks after trying all batches; adjust if you want stricter semantics)
            email_obj.sent_at = timezone.now()
            try:
                email_obj.save(update_fields=['sent_at'])
            except Exception:
                logger.exception("Failed to mark EmailMessage %s as sent_at", getattr(email_obj, 'id', '<unknown>'))

            self.message_user(
                request,
                "Sent '{}' to {}/{} users".format(email_obj.subject, success_count, total_emails),
                level=messages.SUCCESS
            )

        # close connection
        try:
            connection.close()
        except Exception:
            pass

        self.message_user(
            request,
            "Total: Sent {} emails out of {} recipients".format(total_sent, total_emails),
            level=messages.INFO
        )

    send_emails.short_description = "Send selected emails to all users"

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent_at:
            return [f.name for f in self.model._meta.fields] + ['status_display']
        return super().get_readonly_fields(request, obj)
