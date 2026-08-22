from django.db import models
from django.conf import settings

class SesiKasir(models.Model):
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE)
    kasir = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    waktu_buka = models.DateTimeField(auto_now_add=True)
    waktu_tutup = models.DateTimeField(null=True, blank=True)
    saldo_awal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_penjualan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, 
        choices=[('AKTIF', 'AKTIF'), ('DITUTUP', 'DITUTUP')],
        default='AKTIF'
    )

class TransaksiPOS(models.Model):
    nomor_struk = models.CharField(max_length=50, unique=True)
    sesi = models.ForeignKey(SesiKasir, on_delete=models.PROTECT, related_name='transaksi')
    pelanggan = models.ForeignKey('retail.PelangganRetail', on_delete=models.SET_NULL, null=True, blank=True)
    sales = models.ForeignKey('retail.SalesRetail', on_delete=models.SET_NULL, null=True, blank=True)
    waktu_transaksi = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    pajak = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    metode_bayar = models.CharField(
        max_length=20, 
        choices=[('TUNAI', 'TUNAI'), ('QRIS', 'QRIS'), ('TRANSFER', 'TRANSFER'), ('TEMPO', 'TEMPO')]
    )
    status = models.CharField(max_length=20, choices=[('BERHASIL', 'BERHASIL'), ('RETUR', 'RETUR')], default='BERHASIL')

class ItemTransaksi(models.Model):
    transaksi = models.ForeignKey(TransaksiPOS, on_delete=models.CASCADE, related_name='items')
    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT)
    qty = models.IntegerField()
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)