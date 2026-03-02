import hashlib
import logging
import time
from base64 import b64encode
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger("bunny_storage")


@deconstructible
class BunnyStorage(Storage):
    """
    Storage backend compatible con Django 6.0+ para Bunny.net CDN.
    Soporta URLs firmadas (Token Authentication).
    """

    def __init__(self):
        self.storage_zone = getattr(settings, "BUNNY_USERNAME", "")
        self.api_key = getattr(settings, "BUNNY_PASSWORD", "")
        self.cdn_url = getattr(settings, "BUNNY_CDN_URL", "")
        self.token_key = getattr(settings, "BUNNY_TOKEN_KEY", "")
        # Expiración de URLs firmadas en segundos (default: 7 días)
        self.token_expiration = getattr(settings, "BUNNY_TOKEN_EXPIRATION", 604800)
        # Región: vacío=Falkenstein(DE), ny=New York, la=Los Angeles,
        # sg=Singapore, syd=Sydney, br=Sao Paulo, jh=Johannesburg,
        # se=Stockholm, uk=London
        region = getattr(settings, "BUNNY_REGION", "")
        if region:
            self.storage_url = (
                f"https://{region}.storage.bunnycdn.com/{self.storage_zone}/"
            )
        else:
            self.storage_url = f"https://storage.bunnycdn.com/{self.storage_zone}/"

    def _headers(self, content_type="application/octet-stream"):
        h = {
            "AccessKey": self.api_key,
            "Accept": "application/json",
        }
        if content_type:
            h["Content-Type"] = content_type
        return h

    def get_available_name(self, name, max_length=None):
        """
        Ya usamos UUIDs en los nombres (generate_unique_filename),
        así que no necesitamos consultar la API para verificar existencia.
        Esto evita llamadas HTTP innecesarias y posibles cuelgues.
        """
        return name

    def _save(self, name, content):
        url = f"{self.storage_url}{name}"
        logger.info("Subiendo a Bunny: %s", url)

        # Asegurar que el puntero esté al inicio del archivo
        if hasattr(content, "seek"):
            content.seek(0)

        data = content.read()
        if not data:
            raise IOError("El contenido del archivo está vacío.")

        logger.debug("Tamaño del archivo: %d bytes", len(data))

        try:
            response = requests.put(
                url, headers=self._headers(), data=data, timeout=30
            )
        except requests.exceptions.Timeout:
            raise IOError("Timeout al subir archivo a Bunny.net (30s)")
        except requests.exceptions.ConnectionError as e:
            raise IOError(f"Error de conexión con Bunny.net: {e}")

        if response.status_code not in (200, 201):
            logger.error(
                "Bunny PUT %s -> %s: %s", url, response.status_code, response.text
            )
            raise IOError(
                f"Error subiendo archivo a Bunny.net: "
                f"{response.status_code} - {response.text}"
            )

        logger.info("Subida exitosa: %s (%d bytes)", name, len(data))
        return name

    def _open(self, name, mode="rb"):
        url = f"{self.storage_url}{name}"
        try:
            response = requests.get(url, headers=self._headers(None), timeout=30)
        except requests.exceptions.RequestException as e:
            raise FileNotFoundError(f"Error descargando de Bunny.net: {e}")
        if response.status_code != 200:
            raise FileNotFoundError(f"Archivo no encontrado en Bunny.net: {name}")
        return ContentFile(response.content)

    def exists(self, name):
        url = f"{self.storage_url}{name}"
        try:
            response = requests.head(url, headers=self._headers(None), timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def delete(self, name):
        url = f"{self.storage_url}{name}"
        try:
            response = requests.delete(url, headers=self._headers(None), timeout=15)
            if response.status_code not in (200, 404):
                logger.warning(
                    "Bunny DELETE %s -> %s", url, response.status_code
                )
        except requests.exceptions.RequestException as e:
            logger.warning("Error eliminando de Bunny: %s", e)

    def _sign_url(self, url, expiration_seconds=None):
        """
        Genera una URL firmada con Token Authentication de Bunny.net.
        Ref: https://docs.bunny.net/docs/cdn-token-authentication
        """
        if not self.token_key:
            return url

        if expiration_seconds is None:
            expiration_seconds = self.token_expiration

        expires = int(time.time()) + expiration_seconds

        # Extraer el path de la URL
        parsed = urlparse(url)
        path = parsed.path

        # Hash: SHA256(token_key + path + expires)
        hashable = f"{self.token_key}{path}{expires}"
        token_hash = hashlib.sha256(hashable.encode("utf-8")).digest()
        token = b64encode(token_hash).decode("utf-8")

        # Limpiar caracteres no válidos para URL
        token = (
            token.replace("\n", "")
            .replace("+", "-")
            .replace("/", "_")
            .replace("=", "")
        )

        return f"{url}?token={token}&expires={expires}"

    def url(self, name):
        """
        Retorna la URL pública del archivo.
        Si BUNNY_TOKEN_KEY está configurado, genera una URL firmada.
        """
        if self.cdn_url:
            base = self.cdn_url.rstrip("/")
            raw_url = f"{base}/{name}"
        else:
            raw_url = f"{self.storage_url}{name}"

        if self.token_key:
            return self._sign_url(raw_url)

        return raw_url

    def size(self, name):
        url = f"{self.storage_url}{name}"
        try:
            response = requests.head(url, headers=self._headers(None), timeout=5)
            if response.status_code == 200:
                return int(response.headers.get("Content-Length", 0))
        except requests.exceptions.RequestException:
            pass
        return 0

    def listdir(self, path=""):
        url = f"{self.storage_url}{path}"
        try:
            response = requests.get(url, headers=self._headers(None), timeout=15)
        except requests.exceptions.RequestException:
            return [], []
        if response.status_code != 200:
            return [], []

        dirs = []
        files = []
        for item in response.json():
            if item.get("IsDirectory"):
                dirs.append(item["ObjectName"])
            else:
                files.append(item["ObjectName"])
        return dirs, files
