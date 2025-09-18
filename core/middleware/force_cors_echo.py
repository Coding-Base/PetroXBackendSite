# core/middleware/force_cors_echo.py
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class ForceCORSEchoMiddleware(MiddlewareMixin):
    """
    TEMPORARY middleware to: 
      - log origin and requested preflight headers,
      - echo the request Origin back in Access-Control-Allow-Origin if allowed,
      - short-circuit OPTIONS preflight with proper headers.
    Remove after debugging.
    """

    # Build allowed origins from Django settings if present; fallback to common ones
    ALLOWED = getattr(settings, "CORS_ALLOWED_ORIGINS", None) or [
        "https://petrox-test-frontend.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def _allowed_origin(self, origin):
        if not origin:
            return None
        if origin in self.ALLOWED:
            return origin
        # sometimes the browser sends origin with trailing slash or different case — normalize
        normalized = origin.rstrip('/')
        for a in self.ALLOWED:
            if normalized == a.rstrip('/'):
                return a
        return None

    def process_request(self, request):
        origin = request.META.get("HTTP_ORIGIN")
        acrh = request.META.get("HTTP_ACCESS_CONTROL_REQUEST_HEADERS")
        logger.debug("ForceCORSEcho: incoming %s %s Origin=%s ACRH=%s", request.method, request.path, origin, acrh)

        allowed_origin = self._allowed_origin(origin)

        if request.method == "OPTIONS":
            resp = HttpResponse()
            if allowed_origin:
                resp["Access-Control-Allow-Origin"] = allowed_origin
            else:
                # if not allowed, still reply with no origin or you may choose to allow all for quick debug
                resp["Access-Control-Allow-Origin"] = origin or ""
            resp["Access-Control-Allow-Methods"] = "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS"
            # echo requested headers if present (helps match exact names)
            if acrh:
                resp["Access-Control-Allow-Headers"] = acrh
            else:
                resp["Access-Control-Allow-Headers"] = "authorization, content-type, x-upload-timeout"
            resp["Access-Control-Allow-Credentials"] = "false"
            resp["Access-Control-Max-Age"] = "86400"
            logger.debug("ForceCORSEcho: answered OPTIONS for %s (allow-origin=%s allow-headers=%s)", request.path, resp["Access-Control-Allow-Origin"], resp.get("Access-Control-Allow-Headers"))
            return resp
        return None

    def process_response(self, request, response):
        origin = request.META.get("HTTP_ORIGIN")
        allowed_origin = self._allowed_origin(origin)
        if allowed_origin:
            response["Access-Control-Allow-Origin"] = allowed_origin
        elif origin:
            # Echo origin even if not in list (debug only). For production restrict to allowed only.
            response["Access-Control-Allow-Origin"] = origin
        # allow the headers the browser asked for (if any), otherwise set defaults
        acrh = request.META.get("HTTP_ACCESS_CONTROL_REQUEST_HEADERS")
        if acrh:
            response["Access-Control-Allow-Headers"] = acrh
        else:
            response.setdefault("Access-Control-Allow-Headers", "authorization, content-type, x-upload-timeout")
        response.setdefault("Access-Control-Allow-Methods", "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS")
        response.setdefault("Access-Control-Allow-Credentials", "false")
        return response