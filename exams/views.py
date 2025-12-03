"""
Email trigger view removed.

This module previously exposed an admin-only endpoint that triggered Render jobs
to run the removed `send_emailmessage` command. The email feature was removed
from the project; keep this stub in place to avoid import errors elsewhere.
"""

from django.http import JsonResponse

def removed_email_trigger(request, *args, **kwargs):
    return JsonResponse({"error": "Email feature removed"}, status=410)
