import json
import shutil
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


EXCLUDE = [
    "contenttypes",
    "auth.permission",
    "sessions",
    "admin.logentry",
]

BACKUP_DIR = Path("backups")
BACKUP_FILE = Path("backup.json")


class Command(BaseCommand):
    help = "Genera un backup seguro de la base de datos (JSON fixture)."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o", "--output",
            type=str,
            default=None,
            help="Archivo de salida. Por defecto: backup.json (y copia versionada en backups/).",
        )
        parser.add_argument(
            "--no-version",
            action="store_true",
            help="No guardar copia versionada en backups/.",
        )

    def handle(self, *args, **options):
        output = Path(options["output"]) if options["output"] else BACKUP_FILE
        tmp = output.with_suffix(".tmp")

        self.stdout.write(f"Generando backup en {tmp} …")

        # Dump a archivo temporal (si falla, el original no se pierde)
        call_command(
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--indent", "2",
            *(f"--exclude={e}" for e in EXCLUDE),
            output=str(tmp),
            verbosity=0,
        )

        # Validar que el archivo no esté vacío o sea JSON inválido
        content = tmp.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            tmp.unlink(missing_ok=True)
            self.stderr.write(self.style.ERROR(f"Backup inválido (JSON corrupto): {exc}"))
            raise SystemExit(1)

        if not isinstance(data, list) or len(data) == 0:
            tmp.unlink(missing_ok=True)
            self.stderr.write(self.style.ERROR("Backup vacío — no se sobrescribió el anterior."))
            raise SystemExit(1)

        # Mover temporal → destino
        shutil.move(str(tmp), str(output))
        self.stdout.write(self.style.SUCCESS(
            f"✔ {output}  ({len(data)} objetos)"
        ))

        # Copia versionada
        if not options["no_version"]:
            BACKUP_DIR.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            versioned = BACKUP_DIR / f"backup_{stamp}.json"
            shutil.copy2(str(output), str(versioned))
            self.stdout.write(f"  Copia versionada: {versioned}")
