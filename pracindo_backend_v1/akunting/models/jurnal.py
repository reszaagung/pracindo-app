"""
Buku besar — JurnalUmum dan JurnalDetail.

Invariant SUM(debit) = SUM(kredit) per jurnal TIDAK ditegakkan di sini.
Validasi Django bisa dilewati bulk_create, shell, dan migrasi. Penegakannya
lewat CONSTRAINT TRIGGER berjenis DEFERRABLE INITIALLY DEFERRED yang
dipasang di migrasi — lihat akunting/migrations/00XX_trigger_jurnal.py.
DEFERRED penting: trigger baru berjalan saat COMMIT, sehingga baris debit
boleh disimpan lebih dulu sebelum baris kreditnya menyusul.

Jurnal tidak pernah diedit atau dihapus. Koreksi dilakukan dengan
menerbitkan jurnal balik (debit dan kredit ditukar).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import DiauditModel

from .akun import Akun


class JenisKejadian(models.TextChoices):
    AUDIT_GUDANG  = 'AUDIT_GUDANG',  'Penerimaan barang'
    FAKTUR_MASUK  = 'FAKTUR_MASUK',  'Faktur pembelian masuk'
    SELISIH_HARGA = 'SELISIH_HARGA', 'Selisih harga faktur'
    BAYAR_HUTANG  = 'BAYAR_HUTANG',  'Pembayaran hutang'
    RETUR_BELI    = 'RETUR_BELI',    'Retur pembelian'
    PENJUALAN     = 'PENJUALAN',     'Penjualan'
    TERIMA_PIUTANG = 'TERIMA_PIUTANG', 'Penerimaan piutang'
    BEBAN_KAS     = 'BEBAN_KAS',     'Beban dibayar tunai'
    PENYUSUTAN    = 'PENYUSUTAN',    'Penyusutan aset tetap'
    PRODUKSI      = 'PRODUKSI',      'Rekonsiliasi sesi produksi'
    KOREKSI       = 'KOREKSI',       'Jurnal balik / koreksi'


class JurnalUmumQuerySet(models.QuerySet):

    def untuk_entitas(self, entitas_id):
        return self.filter(entitas_id=entitas_id)

    def sampai(self, tanggal):
        return self.filter(tanggal__lte=tanggal)

    def belum_dibalik(self):
        return self.filter(dibalik_oleh__isnull=True)


class JurnalUmum(DiauditModel):
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='jurnal',
    )

    nomor    = models.CharField(max_length=32, editable=False)
    tanggal  = models.DateField(db_index=True)
    kejadian = models.CharField(max_length=16, choices=JenisKejadian.choices, db_index=True)
    referensi   = models.CharField(max_length=64, blank=True)
    keterangan  = models.CharField(max_length=255, blank=True)

    idempotency_key = models.CharField(max_length=96, unique=True, editable=False)
    dibalik_oleh = models.OneToOneField(
        'self', null=True, blank=True, on_delete=models.PROTECT,
        related_name='membalik', editable=False,
    )

    objects = JurnalUmumQuerySet.as_manager()

    class Meta:
        db_table = 'akunting_jurnal_umum'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Jurnal umum'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'nomor'], name='uq_jurnal_nomor_per_entitas',
            ),
        ]
        indexes = [
            models.Index(fields=['entitas', 'tanggal'], name='ix_jurnal_ent_tgl'),
            models.Index(fields=['referensi'], name='ix_jurnal_referensi'),
        ]

    def __str__(self):
        return f"{self.nomor} · {self.get_kejadian_display()}"

    @property
    def total_debit(self):
        return self.baris.aggregate(t=Coalesce(Sum('debit'), Decimal('0')))['t']

    @property
    def total_kredit(self):
        return self.baris.aggregate(t=Coalesce(Sum('kredit'), Decimal('0')))['t']

    @property
    def seimbang(self):
        return self.total_debit == self.total_kredit

    @property
    def sudah_dibalik(self):
        return self.dibalik_oleh_id is not None

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Jurnal tidak bisa dihapus. Terbitkan jurnal balik.'
        )


class JurnalDetail(models.Model):
    jurnal = models.ForeignKey(
        JurnalUmum, on_delete=models.PROTECT, related_name='baris',
    )
    akun = models.ForeignKey(
        Akun, on_delete=models.PROTECT, related_name='baris_jurnal',
    )
    debit = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0'),
    )
    kredit = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0'),
    )

    keterangan = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'akunting_jurnal_detail'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gte=0) & Q(kredit__gte=0),
                name='ck_jd_nilai_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(debit=0) | Q(kredit=0),
                name='ck_jd_satu_sisi',
            ),
            models.CheckConstraint(
                condition=~(Q(debit=0) & Q(kredit=0)),
                name='ck_jd_tidak_nol_dua_duanya',
            ),
        ]
        indexes = [
            models.Index(fields=['akun', 'jurnal'], name='ix_jd_akun_jurnal'),
        ]

    def __str__(self):
        sisi = f"D {self.debit}" if self.debit else f"K {self.kredit}"
        return f"{self.akun.kode} · {sisi}"

    def clean(self):
        if self.akun_id and not self.akun.boleh_diposting:
            raise ValidationError(
                {'akun': f'{self.akun.kode} adalah akun header, tidak menerima posting.'}
            )

    def delete(self, *args, **kwargs):
        raise ValidationError('Baris jurnal tidak bisa dihapus.')
