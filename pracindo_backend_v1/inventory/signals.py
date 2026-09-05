from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone

from core.models import Entitas
from .models import SaldoEntitas, Packing, StatusDokumen


@receiver(post_save, sender=Entitas)
def buat_saldo_entitas(sender, instance, created, **kwargs):
    if created:
        SaldoEntitas.objects.get_or_create(entitas=instance)


@receiver(post_save, sender=Packing)
def eksekusi_posting_packing(sender, instance, created, **kwargs):
    if instance.status == StatusDokumen.POSTED and instance.posted_at is None:
        from warehouse.models import StokBarangJadi
        
        with transaction.atomic():
            stok_jadi, is_new = StokBarangJadi.objects.get_or_create(
                entitas=instance.entitas,
                item=instance.nama_hasil,
                grup_bahan=instance.entitas.grup_bahan, # <-- DIPERBAIKI DI SINI
                kemasan=instance.kemasan.id,
                defaults={
                    'qty_unit': 0, 
                    'qty_kg': Decimal("0")
                }
            )
            
            stok_jadi.qty_unit += instance.total_unit
            stok_jadi.qty_kg += instance.qty_kg
            stok_jadi.save()

            instance.batch.sisa_stok -= instance.qty_kg
            if instance.menghabiskan:
                instance.batch.sisa_stok = Decimal("0")
            instance.batch.save()

            Packing.objects.filter(id=instance.id).update(posted_at=timezone.now())


@receiver(post_delete, sender=Packing)
def rollback_stok_packing_terhapus(sender, instance, **kwargs):
    if instance.status == StatusDokumen.POSTED and instance.posted_at is not None:
        from warehouse.models import StokBarangJadi
        
        with transaction.atomic():
            instance.batch.sisa_stok += instance.qty_kg
            instance.batch.save()

            try:
                stok_jadi = StokBarangJadi.objects.get(
                    entitas=instance.entitas,
                    item=instance.nama_hasil,
                    grup_bahan=instance.entitas.grup_bahan, # <-- DIPERBAIKI DI SINI
                    kemasan=instance.kemasan.id
                )
                
                stok_jadi.qty_unit -= instance.total_unit
                stok_jadi.qty_kg -= instance.qty_kg
                
                if stok_jadi.qty_unit < 0: 
                    stok_jadi.qty_unit = 0
                if stok_jadi.qty_kg < 0: 
                    stok_jadi.qty_kg = Decimal("0")
                
                stok_jadi.save()
            except StokBarangJadi.DoesNotExist:
                pass