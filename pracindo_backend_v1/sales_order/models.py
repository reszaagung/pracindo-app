from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

# Import base model dari core (sesuai standar Anda)
from core.models import TimeStampedModel

# Import relasi dari aplikasi master
from master.models import Pelanggan, Produk

# Import fungsi utilitas (asumsi Anda meletakkannya di master/utils.py atau core/utils.py)
from master.utils import generate_kode_urut


class StatusSO(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    DISETUJUI = 'DISETUJUI', 'Disetujui'
    SELESAI = 'SELESAI', 'Selesai'
    BATAL = 'BATAL', 'Batal'


class SalesOrder(TimeStampedModel):
    # Menggunakan field_name 'nomor_so' agar lebih kontekstual untuk dokumen
    nomor_so = models.CharField(max_length=24, unique=True, blank=True)
    tanggal = models.DateField()
    
    # Relasi ke Pelanggan di modul master
    pelanggan = models.ForeignKey(
        Pelanggan, 
        on_delete=models.PROTECT, 
        related_name='sales_orders'
    )
    
    catatan = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=15, 
        choices=StatusSO.choices, 
        default=StatusSO.DRAFT, 
        db_index=True
    )
    
    # Kalkulasi Finansial (Denormalisasi untuk kecepatan query laporan)
    ppn_persen = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0')
    )
    subtotal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0')
    )
    ppn_nominal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0')
    )
    grand_total = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0')
    )

    class Meta:
        db_table = 'tx_sales_order'
        ordering = ['-tanggal', '-nomor_so']
        verbose_name_plural = 'Sales Order'

    def __str__(self):
        return f"{self.nomor_so} - {self.pelanggan.nama}"

    def save(self, *args, **kwargs):
        # Generate nomor otomatis jika masih kosong
        if not self.nomor_so:
            # Karena di utils Anda defaultnya mencari field 'kode', kita override ke 'nomor_so'
            self.nomor_so = generate_kode_urut(
                SalesOrder, 
                prefix='SO', 
                field_name='nomor_so', 
                padding=4
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Proteksi: Dokumen yang sudah disetujui/berjalan tidak boleh dihapus
        if self.status != StatusSO.DRAFT:
            raise ValidationError('Hanya Sales Order berstatus DRAFT yang boleh dihapus.')
        super().delete(*args, **kwargs)


class SalesOrderItem(TimeStampedModel):
    # Relasi balik ke Header SO (CASCADE: Jika SO dihapus, item ikut terhapus)
    sales_order = models.ForeignKey(
        SalesOrder, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    
    # Relasi ke Produk di modul master
    produk = models.ForeignKey(
        Produk, 
        on_delete=models.PROTECT, 
        related_name='so_items'
    )
    
    qty = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    harga_jual = models.DecimalField(
        max_digits=18, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    subtotal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0')
    )

    class Meta:
        db_table = 'tx_sales_order_item'
        ordering = ['id']
        verbose_name_plural = 'Sales Order Items'

    def __str__(self):
        return f"{self.sales_order.nomor_so} - {self.produk.nama}"

    def save(self, *args, **kwargs):
        # Otomatis menghitung subtotal baris setiap kali disimpan
        if self.qty and self.harga_jual:
            self.subtotal = self.qty * self.harga_jual
        super().save(*args, **kwargs)