from django.conf import settings

def feature_flags(request):
    return {
        'USE_CATALOG': getattr(settings, 'USE_CATALOG', False),
    }
