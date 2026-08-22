from django.db import models

class StokRetail(models.Model):
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE, related_name='stok')
    produk = models.ForeignKey('master.Produk', on_delete=models.CASCADE)
    qty = models.IntegerField(default=0)
    harga_jual = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('cabang', 'produk')
        db_table = 'retail_stok'