"""
Utilidad para firmar URLs de Bunny CDN con Token Authentication.

Bunny.net usa el siguiente formato para URLs firmadas:
https://{hostname}/{path}?token={token}&expires={expires}

Donde token = md5(security_key + path + expires)
en formato URL-safe Base64.

Ref: https://docs.bunny.net/docs/cdn-token-authentication
"""

import hashlib
import base64
import time
from urllib.parse import urlparse
from django.conf import settings


def sign_bunny_url(url: str, expiration_seconds: int = 3600) -> str:
    """
    Firma una URL de Bunny CDN con token authentication.

    Args:
        url: URL completa del recurso (ej: https://tripsdjangoapp.b-cdn.net/imagen.jpg)
        expiration_seconds: Tiempo de validez del token en segundos (default: 1 hora)

    Returns:
        URL firmada con token y expires
    """
    token_key = getattr(settings, "BUNNY_TOKEN_KEY", "")
    if not token_key:
        return url  # Sin token key, devolver URL sin firmar

    # Separar hostname y path
    parsed = urlparse(url)
    path = parsed.path

    # Calcular expiración redondeada a bloques de 1h
    # Así la misma imagen genera la MISMA URL durante 1h,
    # permitiendo que Bunny CDN y el navegador la cacheen.
    block = 3600  # 1 hora
    now = int(time.time())
    expires = now + expiration_seconds
    expires = expires - (expires % block) + block

    # Generar token: md5(security_key + path + expires)
    hashable = f"{token_key}{path}{expires}"
    token_digest = hashlib.md5(hashable.encode("utf-8")).digest()
    token = base64.b64encode(token_digest).decode("utf-8")

    # URL-safe: reemplazar +, / y quitar =
    token = token.replace("\n", "").replace("+", "-").replace("/", "_").replace("=", "")

    # Reconstruir URL con query params
    signed_url = f"{parsed.scheme}://{parsed.netloc}{path}?token={token}&expires={expires}"
    return signed_url
