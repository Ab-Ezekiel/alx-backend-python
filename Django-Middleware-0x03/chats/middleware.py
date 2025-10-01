# Django-Middleware-0x03/chats/middleware.py
import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils import timezone
import time
import threading
from collections import deque
from django.http import HttpResponse, HttpResponseForbidden



# --- Logging setup ----------------------------------------------------------
logger = logging.getLogger(__name__)
# write to requests.log in project root
file_handler = logging.FileHandler("requests.log")
formatter = logging.Formatter("%(message)s")
file_handler.setFormatter(formatter)
# Avoid adding multiple handlers if module is reloaded (devserver)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename
           for h in logger.handlers):
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
# ----------------------------------------------------------------------------


class RequestLoggingMiddleware:
    """Log each request: timestamp, user (or Anonymous), and request path."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else "Anonymous"
        # Use timezone-aware time so logs align with Django settings
        now = timezone.localtime(timezone.now())
        log_message = f"{now.isoformat()} - User: {user} - Path: {request.path}"
        logger.info(log_message)
        return self.get_response(request)


class RestrictAccessByTimeMiddleware:
    """
    Deny access to configured chat endpoints outside allowed hours.

    Settings read from messaging_app/settings.py (with defaults):
      CHAT_ALLOWED_START_HOUR (int, default 6)  - inclusive start hour (0-23)
      CHAT_ALLOWED_END_HOUR   (int, default 21) - exclusive end hour (0-24)
      CHAT_URL_PREFIXES       (list[str])        - URL prefixes to treat as chat endpoints
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Read configuration from Django settings (use defaults if missing)
        self.start_hour = getattr(settings, "CHAT_ALLOWED_START_HOUR", 5)
        self.end_hour = getattr(settings, "CHAT_ALLOWED_END_HOUR", 23)
        self.prefixes = getattr(
            settings,
            "CHAT_URL_PREFIXES",
            ["/chats", "/api/conversations", "/api/messages"],
        )

    def _is_chat_path(self, path: str) -> bool:
        if not path:
            return False
        # match any configured prefix
        return any(path.startswith(prefix) for prefix in self.prefixes)

    def __call__(self, request):
        path = request.path or "/"
        if self._is_chat_path(path):
            # Use Django timezone utilities to be consistent with settings.USE_TZ and TIME_ZONE
            now = timezone.localtime(timezone.now())
            current_hour = now.hour
            # Allowed window semantics: start_hour <= hour < end_hour
            if current_hour < self.start_hour or current_hour >= self.end_hour:
                user = request.user if getattr(request, "user", None) and request.user.is_authenticated else "Anonymous"
                logger.info(f"{now.isoformat()} - BLOCK (outside allowed hours) - User: {user} - Path: {path}")
                return HttpResponseForbidden("Chat is available only during allowed hours.")
        return self.get_response(request)
    
class OffensiveLanguageMiddleware:
    """
    Rate-limit POST requests to chat endpoints by IP address.

    Settings (defaults):
      CHAT_RATE_LIMIT_COUNT  = 5
      CHAT_RATE_LIMIT_WINDOW = 60  # seconds
      CHAT_URL_PREFIXES      = ["/chats", "/api/conversations", "/api/messages"]
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = getattr(settings, "CHAT_RATE_LIMIT_COUNT", 5)
        self.window_seconds = getattr(settings, "CHAT_RATE_LIMIT_WINDOW", 60)
        self.prefixes = getattr(settings, "CHAT_URL_PREFIXES",
                                 ["/chats", "/api/conversations", "/api/messages"])
        self.ip_counters = {}  # { ip: deque([timestamps]) }
        self.lock = threading.Lock()

    def _is_chat_path(self, path: str) -> bool:
        if not path:
            return False
        return any(path.startswith(p) for p in self.prefixes)

    def _get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[0]
        return request.META.get("REMOTE_ADDR", "unknown")

    def __call__(self, request):
        path = request.path or "/"
        if request.method == "POST" and self._is_chat_path(path):
            client_ip = self._get_client_ip(request)
            now_ts = time.time()

            with self.lock:
                dq = self.ip_counters.get(client_ip)
                if dq is None:
                    dq = deque()
                    self.ip_counters[client_ip] = dq

                cutoff = now_ts - self.window_seconds
                while dq and dq[0] < cutoff:
                    dq.popleft()

                if len(dq) >= self.limit:
                    # Return 429 using generic HttpResponse for compatibility
                    resp = HttpResponse(
                        f"Rate limit exceeded: max {self.limit} messages per {self.window_seconds} seconds.",
                        status=429,
                        content_type="text/plain",
                    )
                    resp["Retry-After"] = str(int(self.window_seconds))
                    # Optionally log the event
                    logger.info(f"{timezone.localtime(timezone.now()).isoformat()} - RATE-LIMIT BLOCK ip={client_ip} path={path}")
                    return resp

                dq.append(now_ts)

        return self.get_response(request)
