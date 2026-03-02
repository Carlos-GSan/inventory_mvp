#!/usr/bin/env python
"""
Script de verificación post-despliegue para Disitech Project.
Verifica que todos los componentes estén correctamente configurados.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection


def print_status(check_name, passed, message=""):
    """Imprime el estado de una verificación."""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {check_name}", end="")
    if message:
        print(f" - {message}")
    else:
        print()


def main():
    print("\n" + "="*60)
    print("Verificación de Configuración - Disitech Project")
    print("="*60 + "\n")

    # Verificar SECRET_KEY
    is_secure_key = not settings.SECRET_KEY.startswith("django-insecure")
    print_status(
        "SECRET_KEY configurada",
        is_secure_key,
        "OK" if is_secure_key else "Cambiar en producción"
    )

    # Verificar DEBUG
    print_status(
        f"DEBUG = {settings.DEBUG}",
        True,
        "Desarrollo" if settings.DEBUG else "Producción"
    )

    # Verificar base de datos
    db_engine = settings.DATABASES['default']['ENGINE']
    is_postgres = 'postgresql' in db_engine
    db_name = settings.DATABASES['default'].get('NAME', 'N/A')
    print_status(
        f"Base de datos: {'PostgreSQL' if is_postgres else 'SQLite'}",
        True,
        str(db_name)
    )

    # Verificar conexión a la base de datos
    try:
        connection.ensure_connection()
        print_status("Conexión a base de datos", True)
    except Exception as e:
        print_status("Conexión a base de datos", False, str(e))

    # Verificar migraciones
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    migrations_needed = len(plan) > 0
    print_status(
        "Migraciones aplicadas",
        not migrations_needed,
        f"{len(plan)} pendientes" if migrations_needed else "OK"
    )

    # Verificar usuarios
    User = get_user_model()
    user_count = User.objects.count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    print_status(
        f"Usuarios: {user_count} total, {superuser_count} superusuarios",
        user_count > 0
    )

    # Verificar Bunny Storage
    bunny_enabled = getattr(settings, 'USE_BUNNY_STORAGE', False)
    if bunny_enabled:
        has_key = bool(getattr(settings, 'BUNNY_STORAGE_ACCESS_KEY', ''))
        has_zone = bool(getattr(settings, 'BUNNY_STORAGE_ZONE', ''))
        has_hostname = bool(getattr(settings, 'BUNNY_HOSTNAME', ''))
        bunny_ok = has_key and has_zone and has_hostname
        print_status(
            "Bunny Storage",
            bunny_ok,
            "Configurado" if bunny_ok else "Credenciales incompletas"
        )
    else:
        print_status("Bunny Storage", True, "Deshabilitado (usando almacenamiento local)")

    # Verificar directorios
    media_dir = getattr(settings, 'MEDIA_ROOT', None)
    if media_dir:
        media_exists = os.path.exists(media_dir)
        print_status(
            f"Directorio media",
            media_exists,
            str(media_dir)
        )

    static_dir = getattr(settings, 'STATIC_ROOT', None)
    if static_dir:
        static_exists = os.path.exists(static_dir)
        print_status(
            f"Directorio static",
            True,
            str(static_dir)
        )

    # Verificar configuración de email
    email_backend = settings.EMAIL_BACKEND
    is_console = 'console' in email_backend
    print_status(
        "Email",
        True,
        "Console (dev)" if is_console else "SMTP (producción)"
    )

    print("\n" + "="*60)
    
    # Recomendaciones
    print("\n📋 Recomendaciones:\n")
    
    if not is_secure_key and not settings.DEBUG:
        print("⚠️  Genera un SECRET_KEY seguro para producción")
    
    if migrations_needed:
        print("⚠️  Ejecuta: python manage.py migrate")
    
    if user_count == 0:
        print("⚠️  Ejecuta: python manage.py ensure_superuser")
    
    if settings.DEBUG:
        print("⚠️  Desactiva DEBUG en producción")
    
    print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        sys.exit(1)
