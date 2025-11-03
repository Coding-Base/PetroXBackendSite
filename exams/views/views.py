# exams/views.py
import os
import json
import requests
import logging
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

logger = logging.getLogger(__name__)

RENDER_SERVICE_ID = os.getenv('RENDER_SERVICE_ID', 'srv-cujrrlogph6c73bl2t40')
RENDER_API_KEY = os.getenv('RENDER_API_KEY')
RENDER_API_URL = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/jobs"


@staff_member_required
@require_POST
def trigger_render_job(request):
    """
    Trigger Render one-off job(s).
    POST JSON or form data:
      - email_ids: "123" or "123,124"  (comma separated)
      - test_to (optional)
      - batch_size, pause, timeout (optional)
    Returns JSON with job results.
    """
    if not RENDER_API_KEY:
        return JsonResponse({"error": "RENDER_API_KEY not configured on server"}, status=500)

    data = {}
    # support JSON and form-encoded
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode())
        except Exception:
            return HttpResponseBadRequest("Invalid JSON body.")
    else:
        data = request.POST.dict()

    email_ids = data.get('email_ids') or data.get('ids') or data.get('id')
    if not email_ids:
        return HttpResponseBadRequest("Missing 'email_ids' parameter.")

    ids = [i.strip() for i in str(email_ids).split(',') if i.strip()]
    if not ids:
        return HttpResponseBadRequest("No valid ids provided.")

    test_to = data.get('test_to')
    batch_size = data.get('batch_size') or str(getattr(settings, 'EMAIL_BATCH_SIZE', 20))
    pause = data.get('pause') or str(getattr(settings, 'EMAIL_BATCH_PAUSE', 0.5))
    timeout = data.get('timeout') or str(getattr(settings, 'EMAIL_TIMEOUT', getattr(settings, 'EMAIL_SMTP_TIMEOUT', 10)))

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json",
    }

    results = []
    for email_id in ids:
        if test_to:
            cmd = f"python manage.py send_emailmessage --id {email_id} --test-to {test_to} --timeout {timeout}"
        else:
            cmd = f"python manage.py send_emailmessage --id {email_id} --batch-size {batch_size} --pause {pause} --timeout {timeout}"

        body = {"startCommand": cmd}
        try:
            resp = requests.post(RENDER_API_URL, headers=headers, json=body, timeout=15)
        except requests.RequestException as exc:
            logger.exception("Render API request failed for id=%s: %s", email_id, exc)
            results.append({"email_id": email_id, "ok": False, "error": str(exc)})
            continue

        try:
            jr = resp.json()
        except Exception:
            jr = {"status_code": resp.status_code, "text": resp.text}

        if resp.status_code >= 400:
            results.append({"email_id": email_id, "ok": False, "status": resp.status_code, "body": jr})
        else:
            results.append({"email_id": email_id, "ok": True, "job": jr})

    return JsonResponse({"results": results})
