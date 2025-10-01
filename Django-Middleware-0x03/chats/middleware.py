# Django-Middleware-0x03/chats/middleware.py
import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils import timezone
import time
import threading
from collections import deque
from django.http import HttpResponse, HttpResponseForbidden
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken



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


class RolePermissionMiddleware:
    """
    Middleware that enforces role-based permissions on protected chat paths.
    It will:
      - If Authorization: Bearer <token> header present, try to decode it and attach user to request.
      - For protected paths, allow only users with role 'admin' or 'moderator', or users with is_staff/is_superuser.
      - If no token and user not authenticated, return 403.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # tweak these paths as needed for your app
        self.protected_paths = [
            "/chats/admin",
            "/api/conversations/admin",
            "/api/messages/delete",
            # add more endpoints that require admin/moderator role
        ]

    def _path_is_protected(self, path: str) -> bool:
        if not path:
            return False
        return any(path.startswith(p) for p in self.protected_paths)

    def _get_user_from_token(self, token_str):
        """
        Try to decode an access token and return a Django user instance or None.
        """
        try:
            token = AccessToken(token_str)
            payload = getattr(token, "payload", None)
            if payload is None:
                # fallback: try to convert token to dict (rare)
                try:
                    payload = dict(token)
                except Exception:
                    return None
            # possible claim key: 'user_id' or 'user_id' depending on setup
            user_id = payload.get("user_id") or payload.get("user_id")
            if not user_id:
                return None
            User = get_user_model()
            return User.objects.filter(pk=user_id).first()
        except Exception:
            return None

    def __call__(self, request):
        path = request.path or "/"

        # If there's a Bearer token, try to decode and attach a user to request
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ", 1)[1].strip()
            user = self._get_user_from_token(token_str)
            if user:
                # attach user to request so permission checks see it
                request.user = user

        # If the path is protected, enforce role check
        if self._path_is_protected(path):
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                return JsonResponse({"error": "Authentication required"}, status=403)

            # allow staff/superuser
            if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
                return self.get_response(request)

            # check custom role attribute if present
            role = getattr(user, "role", None)
            if role in ("admin", "moderator"):
                return self.get_response(request)

            return JsonResponse({"error": "Permission denied"}, status=403)

        # non-protected path — continue
        return self.get_response(request)
