"""
Master data — katalog yang dirujuk modul lain.

Semua model di sini murni CRUD tanpa business logic. Begitu salah satunya
mulai punya perilaku sendiri (skoring suplier, kontrak harga berjangka),
dia sudah jadi domain dan layak pindah ke app sendiri.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from core.models import TimeStampedModel

from .utils import generate_kode_urut

class MasterProduk(models.Model):
    id = models.CharField(max_length=50,primary_key=True),
    nama_item = models.CharField(max_length=70)
    
    class Meta:
        db_table = 'master_produk_intern'
        ordering = ['nama_item']
        verbose_name_plural = 'Master Items'

    def __str__(self):
        return self.nama_item

class Kategori(TimeStampedModel):
    kode = models.CharField(max_length=16, unique=True, blank=True)
    nama = models.CharField(max_length=120)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'master_kategori'
        ordering = ['kode']
        verbose_name_plural = 'Kategori'

    def __str__(self):
        return f"{self.kode} - {self.nama}"
        
    def save(self, *args, **kwargs):
        if not self.kode:
            self.kode = generate_kode_urut(Kategori, prefix='KAT', padding=3)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Kategori tidak boleh dihapus. Set aktif=False.')


class Satuan(TimeStampedModel):
    kode = models.CharField(max_length=8, unique=True)
    nama = models.CharField(max_length=40)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'master_satuan'
        ordering = ['kode']
        verbose_name_plural = 'Satuan'

    def __str__(self):
        return self.kode

    def delete(self, *args, **kwargs):
        raise ValidationError('Satuan tidak boleh dihapus. Set aktif=False.')


class JenisProduk(models.TextChoices):
    BAHAN_BAKU  = 'BAHAN_BAKU',  'Bahan baku'
    BARANG_JADI = 'BARANG_JADI', 'Barang jadi'
    KEMASAN     = 'KEMASAN',     'Kemasan'
    LAIN        = 'LAIN',        'Lain-lain'


class Suplier(TimeStampedModel):
    kode  = models.CharField(max_length=16, unique=True, blank=True)
    nama  = models.CharField(max_length=200)
    npwp  = models.CharField(max_length=20, blank=True)
    alamat = models.TextField(blank=True)

    kontak_nama = models.CharField(max_length=120, blank=True)
    kontak_hp   = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)

    termin_hari_default = models.PositiveSmallIntegerField(default=0)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'master_suplier'
        ordering = ['nama']
        verbose_name_plural = 'Suplier'

    def __str__(self):
        return self.nama

    @property
    def pkp(self):
        return bool(self.npwp)
        
    def save(self, *args, **kwargs):
        if not self.kode:
            self.kode = generate_kode_urut(Suplier, prefix='SUP', padding=4)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Suplier tidak boleh dihapus. Set aktif=False.')


class Produk(TimeStampedModel):
    kode     = models.CharField(max_length=24, unique=True, blank=True)
    nama     = models.CharField(max_length=200)
    jenis    = models.CharField(max_length=12, choices=JenisProduk.choices, db_index=True)
    kategori = models.ForeignKey(Kategori, null=True, blank=True,
                                 on_delete=models.PROTECT, related_name='produk')
    satuan   = models.ForeignKey(Satuan, on_delete=models.PROTECT, related_name='produk')
    lokasi_simpan = models.CharField(max_length=100, blank=True)
    suplier = models.ManyToManyField(Suplier, blank=True, related_name='produk_disuplai')
    disimpan_di_tanki = models.BooleanField(default=False)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'master_produk'
        ordering = ['kode']
        verbose_name_plural = 'Produk'
        indexes = [models.Index(fields=['jenis', 'aktif'], name='ix_produk_jenis_aktif')]

    def __str__(self):
        return f"{self.kode} - {self.nama}"
        
    def save(self, *args, **kwargs):
        if not self.kode:
            # Bikin prefix dinamis berdasarkan jenis produk
            if self.jenis == JenisProduk.BAHAN_BAKU:
                prefix = 'BP'
            elif self.jenis == JenisProduk.BARANG_JADI:
                prefix = 'BJ'
            elif self.jenis == JenisProduk.KEMASAN:
                prefix = 'KM'
            else:
                prefix = 'PRD'
                
            self.kode = generate_kode_urut(Produk, prefix=prefix, padding=4)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Produk tidak boleh dihapus. Set aktif=False.')


class Pelanggan(TimeStampedModel):
    # Tambahkan blank=True agar lolos validasi serializer
    kode   = models.CharField(max_length=16, unique=True, blank=True)
    nama   = models.CharField(max_length=200)
    npwp   = models.CharField(max_length=20, blank=True)
    alamat = models.TextField(blank=True)

    kontak_nama = models.CharField(max_length=120, blank=True)
    kontak_hp   = models.CharField(max_length=20, blank=True)

    termin_hari_default = models.PositiveSmallIntegerField(default=0)
    plafon_kredit = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'master_pelanggan'
        ordering = ['nama']
        verbose_name_plural = 'Pelanggan'

    def __str__(self):
        return self.nama
        
    def save(self, *args, **kwargs):
        if not self.kode:
            self.kode = generate_kode_urut(Pelanggan, prefix='CUST', padding=4)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Pelanggan tidak boleh dihapus. Set aktif=False.')