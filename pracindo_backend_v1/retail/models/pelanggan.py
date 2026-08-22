from django.db import models

class PelangganRetail(models.Model):
    nama = models.CharField(max_length=150)
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    limit_piutang = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    default_tempo_hari = models.IntegerField(default=30)
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE, related_name='pelanggan')
    sales = models.ForeignKey('retail.SalesRetail', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'retail_pelanggan'

    def __str__(self):
        return self.nama