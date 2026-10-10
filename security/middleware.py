from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone


class SessionInactivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(timezone.now().timestamp())
            last_seen = request.session.get('last_seen_at', now)
            if now - last_seen > settings.SESSION_INACTIVITY_SECONDS:
                logout(request)
                return redirect('login')
            request.session['last_seen_at'] = now
        return self.get_response(request)
