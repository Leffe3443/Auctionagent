from django.conf import settings
from django.shortcuts import redirect

EXEMPT_PATHS = [settings.LOGIN_URL]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={path}")

        return self.get_response(request)
