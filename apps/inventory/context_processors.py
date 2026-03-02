import os
from django.conf import settings
from apps.company.models.company import Company


def logo_context(request):
    """Agrega la URL del logo de la empresa al contexto de todos los templates"""
    try:
        company = Company.objects.first()
        if company and company.logo:
            logo_url = company.logo.url
        else:
            logo_url = None
    except Exception:
        logo_url = None

    return {"logo_url": logo_url}
