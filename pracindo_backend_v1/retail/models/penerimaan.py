from django.db import models
from django.utils import timezone

class SuratJalan(models.Model):
    nomor_do = models.CharField(max_length=50, unique=True)
    cabang = models.ForeignKey('retail.CabangToko', on_delete=models.CASCADE, related_name='penerimaan_do')
    asal_pengiriman = models.CharField(max_length=150, default='Gudang Utama Pracindo')
    tanggal_kirim = models.DateTimeField(default=timezone.now)
    tanggal_terima = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[('MENUNGGU', 'MENUNGGU'), ('SELESAI', 'SELESAI')], 
        default='MENUNGGU'
    )
    pengirim = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'retail_surat_jalan'
        ordering = ['-tanggal_kirim']

    def __str__(self):
        return f"{self.nomor_do} - {self.cabang.nama}"