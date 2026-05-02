from django.http import HttpResponse
from django.template.loader import render_to_string
from decouple import config


class MaintenanceModeMiddleware:
    """
    Returns HTTP 503 with templates/503.html when MAINTENANCE_MODE=True.
    Admin URLs (/admin/) are always allowed through.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if config('MAINTENANCE_MODE', default=False, cast=bool):
            if not request.path.startswith('/admin/'):
                html = render_to_string('503.html')
                return HttpResponse(html, status=503, content_type='text/html; charset=utf-8')
        return self.get_response(request)
