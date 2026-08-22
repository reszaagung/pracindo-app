from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

class BukuHutangRetail(models.Model):
    STATUS_CHOICES = [
        ('BELUM LUNAS', 'BELUM LUNAS'),
        ('MENCICIL', 'MENCICIL'),
        ('LUNAS', 'LUNAS')
    ]

    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.PROTECT, related_name='daftar_hutang')
    referensi = models.CharField(max_length=100)
    tanggal_hutang = models.DateField(default=timezone.now)
    jatuh_tempo = models.DateField(blank=True, null=True)
    keterangan = models.TextField(blank=True)
    total_hutang = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_dibayar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BELUM LUNAS')
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'retail_buku_hutang'
        ordering = ['-tanggal_hutang', '-id']

    @property
    def sisa_hutang(self):
        return self.total_hutang - self.total_dibayar

    def save(self, *args, **kwargs):
        if self.total_dibayar >= self.total_hutang and self.total_hutang > 0:
            self.status = 'LUNAS'
        elif self.total_dibayar > 0:
            self.status = 'MENCICIL'
        else:
            self.status = 'BELUM LUNAS'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.referensi} - {self.cabang.nama}"

class RiwayatBayarHutang(models.Model):
    hutang = models.ForeignKey(BukuHutangRetail, on_delete=models.CASCADE, related_name='riwayat_bayar')
    tanggal_bayar = models.DateField(default=timezone.now)
    nominal = models.DecimalField(max_digits=15, decimal_places=2)
    metode_bayar = models.CharField(max_length=50)
    catatan = models.CharField(max_length=255, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'retail_riwayat_bayar'

@receiver([post_save, post_delete], sender=RiwayatBayarHutang)
def update_saldo_buku_hutang(sender, instance, **kwargs):
    hutang_induk = instance.hutang
    total = hutang_induk.riwayat_bayar.aggregate(Sum('nominal'))['nominal__sum'] or 0
    hutang_induk.total_dibayar = total
    hutang_induk.save()