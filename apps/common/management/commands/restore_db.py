import json
from io import StringIO
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


DEFAULT_FIXTURE = Path("backup.json")


class Command(BaseCommand):
    help = "Carga el fixture (backup.json) en la base de datos actual."

    def add_arguments(self, parser):
        parser.add_argument(
            "-i", "--input",
            type=str,
            default=None,
            help="Archivo fixture a cargar. Por defecto: backup.json",
        )
        parser.add_argument(
            "--run-migrations",
            action="store_true",
            help="Ejecutar migrate antes de cargar el fixture.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Borrar todos los datos antes de cargar (excepto usuarios).",
        )

    def handle(self, *args, **options):
        fixture = Path(options["input"]) if options["input"] else DEFAULT_FIXTURE

        if not fixture.exists():
            self.stderr.write(self.style.ERROR(f"No se encontró el archivo: {fixture}"))
            raise SystemExit(1)

        content = fixture.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            self.stderr.write(self.style.ERROR(f"Fixture inválido (JSON corrupto): {exc}"))
            raise SystemExit(1)

        if not isinstance(data, list) or len(data) == 0:
            self.stderr.write(self.style.ERROR("Fixture vacío — nada que cargar."))
            raise SystemExit(1)

        if options["run_migrations"]:
            self.stdout.write("Ejecutando migraciones …")
            call_command("migrate", verbosity=1)

        if options["flush"]:
            self.stdout.write("Borrando datos existentes (excepto usuarios) …")
            # No usar flush completo para preservar usuarios
            self._flush_except_users()

        self.stdout.write(f"Cargando {len(data)} objetos desde {fixture} …")
        call_command("loaddata", str(fixture), verbosity=1)

        # Resetear secuencias de PostgreSQL
        self._reset_sequences()

        self.stdout.write(self.style.SUCCESS(f"✔ Restore completado ({len(data)} objetos)"))

    def _flush_except_users(self):
        """Borra todos los datos excepto usuarios, grupos y permisos."""
        # Obtener todos los modelos excepto los de auth
        excluded_apps = ['auth', 'contenttypes', 'sessions', 'admin']
        
        for app_config in apps.get_app_configs():
            if app_config.label in excluded_apps:
                continue
            
            for model in app_config.get_models():
                model_name = f"{app_config.label}.{model._meta.model_name}"
                try:
                    count = model.objects.count()
                    if count > 0:
                        model.objects.all().delete()
                        self.stdout.write(f"  Eliminados {count} objetos de {model_name}")
                except Exception as exc:
                    self.stderr.write(
                        self.style.WARNING(f"  Error al eliminar {model_name}: {exc}")
                    )

    def _reset_sequences(self):
        """Resetea las secuencias de PostgreSQL para evitar conflictos de IDs."""
        if connection.vendor != "postgresql":
            return

        self.stdout.write("Reseteando secuencias de PostgreSQL …")
        app_labels = [config.label for config in apps.get_app_configs()]

        for app_label in app_labels:
            output = StringIO()
            try:
                call_command("sqlsequencereset", app_label, stdout=output, no_color=True)
            except Exception:
                continue

            sql = output.getvalue().strip()
            if sql:
                with connection.cursor() as cursor:
                    cursor.execute(sql)

        self.stdout.write(self.style.SUCCESS("✔ Secuencias reseteadas"))
