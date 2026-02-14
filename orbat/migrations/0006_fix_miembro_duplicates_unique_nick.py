"""
Migración para:
1. Fusionar miembros duplicados (mismo nombre_milsim) conservando el más completo.
2. Aplicar unique=True sobre nombre_milsim para evitar futuros duplicados.
"""

from django.db import migrations, models


def merge_duplicate_miembros(apps, schema_editor):
    """Fusiona duplicados de nombre_milsim manteniendo el registro más completo."""
    Miembro = apps.get_model('orbat', 'Miembro')

    # Buscar nombres duplicados
    from django.db.models import Count
    duplicados = (
        Miembro.objects.values('nombre_milsim')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
    )

    for dup in duplicados:
        nick = dup['nombre_milsim']
        miembros = list(Miembro.objects.filter(nombre_milsim=nick).order_by('id'))

        # El primero será el "principal" (el original)
        principal = miembros[0]

        for duplicado in miembros[1:]:
            # Transferir asignaciones de unidad que el principal no tenga
            if not principal.regimiento_id and duplicado.regimiento_id:
                principal.regimiento_id = duplicado.regimiento_id
            if not principal.compania_id and duplicado.compania_id:
                principal.compania_id = duplicado.compania_id
            if not principal.peloton_id and duplicado.peloton_id:
                principal.peloton_id = duplicado.peloton_id
            if not principal.escuadra_id and duplicado.escuadra_id:
                principal.escuadra_id = duplicado.escuadra_id

            # Transferir datos vacíos
            if not principal.usuario_id and duplicado.usuario_id:
                principal.usuario_id = duplicado.usuario_id
            if not principal.discord_id and duplicado.discord_id:
                principal.discord_id = duplicado.discord_id
            if not principal.steam_id and duplicado.steam_id:
                principal.steam_id = duplicado.steam_id
            if not principal.notas_admin and duplicado.notas_admin:
                principal.notas_admin = duplicado.notas_admin

            # Transferir cursos del duplicado al principal
            for curso in duplicado.cursos.all():
                principal.cursos.add(curso)

            # Conservar el rango más alto (menor posición en choices = más alto)
            # Si el duplicado está activo, mantener activo
            if duplicado.activo:
                principal.activo = True

            # Eliminar el duplicado
            duplicado.delete()

        # Asegurar que solo quede UNA asignación jerárquica (la más específica)
        if principal.escuadra_id:
            principal.peloton_id = None
            principal.compania_id = None
            principal.regimiento_id = None
        elif principal.peloton_id:
            principal.compania_id = None
            principal.regimiento_id = None
        elif principal.compania_id:
            principal.regimiento_id = None

        principal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('orbat', '0005_update_rango_choices_and_data'),
    ]

    operations = [
        # Paso 1: Fusionar duplicados
        migrations.RunPython(merge_duplicate_miembros, migrations.RunPython.noop),
        # Paso 2: Aplicar restricción unique
        migrations.AlterField(
            model_name='miembro',
            name='nombre_milsim',
            field=models.CharField(max_length=100, unique=True, verbose_name='Nick'),
        ),
    ]
