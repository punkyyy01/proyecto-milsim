from django.contrib.admin.models import LogEntry
from django.core.exceptions import PermissionDenied
from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete, sender=LogEntry)
def prevent_logentry_delete(sender, instance, **kwargs):
    raise PermissionDenied("Los logs de auditoría no se pueden eliminar.")
