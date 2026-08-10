"""
Bagan akun (COA) dan checkpoint saldo bulanan.

COA dipakai bersama oleh keempat entitas. Saldo per entitas didapat dari
filter jurnal, bukan dari akun yang digandakan. Dengan empat entitas,
empat COA terpisah berarti empat daftar yang harus dijaga tetap sinkron —
dan begitu satu entitas menambah akun sendiri, konsolidasi pecah diam-diam.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import TimeStampedModel


class TipeAkun(models.TextChoices):
    ASET       = 'ASET',       'Aset'
    KEWAJIBAN  = 'KEWAJIBAN',  'Kewajiban'
    EKUITAS     = 'EKUITAS',    'Ekuitas'
    PENDAPATAN = 'PENDAPATAN', 'Pendapatan'
    BEBAN      = 'BEBAN',      'Beban'


# Akun bersaldo normal debit bertambah di sisi debit.
SALDO_NORMAL_DEBIT = frozenset({TipeAkun.ASET, TipeAkun.BEBAN})


class AkunQuerySet(models.QuerySet):

    def bisa_diposting(self):
        return self.filter(boleh_diposting=True, aktif=True)

    def neraca(self):
        return self.filter(tipe__in=[TipeAkun.ASET, TipeAkun.KEWAJIBAN, TipeAkun.EKUITAS])

    def laba_rugi(self):
        return self.filter(tipe__in=[TipeAkun.PENDAPATAN, TipeAkun.BEBAN])


class Akun(TimeStampedModel):
    kode = models.CharField(max_length=8, unique=True)
    nama = models.CharField(max_length=120)
    tipe = models.CharField(max_length=12, choices=TipeAkun.choices, db_index=True)

    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT,
        related_name='anak',
    )

    # Akun header hanya untuk pengelompokan laporan. Jurnal ditolak.
    boleh_diposting = models.BooleanField(default=True)
    aktif = models.BooleanField(default=True)

    objects = AkunQuerySet.as_manager()

    class Meta:
        db_table = 'akunting_akun'
        ordering = ['kode']
        verbose_name_plural = 'Akun'
        indexes = [
            models.Index(fields=['tipe', 'kode'], name='ix_akun_tipe_kode'),
        ]

    def __str__(self):
        return f"{self.kode} — {self.nama}"

    @property
    def saldo_normal(self):
        return 'D' if self.tipe in SALDO_NORMAL_DEBIT else 'K'

    @property
    def pengali(self):
        """Pengali untuk mengubah (debit - kredit) jadi saldo bertanda benar."""
        return 1 if self.tipe in SALDO_NORMAL_DEBIT else -1

    def clean(self):
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({'parent': 'Akun tidak boleh jadi parent dirinya sendiri.'})
            if self.parent.tipe != self.tipe:
                raise ValidationError({'parent': 'Tipe akun harus sama dengan parent.'})
            if self.parent.boleh_diposting:
                raise ValidationError({'parent': 'Parent harus akun header (boleh_diposting=False).'})


class SaldoAkunBulanan(models.Model):
    """
    Checkpoint bulanan per akun per entitas.

    Tanpa ini, laporan per tanggal harus mengagregasi seluruh JurnalDetail
    sejak awal. Dengan ini, laporan hanya menjumlahkan jurnal sejak
    checkpoint terakhir. Diisi oleh proses tutup bulan.
    """

    akun    = models.ForeignKey(Akun, on_delete=models.PROTECT, related_name='saldo_bulanan')
    entitas = models.ForeignKey('core.Entitas', on_delete=models.PROTECT)
    tahun   = models.PositiveSmallIntegerField()
    bulan   = models.PositiveSmallIntegerField()

    saldo_awal   = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                       default=Decimal('0'))
    total_debit  = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                       default=Decimal('0'))
    total_kredit = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                       default=Decimal('0'))
    saldo_akhir  = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                       default=Decimal('0'))

    class Meta:
        db_table = 'akunting_saldo_akun_bulanan'
        ordering = ['-tahun', '-bulan', 'akun__kode']
        constraints = [
            models.UniqueConstraint(
                fields=['akun', 'entitas', 'tahun', 'bulan'],
                name='uq_saldo_akun_periode',
            ),
            models.CheckConstraint(
                condition=Q(bulan__gte=1) & Q(bulan__lte=12),
                name='ck_saldo_bulan_valid',
            ),
        ]
        indexes = [
            models.Index(fields=['entitas', 'tahun', 'bulan'], name='ix_saldo_ent_periode'),
        ]

    def __str__(self):
        return f"{self.akun.kode} · {self.entitas.kode} · {self.bulan:02d}/{self.tahun}"
