from django.conf import settings
from django.http import Http404
from functools import wraps

def require_catalog(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(settings, 'USE_CATALOG', False):
            raise Http404("Catálogo não disponível")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
