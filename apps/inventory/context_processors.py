import os
from django.conf import settings


def logo_context(request):
    """Agrega la URL del logo al contexto de todos los templates"""
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    
    if os.path.exists(logo_path):
        logo_url = settings.MEDIA_URL + 'logo.png'
    else:
        logo_url = None
    
    return {'logo_url': logo_url}
