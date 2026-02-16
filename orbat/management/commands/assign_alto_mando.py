"""
Management command: assign_alto_mando
=================================
Quita `is_superuser` a todos los usuarios excepto al usuario con
`username == 'Emi'` y añade esos usuarios al grupo `ALTO_MANDO_ERP`.

Uso:
  python manage.py assign_alto_mando        # pide confirmación interactiva
  python manage.py assign_alto_mando --yes  # aplica sin pedir confirmación

Este comando es idempotente: puede ejecutarse varias veces.
"""

from typing import Tuple

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Quita is_superuser a todos los usuarios excepto 'Emi' y los añade al grupo ALTO_MANDO_ERP."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            dest="yes",
            help="Aplicar cambios sin pedir confirmación",
        )

    def _perform(self) -> Tuple[int, int, int]:
        """Realiza la operación y devuelve (total, changed, already)."""
        try:
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import Group
        except Exception as exc:
            raise CommandError(f"Error cargando modelos de auth: {exc}")

        User = get_user_model()

        group, _created = Group.objects.get_or_create(name="ALTO_MANDO_ERP")

        qs = User.objects.exclude(username="Emi")
        total = qs.count()
        changed = 0
        already = 0

        for user in qs:
            modified = False

            if user.is_superuser:
                user.is_superuser = False
                modified = True

            if not user.groups.filter(pk=group.pk).exists():
                user.groups.add(group)
                # Adding to group does not mark `user` as dirty for save(),
                # but we consider this a change to report.
                modified = True

            if modified:
                user.save()
                changed += 1
            else:
                already += 1

        return total, changed, already

    def handle(self, *args, **options):
        yes = options.get("yes")

        self.stdout.write(self.style.WARNING("Operación: quitar superusuario y añadir al grupo ALTO_MANDO_ERP"))

        try:
            from django.contrib.auth import get_user_model
        except Exception as exc:
            raise CommandError(f"Error cargando User model: {exc}")

        User = get_user_model()
        total_users = User.objects.exclude(username="Emi").count()

        if total_users == 0:
            self.stdout.write("No hay usuarios (excluyendo 'Emi') sobre los cuales operar.")
            return

        self.stdout.write(f"Usuarios a afectar (excluyendo 'Emi'): {total_users}")

        if not yes:
            confirm = input("¿Continuar y aplicar los cambios? [y/N]: ")
            if confirm.lower() not in ("y", "yes"):
                self.stdout.write("Operación cancelada por el usuario.")
                return

        total, changed, already = self._perform()

        self.stdout.write(self.style.SUCCESS(f"Total usuarios evaluados: {total}"))
        self.stdout.write(self.style.SUCCESS(f"Usuarios modificados: {changed}"))
        self.stdout.write(self.style.SUCCESS(f"Usuarios ya en estado esperado: {already}"))
