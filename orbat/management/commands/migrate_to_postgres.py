"""
Management command: migrate_to_postgres
Exporta todos los datos de SQLite y los carga en PostgreSQL.

Uso:
  1. Primero ejecutar para exportar desde SQLite:
     python manage.py migrate_to_postgres --export --use-sqlite

  2. Luego con DATABASE_URL apuntando a PostgreSQL:
     python manage.py migrate_to_postgres --import
"""
import json
import os
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Migra datos de SQLite a PostgreSQL. Usar --export primero, luego --import."

    DUMP_FILE = "db_dump.json"

    # Apps y modelos en orden correcto (respetando FK)
    EXPORT_LABELS = [
        "contenttypes",
        "auth.permission",
        "auth.group",
        "auth.user",
        "admin.logentry",
        "sessions",
        "orbat.regimiento",
        "orbat.compania",
        "orbat.peloton",
        "orbat.escuadra",
        "orbat.curso",
        "orbat.miembro",
    ]

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--export",
            action="store_true",
            help="Exporta los datos de la BD actual (SQLite) a un archivo JSON.",
        )
        group.add_argument(
            "--import",
            action="store_true",
            help="Importa los datos del JSON en la BD actual (PostgreSQL).",
        )
        parser.add_argument(
            "--file",
            type=str,
            default=self.DUMP_FILE,
            help=f"Ruta del archivo JSON (por defecto: {self.DUMP_FILE}).",
        )
        parser.add_argument(
            "--skip-migrate",
            action="store_true",
            help="No ejecutar migrate antes del import.",
        )
        parser.add_argument(
            "--use-sqlite",
            action="store_true",
            help="Fuerza el uso de SQLite (ignora DATABASE_URL). Útil para --export.",
        )

    def handle(self, *args, **options):
        # Si se pide --use-sqlite, forzar SQLite sobreescribiendo la configuración
        if options["use_sqlite"]:
            self._force_sqlite()

        dump_path = Path(options["file"])

        if options["export"]:
            self._export(dump_path)
        elif options["import"]:
            self._import(dump_path, skip_migrate=options["skip_migrate"])

    @staticmethod
    def _force_sqlite():
        """Sobreescribe la configuración de BD para usar SQLite local."""
        from django.conf import settings
        from django.db import connections

        sqlite_config = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": settings.BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "OPTIONS": {},
            "TIME_ZONE": None,
            "TEST": {},
        }

        settings.DATABASES["default"] = sqlite_config

        # Cerrar y eliminar la conexión existente para que Django
        # cree una nueva con la configuración de SQLite
        conn = connections["default"]
        conn.close()
        del connections._connections.default  # noqa: access internal to force re‑init

    def _export(self, dump_path: Path):
        """Exporta toda la base de datos actual a JSON."""
        from django.conf import settings

        engine = settings.DATABASES["default"]["ENGINE"]
        self.stdout.write(f"Exportando desde: {engine}")

        self.stdout.write("Exportando datos...")
        with open(dump_path, "w", encoding="utf-8") as f:
            call_command(
                "dumpdata",
                *self.EXPORT_LABELS,
                "--indent=2",
                "--natural-foreign",
                "--natural-primary",
                stdout=f,
            )

        # Verificar
        with open(dump_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Contar por modelo
        counts = {}
        for obj in data:
            model = obj["model"]
            counts[model] = counts.get(model, 0) + 1

        self.stdout.write(self.style.SUCCESS(f"\nExportados {len(data)} registros a '{dump_path}':"))
        for model, count in sorted(counts.items()):
            self.stdout.write(f"  {model}: {count}")

    def _import(self, dump_path: Path, skip_migrate: bool = False):
        """Importa datos JSON a la BD actual (PostgreSQL)."""
        from django.conf import settings

        engine = settings.DATABASES["default"]["ENGINE"]
        if "sqlite" in engine:
            raise CommandError(
                "¡Estás importando a SQLite! Configura DATABASE_URL "
                "para apuntar a PostgreSQL antes de importar."
            )

        if not dump_path.exists():
            raise CommandError(
                f"No se encontró '{dump_path}'. "
                f"Ejecuta primero: python manage.py migrate_to_postgres --export"
            )

        self.stdout.write(f"Importando a: {engine}")

        # Paso 1: Asegurar que las migraciones están aplicadas
        if not skip_migrate:
            self.stdout.write("Aplicando migraciones en PostgreSQL...")
            call_command("migrate", "--noinput")

        # Paso 2: Limpiar datos existentes (si los hay) para evitar conflictos
        self.stdout.write("Limpiando tablas (flush)...")
        call_command("flush", "--noinput")

        # Paso 3: Cargar datos
        self.stdout.write("Cargando datos...")
        call_command("loaddata", str(dump_path))

        # Paso 4: Verificar conteos
        self._verify_import(dump_path)

        self.stdout.write(self.style.SUCCESS("\n¡Migración completada exitosamente!"))
        self.stdout.write(
            self.style.WARNING(
                "IMPORTANTE: Las contraseñas de los usuarios se preservaron. "
                "Si necesitas resetear alguna, usa: python manage.py changepassword <usuario>"
            )
        )

    def _verify_import(self, dump_path: Path):
        """Verifica que los datos se importaron correctamente."""
        from django.apps import apps

        with open(dump_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Contar por modelo en el dump
        dump_counts = {}
        for obj in data:
            model = obj["model"]
            dump_counts[model] = dump_counts.get(model, 0) + 1

        self.stdout.write("\nVerificación de importación:")
        all_ok = True
        for model_label, expected in sorted(dump_counts.items()):
            try:
                app_label, model_name = model_label.split(".")
                Model = apps.get_model(app_label, model_name)
                actual = Model.objects.count()
                if actual == expected:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {model_label}: {actual}/{expected}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ {model_label}: {actual}/{expected}")
                    )
                    all_ok = False
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {model_label}: error - {e}")
                )
                all_ok = False

        if not all_ok:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ Algunos conteos no coinciden. Revisa los errores arriba."
                )
            )
