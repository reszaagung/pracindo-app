from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

class BukuPiutangRetail(models.Model):
    STATUS_CHOICES = [
        ('BELUM LUNAS', 'BELUM LUNAS'),
        ('MENCICIL', 'MENCICIL'),
        ('LUNAS', 'LUNAS')
    ]

    pelanggan = models.ForeignKey('retail.PelangganRetail', on_delete=models.PROTECT, related_name='daftar_piutang')
    transaksi = models.OneToOneField('retail.TransaksiPOS', on_delete=models.CASCADE, related_name='data_piutang')
    tanggal_piutang = models.DateField(default=timezone.now)
    jatuh_tempo = models.DateField()
    total_piutang = models.DecimalField(max_digits=15, decimal_places=2)
    total_dibayar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BELUM LUNAS')

    class Meta:
        db_table = 'retail_buku_piutang'
        ordering = ['-tanggal_piutang']

    @property
    def sisa_piutang(self):
        return self.total_piutang - self.total_dibayar

    @property
    def umur_piutang_hari(self):
        return (timezone.now().date() - self.tanggal_piutang).days

    @property
    def sisa_hari_jatuh_tempo(self):
        return (self.jatuh_tempo - timezone.now().date()).days

    def save(self, *args, **kwargs):
        if self.total_dibayar >= self.total_piutang and self.total_piutang > 0:
            self.status = 'LUNAS'
        elif self.total_dibayar > 0:
            self.status = 'MENCICIL'
        else:
            self.status = 'BELUM LUNAS'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pelanggan.nama} - {self.transaksi.nomor_struk}"

class RiwayatBayarPiutang(models.Model):
    piutang = models.ForeignKey(BukuPiutangRetail, on_delete=models.CASCADE, related_name='riwayat_bayar')
    tanggal_bayar = models.DateField(default=timezone.now)
    nominal = models.DecimalField(max_digits=15, decimal_places=2)
    metode_bayar = models.CharField(max_length=50)

    class Meta:
        db_table = 'retail_riwayat_bayar_piutang'

@receiver([post_save, post_delete], sender=RiwayatBayarPiutang)
def update_saldo_buku_piutang(sender, instance, **kwargs):
    piutang_induk = instance.piutang
    total = piutang_induk.riwayat_bayar.aggregate(Sum('nominal'))['nominal__sum'] or 0
    piutang_induk.total_dibayar = total
    piutang_induk.save()