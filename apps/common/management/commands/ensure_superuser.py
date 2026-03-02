import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superusuario desde variables de entorno si no existe ningún usuario."

    def handle(self, *args, **options):
        User = get_user_model()

        # Verificar si ya existen usuarios
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING("⚠ Ya existen usuarios en la base de datos. No se creará superusuario.")
            )
            return

        # Obtener credenciales desde variables de entorno
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")

        # Validar que al menos el password esté configurado
        if password == "admin123":
            self.stderr.write(
                self.style.WARNING(
                    "⚠ Usando password por defecto. Configure DJANGO_SUPERUSER_PASSWORD en .env"
                )
            )

        try:
            # Crear superusuario
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Superusuario creado exitosamente: {username}"
                )
            )
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f"Error al crear superusuario: {exc}")
            )
            raise SystemExit(1)
