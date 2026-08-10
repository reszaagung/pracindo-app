"""
Jejak aktivitas — audit/models.py

APA YANG DICATAT DI SINI, DAN APA YANG TIDAK

Sistem sudah punya beberapa lapis jejak sebelum app ini:

    DiauditModel.dibuat_oleh   siapa membuat dokumen
    JurnalUmum                 setiap kejadian ekonomi
    MutasiStok, MutasiKlaim    setiap gerak barang dan hak
    RiwayatAkses               login berhasil dan gagal

Yang TIDAK tercatat di mana pun: perubahan status yang tidak
menghasilkan jurnal. PO dikirim, PO dibatalkan, laporan selisih
diselesaikan, periode ditutup, role pengguna diubah.

Justru itu yang paling sering ditanyakan saat ada masalah: siapa yang
membatalkan PO ini, kapan, dan kenapa.

APPEND-ONLY. Tidak pernah di-update maupun di-delete. Jejak audit yang
bisa disunting tidak ada gunanya.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class JenisAksi(models.TextChoices):
    BUAT      = 'BUAT',      'Dibuat'
    UBAH      = 'UBAH',      'Diubah'
    KIRIM     = 'KIRIM',     'Dikirim'
    BATAL     = 'BATAL',     'Dibatalkan'
    SETUJU    = 'SETUJU',    'Disetujui'
    TOLAK     = 'TOLAK',     'Ditolak'
    SELESAI   = 'SELESAI',   'Diselesaikan'
    TUTUP     = 'TUTUP',     'Ditutup'
    BUKA      = 'BUKA',      'Dibuka kembali'
    NONAKTIF  = 'NONAKTIF',  'Dinonaktifkan'
    AKTIF     = 'AKTIF',     'Diaktifkan'
    UBAH_ROLE = 'UBAH_ROLE', 'Peran diubah'
    RESET_PWD = 'RESET_PWD', 'Password direset'


class JejakAktivitas(models.Model):
    """
    Satu baris per perubahan status. Objeknya apa pun, lewat
    GenericForeignKey -- supaya app ini tidak perlu mengimpor app lain
    dan bisa tetap berada di lapis bawah.
    """

    waktu = models.DateTimeField(auto_now_add=True, db_index=True)
    oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name='jejak_aktivitas',
    )

    aksi = models.CharField(max_length=12, choices=JenisAksi.choices,
                            db_index=True)

    # Objek yang berubah
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id    = models.PositiveBigIntegerField()
    objek        = GenericForeignKey('content_type', 'object_id')

    # Salinan teks supaya laporan tetap terbaca setelah objeknya diarsip
    # atau nomornya berubah.
    label_objek = models.CharField(max_length=120, blank=True)

    # Entitas yang terdampak. Boleh kosong untuk objek lintas entitas
    # seperti akun pengguna.
    entitas = models.ForeignKey(
        'core.Entitas', null=True, blank=True,
        on_delete=models.PROTECT, related_name='jejak_aktivitas',
    )

    status_lama = models.CharField(max_length=32, blank=True)
    status_baru = models.CharField(max_length=32, blank=True)
    alasan      = models.TextField(blank=True)

    # Rincian tambahan yang tidak muat di kolom di atas.
    rincian = models.JSONField(null=True, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'audit_jejak_aktivitas'
        ordering = ['-waktu', '-id']
        verbose_name = 'Jejak aktivitas'
        verbose_name_plural = 'Jejak aktivitas'
        indexes = [
            models.Index(fields=['content_type', 'object_id'],
                         name='ix_jejak_objek'),
            models.Index(fields=['oleh', '-waktu'], name='ix_jejak_oleh'),
            models.Index(fields=['entitas', '-waktu'], name='ix_jejak_entitas'),
            models.Index(fields=['aksi', '-waktu'], name='ix_jejak_aksi'),
        ]

    def __str__(self):
        siapa = self.oleh.username if self.oleh_id else 'sistem'
        return f"[{self.waktu:%Y-%m-%d %H:%M}] {siapa} {self.aksi} {self.label_objek}"

    @property
    def perpindahan(self):
        """DRAFT -> TERKIRIM, atau string kosong kalau bukan perubahan status."""
        if not (self.status_lama or self.status_baru):
            return ''
        return f"{self.status_lama or '-'} -> {self.status_baru or '-'}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('JejakAktivitas append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('JejakAktivitas append-only.')
