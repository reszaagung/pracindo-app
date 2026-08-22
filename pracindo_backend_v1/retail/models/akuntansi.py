from django.db import models
from django.utils import timezone

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
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE, null=True, blank=True)
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
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE)

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