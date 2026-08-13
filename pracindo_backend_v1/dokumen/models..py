"""
Lampiran generik — surat jalan, faktur scan, bukti transfer, foto barang.

Append-only. Dokumen yang salah tidak dihapus tapi ditandai
`digantikan_oleh`, supaya jejak audit tetap utuh.

GenericForeignKey dipakai supaya satu tabel melayani semua modul tanpa
dokumen/ perlu tahu app mana saja yang memakainya -- syarat agar app ini
tetap berada di lapis 2.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import DiauditModel


class JenisLampiran(models.TextChoices):
    SURAT_JALAN   = 'SURAT_JALAN',   'Surat jalan'
    FAKTUR        = 'FAKTUR',        'Faktur suplier'
    BUKTI_BAYAR   = 'BUKTI_BAYAR',   'Bukti transfer'
    FOTO_BARANG   = 'FOTO_BARANG',   'Foto barang'
    KONTRAK       = 'KONTRAK',       'Kontrak / perjanjian'
    LAIN          = 'LAIN',          'Lain-lain'


def path_lampiran(instance, filename):
    # dibuat_pada masih None saat upload_to dipanggil pertama kali,
    # jadi pakai jam server -- bukan field yang belum terisi.
    return f"lampiran/{timezone.now():%Y/%m}/{filename}"


class Lampiran(DiauditModel):
    jenis = models.CharField(max_length=16, choices=JenisLampiran.choices, db_index=True)
    berkas = models.FileField(upload_to=path_lampiran)

    nama_asli    = models.CharField(max_length=255, blank=True)
    ukuran_byte  = models.PositiveIntegerField(default=0, editable=False)
    keterangan   = models.CharField(max_length=255, blank=True)

    # Objek pemilik: PenerimaanBarang, FakturPembelian, Pembayaran, dst.
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.PROTECT,
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    pemilik   = GenericForeignKey('content_type', 'object_id')

    # Koreksi tanpa menghapus.
    digantikan_oleh = models.OneToOneField(
        'self', null=True, blank=True, on_delete=models.PROTECT,
        related_name='menggantikan',
    )

    class Meta:
        db_table = 'dokumen_lampiran'
        ordering = ['-dibuat_pada']
        verbose_name_plural = 'Lampiran'
        indexes = [
            models.Index(fields=['content_type', 'object_id'], name='ix_lampiran_pemilik'),
            models.Index(fields=['jenis', '-dibuat_pada'], name='ix_lampiran_jenis'),
        ]

    def __str__(self):
        return f"{self.get_jenis_display()} - {self.nama_asli or self.berkas.name}"

    @property
    def masih_berlaku(self):
        return self.digantikan_oleh_id is None

    def save(self, *args, **kwargs):
        if self.berkas and not self.nama_asli:
            self.nama_asli = self.berkas.name
        if self.berkas and not self.ukuran_byte:
            try:
                self.ukuran_byte = self.berkas.size
            except (OSError, ValueError):
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Lampiran append-only. Unggah pengganti lalu isi digantikan_oleh.'
        )
