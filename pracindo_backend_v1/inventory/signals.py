from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Entitas

from .models import SaldoEntitas


@receiver(post_save, sender=Entitas)
def buat_saldo_entitas(sender, instance, created, **kwargs):
    """
    Baris saldo dibuat bersamaan entitasnya.

    get_or_create di dalam transaksi posting tidak mengunci di jalur
    create -- dua posting bersamaan untuk entitas baru lolos
    berdampingan. Membuatnya di sini menghilangkan jalur itu sepenuhnya.
    """
    if created:
        SaldoEntitas.objects.get_or_create(entitas=instance)