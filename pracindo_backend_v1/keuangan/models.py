"""
Kas dan bank -- sisi KEPUTUSAN atas uang.

Batas dengan akunting: kalau objeknya punya NOMOR REKENING, dia milik
keuangan. Kalau punya KODE AKUN, dia milik akunting.

Ketergantungan satu arah: keuangan memanggil akunting, tidak pernah
sebaliknya. Impor ke akunting dilakukan DI DALAM FUNGSI di services.py,
bukan di kepala file.

MutasiKas memakai pola bank: saldo ditulis saat posting, tidak pernah
dihitung dengan SUM saat dibaca.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import DiauditModel, TimeStampedModel


class JenisRekening(models.TextChoices):
    BANK      = 'BANK',      'Rekening bank'
    KAS       = 'KAS',       'Kas tunai'
    KAS_KECIL = 'KAS_KECIL', 'Kas kecil'


class RekeningBank(TimeStampedModel):
    entitas = models.ForeignKey('core.Entitas', on_delete=models.PROTECT,
                                related_name='rekening')
    jenis   = models.CharField(max_length=10, choices=JenisRekening.choices)

    nama_bank      = models.CharField(max_length=80, blank=True)
    nomor_rekening = models.CharField(max_length=40, blank=True)
    nama_pemilik   = models.CharField(max_length=120, blank=True)

    akun = models.ForeignKey('akunting.Akun', on_delete=models.PROTECT,
                             related_name='rekening')

    saldo = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )
    urutan_terakhir = models.BigIntegerField(default=0, editable=False)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'keuangan_rekening_bank'
        ordering = ['entitas__kode', 'nama_bank']
        verbose_name_plural = 'Rekening bank'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'nomor_rekening'],
                condition=~Q(nomor_rekening=''),
                name='uq_rekening_nomor',
            ),
        ]

    def __str__(self):
        if self.jenis == JenisRekening.BANK:
            return f"{self.nama_bank} {self.nomor_rekening} ({self.entitas.kode})"
        return f"{self.get_jenis_display()} {self.entitas.kode}"


class MutasiKas(models.Model):
    """
    Append-only dengan saldo berjalan.

    idempotency_key mencegah pembayaran dobel saat jaringan putus dan
    klien mengirim ulang -- pola yang sama dipakai transfer bank.
    """

    rekening = models.ForeignKey(RekeningBank, on_delete=models.PROTECT,
                                 related_name='mutasi')
    urutan   = models.BigIntegerField()
    tanggal  = models.DateTimeField(default=timezone.now, db_index=True)

    debit  = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                 default=Decimal('0'))   
    kredit = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                 default=Decimal('0'))   
    saldo_akhir = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES)
    keterangan = models.CharField(max_length=255, blank=True)
    referensi  = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=96, unique=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'keuangan_mutasi_kas'
        ordering = ['rekening', 'urutan']
        verbose_name_plural = 'Mutasi kas'
        constraints = [
            models.UniqueConstraint(fields=['rekening', 'urutan'], name='uq_mutasi_kas_urutan'),
            models.CheckConstraint(
                condition=Q(debit__gte=0) & Q(kredit__gte=0), name='ck_mutasi_kas_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(debit=0) | Q(kredit=0), name='ck_mutasi_kas_satu_sisi',
            ),
        ]
        indexes = [models.Index(fields=['rekening', '-urutan'], name='ix_mutasi_kas_urut')]

    def __str__(self):
        arah = f"-{self.debit}" if self.debit else f"+{self.kredit}"
        return f"{self.rekening} {arah} = {self.saldo_akhir}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('MutasiKas append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('MutasiKas append-only.')


class StatusRencana(models.TextChoices):
    DRAFT      = 'DRAFT',      'Draft'
    DIAJUKAN   = 'DIAJUKAN',   'Diajukan'
    DISETUJUI  = 'DISETUJUI',  'Disetujui'
    DIEKSEKUSI = 'DIEKSEKUSI', 'Sudah dibayar'
    DITOLAK    = 'DITOLAK',    'Ditolak'


class RencanaBayar(DiauditModel):
    """
    Usulan pembayaran ke suplier. Nominal di sini hanya USULAN --
    angka final divalidasi ulang di bawah lock saat eksekusi, karena
    sisa hutang bisa berubah antara penyusunan dan pembayaran.
    """

    entitas  = models.ForeignKey('core.Entitas', on_delete=models.PROTECT)
    suplier  = models.ForeignKey('master.Suplier', on_delete=models.PROTECT,
                                 related_name='rencana_bayar')
    rekening = models.ForeignKey(RekeningBank, on_delete=models.PROTECT,
                                 related_name='rencana_bayar')

    tanggal_rencana = models.DateField()
    nominal = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    status = models.CharField(max_length=12, choices=StatusRencana.choices,
                              default=StatusRencana.DRAFT, db_index=True)

    disetujui_oleh = models.ForeignKey(
        'staff_user.Profil', null=True, blank=True,
        on_delete=models.PROTECT, related_name='rencana_disetujui',
    )
    dieksekusi_oleh = models.ForeignKey(
        'staff_user.Profil', null=True, blank=True,
        on_delete=models.PROTECT, related_name='rencana_dieksekusi',
    )
    mutasi = models.OneToOneField(
        MutasiKas, null=True, blank=True,
        on_delete=models.PROTECT, related_name='rencana',
    )
    catatan = models.TextField(blank=True)

    class Meta:
        db_table = 'keuangan_rencana_bayar'
        ordering = ['tanggal_rencana', 'id']
        verbose_name_plural = 'Rencana bayar'
        indexes = [
            models.Index(fields=['status', 'tanggal_rencana'], name='ix_rencana_status'),
        ]

    def __str__(self):
        return f"{self.suplier.nama} - {self.nominal} ({self.get_status_display()})"

    def clean(self):
        if self.rekening_id and self.entitas_id:
            if self.rekening.entitas_id != self.entitas_id:
                raise ValidationError(
                    {'rekening': 'Rekening harus milik entitas yang sama.'}
                )

class PengeluaranKas(TimeStampedModel):
    entitas = models.ForeignKey('core.Entitas', on_delete=models.PROTECT)
    kategori = models.CharField(max_length=50)
    keterangan = models.CharField(max_length=255)
    pemohon = models.CharField(max_length=120)
    nominal = models.DecimalField(max_digits=18, decimal_places=2)
    bukti_nota = models.FileField(upload_to='keuangan/nota/', null=True, blank=True)
    
    # Menautkan bukti pengeluaran ini langsung ke mutasi brankas
    mutasi = models.OneToOneField(
        'keuangan.MutasiKas', null=True, blank=True, 
        on_delete=models.PROTECT, related_name='pengeluaran'
    )

    class Meta:
        db_table = 'keuangan_pengeluaran_kas'
        ordering = ['-id']

    def __str__(self):
        return f"{self.keterangan} - {self.nominal}"
