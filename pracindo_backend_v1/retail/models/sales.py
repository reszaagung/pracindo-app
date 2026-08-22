from django.db import models
from django.utils import timezone

class SalesRetail(models.Model):
    nama = models.CharField(max_length=150)
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE, related_name='sales')
    persentase_bonus = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'retail_sales'

    def __str__(self):
        return self.nama

class BonusSales(models.Model):
    sales = models.ForeignKey(SalesRetail, on_delete=models.CASCADE, related_name='bonus')
    transaksi = models.OneToOneField('retail.TransaksiPOS', on_delete=models.CASCADE, related_name='data_bonus')
    tanggal = models.DateField(default=timezone.now)
    nominal_bonus = models.DecimalField(max_digits=12, decimal_places=2)
    status_pencairan = models.CharField(max_length=20, choices=[('BELUM CAIR', 'BELUM CAIR'), ('CAIR', 'CAIR')], default='BELUM CAIR')

    class Meta:
        db_table = 'retail_bonus_sales'