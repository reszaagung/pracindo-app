import uuid
from django.db import models
from django.utils import timezone

class LaporanSelisih(models.Model):
    JENIS_CHOICES = [
        ('KURANG_KIRIM', 'Kurang Kirim (Selisih Timbang)'),
        ('BARANG_RUSAK', 'Barang Rusak / Ditolak'),
        ('LAINNYA', 'Lainnya')
    ]
    STATUS_CHOICES = [
        ('DIBUKA', 'Dibuka'),
        ('DIAJUKAN', 'Diajukan ke Suplier'),
        ('DISEPAKATI', 'Disepakati'),
        ('DISELESAIKAN', 'Diselesaikan'),
        ('DITUTUP', 'Ditutup')
    ]
    nomor = models.CharField(max_length=50, unique=True, blank=True)
    tanggal = models.DateTimeField(default=timezone.now)
    
    jenis = models.CharField(max_length=20, choices=JENIS_CHOICES, default='KURANG_KIRIM')
    qty_selisih = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DIBUKA')
    catatan_klaim = models.TextField(blank=True, null=True)
    resolusi = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'retail_laporan_selisih'
        ordering = ['-tanggal']

    def save(self, *args, **kwargs):
        if not self.nomor:
            self.nomor = f"LS-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nomor