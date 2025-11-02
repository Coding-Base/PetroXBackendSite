# core/management/commands/send_emailmessage.py
import time
import gc
import socket
import ssl
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core import mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from exams.models import EmailMessage
import requests

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Send an EmailMessage (by id) to all active users in safe batches. Run as a one-off worker."

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help='EmailMessage id to send', required=True)
        parser.add_argument('--batch-size', type=int, default=int(getattr(settings, 'EMAIL_BATCH_SIZE', 20)))
        parser.add_argument('--pause', type=float, default=float(getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5)))
        parser.add_argument('--timeout', type=int, default=int(getattr(settings, 'EMAIL_TIMEOUT', 10)))
        parser.add_argument('--test-to', type=str, help='If set, send only to this recipient (useful for quick test)')

    def handle(self, *args, **options):
        email_id = options['id']
        batch_size = max(1, options['batch_size'])
        pause = options['pause']
        timeout = options['timeout']
        test_to = options.get('test_to')

        try:
            email_obj = EmailMessage.objects.get(pk=email_id)
        except EmailMessage.DoesNotExist:
            raise CommandError(f"EmailMessage id={email_id} not found")

        if email_obj.sent_at:
            self.stdout.write(self.style.WARNING(f"EmailMessage id={email_id} already has sent_at={email_obj.sent_at}"))
            # continue anyway if you want, or exit:
            # return

        # Build recipient queryset (or test recipient)
        if test_to:
            recipients = [test_to]
            total_recipients = 1
        else:
            users_qs = User.objects.filter(is_active=True).exclude(email='').order_by('id')
            total_recipients = users_qs.count()

        if total_recipients == 0:
            self.stdout.write(self.style.WARNING("No recipients found."))
            return

        self.stdout.write(self.style.NOTICE(f"Starting send for EmailMessage id={email_id} to {total_recipients} recipients (batch={batch_size})"))
        total_sent = 0

        # If sending to test_to only do a single batch
        if test_to:
            pages = [[test_to]]
        else:
            paginator = Paginator(users_qs, batch_size)
            pages = [paginator.page(p).object_list for p in paginator.page_range]

        for batch_index, batch in enumerate(pages, start=1):
            email_messages = []
            for user in batch:
                try:
                    # if batch contains user instances vs emails unify:
                    if hasattr(user, 'email'):
                        to_email = user.email
                    else:
                        to_email = user

                    context = {
                        'user': user if hasattr(user, 'email') else None,
                        'content': email_obj.content,
                        'button_text': email_obj.button_text,
                        'button_link': email_obj.button_link,
                        'subject': email_obj.subject,
                        'FRONTEND_DOMAIN': getattr(settings, 'FRONTEND_DOMAIN', '')
                    }

                    try:
                        html_content = render_to_string('email/email_template.html', context)
                    except Exception as e:
                        logger.exception("Template render failed for %s: %s", to_email, e)
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

                    text_content = "{}\n\n{}\n\n".format(email_obj.subject, email_obj.content)
                    if email_obj.button_text and email_obj.button_link:
                        text_content += "{}: {}\n\n".format(email_obj.button_text, email_obj.button_link)
                    text_content += "Unsubscribe: {}/unsubscribe".format(getattr(settings, 'FRONTEND_DOMAIN', '').rstrip('/'))

                    msg = mail.EmailMultiAlternatives(
                        subject=email_obj.subject,
                        body=text_content,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        to=[to_email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    email_messages.append(msg)
                except Exception as e:
                    logger.exception("Failed to prepare message for %s: %s", getattr(user, 'email', user), e)

            if not email_messages:
                self.stdout.write(self.style.WARNING(f"Batch {batch_index} has no messages, skipping"))
                gc.collect()
                continue

            # Create a fresh connection per batch and attach a timeout wrapper for requests if needed
            try:
                try:
                    connection = mail.get_connection(timeout=timeout)
                except TypeError:
                    connection = mail.get_connection()

                # If connection uses session (Anymail uses requests.Session) wrap request to include timeout
                if hasattr(connection, 'session') and callable(getattr(connection, 'session').request):
                    orig_req = connection.session.request
                    def req_with_timeout(method, url, **kwargs):
                        if 'timeout' not in kwargs or kwargs.get('timeout') is None:
                            kwargs['timeout'] = timeout
                        return orig_req(method, url, **kwargs)
                    connection.session.request = req_with_timeout  # type: ignore

                connection.open()
            except Exception as e:
                logger.exception("Failed to open connection for batch %s: %s", batch_index, e)
                self.stderr.write(f"Failed to open connection for batch {batch_index}: {e}")
                # skip this batch
                continue

            try:
                sent = connection.send_messages(email_messages) or 0
                if isinstance(sent, (list, tuple)):
                    sent = len(sent)
                sent = int(sent)
                total_sent += sent
                self.stdout.write(self.style.SUCCESS(f"Batch {batch_index}: sent {sent} messages"))
            except (socket.timeout, ssl.SSLError, requests.exceptions.RequestException) as net_err:
                logger.exception("Network error sending batch %s: %s", batch_index, net_err)
                self.stderr.write(f"Network error sending batch {batch_index}: {net_err}")
            except Exception as e:
                logger.exception("Failed to send batch %s: %s", batch_index, e)
                self.stderr.write(f"Failed to send batch {batch_index}: {e}")
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

            # cleanup & pause
            try:
                del email_messages
            except Exception:
                pass
            gc.collect()
            if pause:
                time.sleep(pause)

        # mark message as sent (or you can choose to record partial send)
        email_obj.sent_at = getattr(email_obj, 'sent_at', None) or timezone.now()
        email_obj.save(update_fields=['sent_at'])

        self.stdout.write(self.style.SUCCESS(f"Done. Total sent (approx): {total_sent}/{total_recipients}"))
