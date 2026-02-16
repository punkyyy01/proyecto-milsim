"""
Management command: assign_alto_mando
====================================
Revoca el estado de superusuario a todos los usuarios excepto uno
(ej. "Emi") y los agrega al grupo ALTO_MANDO_ERP.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Quita superusuario a todos los usuarios salvo el excluido y los "
        "agrega al grupo ALTO_MANDO_ERP."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-username",
            default="Emi",
            help="Usuario a excluir (por defecto: Emi)",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Ejecutar sin pedir confirmacion",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar lo que haria, sin cambios",
        )
        parser.add_argument(
            "--use-sqlite",
            action="store_true",
            help="Forzar SQLite local (ignora DATABASE_URL)",
        )

    @staticmethod
    def _force_sqlite():
        """Sobrescribe la configuracion de BD para usar SQLite local."""
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

        conn = connections["default"]
        conn.close()
        del connections._connections.default

    def handle(self, *args, **options):
        if options.get("use_sqlite"):
            self._force_sqlite()

        exclude_username = options["exclude_username"]
        dry_run = options["dry_run"]
        auto_yes = options["yes"]

        group, _ = Group.objects.get_or_create(name="ALTO_MANDO_ERP")
        User = get_user_model()

        qs = User.objects.exclude(username__iexact=exclude_username)
        total = qs.count()
        if total == 0:
            self.stdout.write("No hay usuarios para actualizar.")
            return

        superusers_to_demote = qs.filter(is_superuser=True).count()

        self.stdout.write(
            f"Usuarios a procesar: {total} (superusuarios a revocar: {superusers_to_demote})"
        )
        self.stdout.write(f"Grupo objetivo: {group.name}")

        if dry_run:
            preview = list(qs.values_list("username", flat=True)[:10])
            self.stdout.write("Dry run activado. Ejemplo de usuarios:")
            for name in preview:
                self.stdout.write(f"  - {name}")
            return

        if not auto_yes:
            confirm = input("Esto quitara superusuario y agregara al grupo. Continuar? [y/N]: ")
            if confirm.lower() not in ("y", "yes"):
                self.stdout.write("Operacion cancelada por el usuario.")
                return

        added_to_group = 0
        with transaction.atomic():
            qs.update(is_superuser=False)
            for user in qs.iterator():
                if not user.groups.filter(id=group.id).exists():
                    user.groups.add(group)
                    added_to_group += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Superusuarios revocados: {superusers_to_demote}. "
                f"Agregados a {group.name}: {added_to_group}."
            )
        )
