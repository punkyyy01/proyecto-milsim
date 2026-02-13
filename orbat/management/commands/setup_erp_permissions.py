from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from orbat.models import Compania, Curso, Escuadra, Miembro, Peloton, Regimiento


class Command(BaseCommand):
    help = "Crea/actualiza grupos de permisos del ERP ORBAT y asigna CREADOR a Emi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--emi-username",
            default="Emi",
            help="Nombre de usuario a asignar al grupo CREADOR_ERP (por defecto: Emi)",
        )
        parser.add_argument(
            "--assign",
            action="append",
            default=[],
            help=(
                "Asignación masiva en formato GRUPO:usuario1,usuario2. "
                "Ejemplo: --assign OFICIAL_ERP:juan,maria"
            ),
        )

    def handle(self, *args, **options):
        emi_username = options["emi_username"]
        assign_specs = options["assign"]

        model_content_types = ContentType.objects.get_for_models(
            Regimiento, Compania, Peloton, Escuadra, Miembro, Curso
        )
        model_names = {ct.model for ct in model_content_types.values()}

        all_orbat_permissions = Permission.objects.filter(content_type__app_label="orbat")

        def perms_for_actions(actions):
            codenames = []
            for model_name in model_names:
                for action in actions:
                    codenames.append(f"{action}_{model_name}")
            return Permission.objects.filter(codename__in=codenames)

        group_matrix = {
            "CREADOR_ERP": Permission.objects.all(),
            "ALTO_MANDO_ERP": all_orbat_permissions,
            "OFICIAL_ERP": perms_for_actions(["view", "add", "change"]),
            "SARGENTO_ERP": Permission.objects.filter(
                codename__in=[
                    "view_regimiento",
                    "view_compania",
                    "view_peloton",
                    "view_escuadra",
                    "view_miembro",
                    "add_miembro",
                    "change_miembro",
                    "view_curso",
                ]
            ),
            "CONSULTA_ERP": perms_for_actions(["view"]),
        }

        for group_name, permissions in group_matrix.items():
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.set(permissions)
            status = "creado" if created else "actualizado"
            self.stdout.write(self.style.SUCCESS(f"Grupo {group_name}: {status}"))

        User = get_user_model()
        groups_by_name = {group.name: group for group in Group.objects.filter(name__in=group_matrix.keys())}

        def assign_user_to_group(username, group_name):
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                self.stdout.write(
                    self.style.WARNING(
                        f"No se encontró el usuario '{username}'. Se omitió asignación a {group_name}."
                    )
                )
                return

            group = groups_by_name.get(group_name)
            if not group:
                self.stdout.write(self.style.WARNING(f"Grupo desconocido '{group_name}'. Se omite."))
                return

            user.groups.add(group)
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])

            self.stdout.write(
                self.style.SUCCESS(f"Usuario {user.username} asignado a {group_name} correctamente.")
            )

        emi_user = User.objects.filter(username__iexact=emi_username).first()

        if not emi_user:
            self.stdout.write(
                self.style.WARNING(
                    f"No se encontró el usuario '{emi_username}'. Se omitió la asignación del grupo CREADOR_ERP."
                )
            )
        else:
            assign_user_to_group(emi_user.username, "CREADOR_ERP")

        for spec in assign_specs:
            if ":" not in spec:
                self.stdout.write(
                    self.style.WARNING(
                        f"Formato inválido en --assign '{spec}'. Usa GRUPO:usuario1,usuario2"
                    )
                )
                continue

            group_name, raw_users = spec.split(":", 1)
            group_name = group_name.strip().upper()
            usernames = [u.strip() for u in raw_users.split(",") if u.strip()]

            if not usernames:
                self.stdout.write(self.style.WARNING(f"Sin usuarios para '{group_name}'. Se omite."))
                continue

            for username in usernames:
                assign_user_to_group(username, group_name)

