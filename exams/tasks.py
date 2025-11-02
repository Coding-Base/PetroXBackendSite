# exams/tasks.py
import logging
import time
import gc
import socket
import ssl
from django.core import mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

import requests  # used for exception class (requests.exceptions.RequestException)

from .models import EmailMessage

logger = logging.getLogger(__name__)
User = get_user_model()


def send_emailmessage_task(email_id: int, batch_size: int = None, pause: float = None, timeout: int = None, test_to: str = None):
    """
    Background job to send EmailMessage with id=email_id.
    - batch_size: number of emails per batch
    - pause: seconds to sleep between batches
    - timeout: per-request timeout (seconds) for external HTTP calls (SendGrid)
    - test_to: if provided, send only to this recipient (for testing)
    """
    batch_size = int(batch_size or getattr(settings, 'EMAIL_BATCH_SIZE', 20))
    pause = float(pause if pause is not None else getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5))
    timeout = int(timeout or getattr(settings, 'EMAIL_TIMEOUT', getattr(settings, 'EMAIL_SMTP_TIMEOUT', 10)))
    default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    use_sendgrid = getattr(settings, 'USE_SENDGRID', True)

    try:
        email_obj = EmailMessage.objects.get(pk=email_id)
    except EmailMessage.DoesNotExist:
        logger.error("send_emailmessage_task: EmailMessage id=%s not found", email_id)
        return {"status": "error", "reason": "not_found"}

    if email_obj.sent_at:
        logger.info("send_emailmessage_task: EmailMessage id=%s already sent at %s", email_id, email_obj.sent_at)
        return {"status": "skipped", "sent_at": str(email_obj.sent_at)}

    # Build recipients
    if test_to:
        recipients = [test_to]
    else:
        users_qs = User.objects.filter(is_active=True).exclude(email='').order_by('id')
        recipients = list(users_qs.values_list('email', flat=True))

    total_recipients = len(recipients)
    if total_recipients == 0:
        logger.warning("send_emailmessage_task: no recipients for email id=%s", email_id)
        return {"status": "no_recipients"}

    total_sent = 0

    # Chunk recipients into batches
    for i in range(0, total_recipients, batch_size):
        chunk = recipients[i:i + batch_size]
        email_messages = []
        for to_email in chunk:
            try:
                # If you want to pass user context when available, you'd fetch user here.
                # For now we render without per-user personalization (or extend to fetch user by email).
                context = {
                    'user': None,
                    'content': email_obj.content,
                    'button_text': email_obj.button_text,
                    'button_link': email_obj.button_link,
                    'subject': email_obj.subject,
                    'FRONTEND_DOMAIN': getattr(settings, 'FRONTEND_DOMAIN', '')
                }

                try:
                    html_content = render_to_string('email/email_template.html', context)
                except Exception as e:
                    logger.exception("Template render error for %s: %s", to_email, e)
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
                    from_email=default_from,
                    to=[to_email],
                )
                msg.attach_alternative(html_content, "text/html")
                email_messages.append(msg)
            except Exception:
                logger.exception("Failed to prepare message for %s", to_email)
                # continue to next recipient

        if not email_messages:
            gc.collect()
            continue

        # send this batch with a fresh connection and timeout wrapper if necessary
        try:
            try:
                connection = mail.get_connection(timeout=timeout)
            except TypeError:
                connection = mail.get_connection()

            if hasattr(connection, 'session') and getattr(connection, 'session', None) is not None:
                orig_request = getattr(connection.session, 'request', None)
                if callable(orig_request):
                    def _request_with_timeout(method, url, **kwargs):
                        if 'timeout' not in kwargs or kwargs.get('timeout') is None:
                            kwargs['timeout'] = timeout
                        return orig_request(method, url, **kwargs)
                    connection.session.request = _request_with_timeout  # type: ignore

            connection.open()
        except Exception as e:
            logger.exception("Failed to open mail connection for batch starting at %s: %s", i, e)
            # skip this batch and continue
            continue

        try:
            sent_count = connection.send_messages(email_messages) or 0
            if isinstance(sent_count, (list, tuple)):
                sent_count = len(sent_count)
            sent_count = int(sent_count)
            total_sent += sent_count
            logger.info("send_emailmessage_task: sent %s emails for batch starting at %s", sent_count, i)
        except (socket.timeout, ssl.SSLError, requests.exceptions.RequestException) as net_err:
            logger.exception("Network error sending batch starting at %s: %s", i, net_err)
        except Exception:
            logger.exception("Failed to send batch starting at %s", i)
        finally:
            try:
                connection.close()
            except Exception:
                pass

        try:
            del email_messages
        except Exception:
            pass
        gc.collect()

        if pause:
            time.sleep(pause)

    # mark as sent
    email_obj.sent_at = timezone.now()
    try:
        email_obj.save(update_fields=['sent_at'])
    except Exception:
        logger.exception("Failed to save sent_at for EmailMessage id=%s", email_id)

    logger.info("send_emailmessage_task: done id=%s total_sent=%s/%s", email_id, total_sent, total_recipients)
    return {"status": "done", "total_sent": total_sent, "total_recipients": total_recipients}
