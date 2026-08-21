from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


class CabangToko(models.Model):
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    alamat = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class StokRetail(models.Model):
    cabang = models.ForeignKey(CabangToko, on_delete=models.CASCADE, related_name='stok')
    produk = models.ForeignKey('master.Produk', on_delete=models.CASCADE)
    qty = models.IntegerField(default=0)
    harga_jual = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('cabang', 'produk')
        db_table = 'retail_stok'


class SesiKasir(models.Model):
    cabang = models.ForeignKey(CabangToko, on_delete=models.CASCADE)
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
    waktu_transaksi = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    pajak = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    metode_bayar = models.CharField(
        max_length=20, 
        choices=[('TUNAI', 'TUNAI'), ('QRIS', 'QRIS'), ('TRANSFER', 'TRANSFER')]
    )
    status = models.CharField(max_length=20, choices=[('BERHASIL', 'BERHASIL'), ('RETUR', 'RETUR')], default='BERHASIL')


class ItemTransaksi(models.Model):
    transaksi = models.ForeignKey(TransaksiPOS, on_delete=models.CASCADE, related_name='items')
    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT)
    qty = models.IntegerField()
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


class BukuHutangRetail(models.Model):
    STATUS_CHOICES = [
        ('BELUM LUNAS', 'BELUM LUNAS'),
        ('MENCICIL', 'MENCICIL'),
        ('LUNAS', 'LUNAS')
    ]

    cabang = models.ForeignKey(CabangToko, on_delete=models.PROTECT, related_name='daftar_hutang')
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


class KategoriAkun(models.Model):
    nama = models.CharField(max_length=50, unique=True)
    tipe_saldo = models.CharField(max_length=10, choices=[('DEBIT', 'DEBIT'), ('KREDIT', 'KREDIT')])

    class Meta:
        db_table = 'retail_kategori_akun'

    def __str__(self):
        return self.nama


class AkunBukuBesar(models.Model):
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    kategori = models.ForeignKey(KategoriAkun, on_delete=models.PROTECT)
    cabang = models.ForeignKey(CabangToko, on_delete=models.CASCADE, null=True, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'retail_akun_buku_besar'

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class TransaksiJurnal(models.Model):
    nomor_jurnal = models.CharField(max_length=50, unique=True)
    tanggal = models.DateTimeField(default=timezone.now)
    referensi = models.CharField(max_length=100)
    keterangan = models.TextField()
    cabang = models.ForeignKey(CabangToko, on_delete=models.CASCADE)

    class Meta:
        db_table = 'retail_transaksi_jurnal'
        ordering = ['-tanggal', '-id']

    def __str__(self):
        return self.nomor_jurnal


class DetailJurnal(models.Model):
    jurnal = models.ForeignKey(TransaksiJurnal, on_delete=models.CASCADE, related_name='item_jurnal')
    akun = models.ForeignKey(AkunBukuBesar, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'retail_detail_jurnal'