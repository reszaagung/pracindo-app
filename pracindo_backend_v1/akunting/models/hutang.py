"""
Hutang usaha (AP) — FakturPembelian, KartuHutang, UangMukaSuplier.

Pembagian peran:
  - FakturPembelian menyimpan sisa_hutang sebagai CACHE. Baca sisa hutang =
    baca satu kolom, O(1), tidak peduli ada berapa baris mutasi.
  - KartuHutang adalah SUMBER KEBENARAN. Append-only, tidak pernah di-update
    maupun di-delete. Cache di atas bisa melenceng karena bug; ledger tidak.

Pembayaran yang dibatalkan TIDAK dihapus dan tidak diberi flag. Post baris
KOREKSI dengan kredit sebesar nominal yang dibatalkan. total_dibayar jadi
benar tanpa perlu filter apa pun di query.

Liabilitas sendiri lahir lebih dulu di penerimaan barang sebagai GRNI.
Faktur tidak melahirkan hutang — faktur mereklasifikasi GRNI jadi hutang
usaha dan menetapkan tanggal jatuh tempo.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import CounterDokumen, DiauditModel, TimeStampedModel


class JenisFaktur(models.TextChoices):
    BARANG = 'BARANG', 'Pembelian barang'
    JASA   = 'JASA',   'Jasa / beban'


class StatusFaktur(models.TextChoices):
    BELUM_BAYAR = 'BELUM_BAYAR', 'Belum dibayar'
    SEBAGIAN    = 'SEBAGIAN',    'Dibayar sebagian'
    LUNAS       = 'LUNAS',       'Lunas'
    BATAL       = 'BATAL',       'Dibatalkan'


class JenisMutasiHutang(models.TextChoices):
    FAKTUR  = 'FAKTUR',  'Faktur diterbitkan'
    BAYAR   = 'BAYAR',   'Pembayaran'
    RETUR   = 'RETUR',   'Retur pembelian'
    KOREKSI = 'KOREKSI', 'Koreksi / pembatalan'


class FakturPembelianQuerySet(models.QuerySet):

    def terbuka(self):
        return self.filter(status__in=[StatusFaktur.BELUM_BAYAR, StatusFaktur.SEBAGIAN])

    def untuk_entitas(self, entitas_id):
        return self.filter(entitas_id=entitas_id)

    def jatuh_tempo_sampai(self, tanggal):
        return self.terbuka().filter(tanggal_jatuh_tempo__lte=tanggal)

    def terlambat(self, per=None):
        per = per or timezone.localdate()
        return self.terbuka().filter(tanggal_jatuh_tempo__lt=per)


class FakturPembelian(DiauditModel):
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='faktur_pembelian',
    )
    suplier = models.ForeignKey(
        'master.Suplier', on_delete=models.PROTECT, related_name='faktur_pembelian',
    )

    jenis = models.CharField(
        max_length=8, choices=JenisFaktur.choices, default=JenisFaktur.BARANG,
    )
    # Wajib untuk jenis BARANG — struktur ini yang mencegah penagihan atas
    # barang yang belum pernah datang. Null hanya boleh untuk JASA.
    penerimaan = models.ForeignKey(
        'warehouse.PenerimaanBarang', null=True, blank=True,
        on_delete=models.PROTECT, related_name='faktur',
    )

    no_internal   = models.CharField(max_length=32, editable=False)
    nomor_faktur  = models.CharField(max_length=64)          # nomor dari suplier
    tanggal_faktur      = models.DateField()
    termin_hari         = models.PositiveSmallIntegerField(default=0)
    tanggal_jatuh_tempo = models.DateField(db_index=True, editable=False)

    total_tagihan = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        validators=[MinValueValidator(Decimal('0'))],
    )
    total_dibayar = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )
    sisa_hutang = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )

    status = models.CharField(
        max_length=12, choices=StatusFaktur.choices,
        default=StatusFaktur.BELUM_BAYAR, db_index=True,
    )
    dokumen = models.ForeignKey(
        'dokumen.Lampiran', null=True, blank=True,
        on_delete=models.PROTECT, related_name='+',
    )
    catatan = models.TextField(blank=True)

    objects = FakturPembelianQuerySet.as_manager()

    class Meta:
        db_table = 'akunting_faktur_pembelian'
        ordering = ['tanggal_jatuh_tempo', 'id']
        verbose_name_plural = 'Faktur pembelian'
        constraints = [
            # Suplier tidak boleh menagih nomor faktur yang sama dua kali.
            models.UniqueConstraint(
                fields=['suplier', 'nomor_faktur'], name='uq_faktur_suplier_nomor',
            ),
            models.UniqueConstraint(
                fields=['entitas', 'no_internal'], name='uq_faktur_no_internal',
            ),
            models.CheckConstraint(
                condition=Q(sisa_hutang__gte=0), name='ck_faktur_sisa_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(total_dibayar__gte=0) & Q(total_dibayar__lte=models.F('total_tagihan')),
                name='ck_faktur_dibayar_dalam_batas',
            ),
            # Faktur barang WAJIB punya penerimaan.
            models.CheckConstraint(
                condition=Q(jenis=JenisFaktur.JASA) | Q(penerimaan__isnull=False),
                name='ck_faktur_barang_wajib_penerimaan',
            ),
        ]
        indexes = [
            models.Index(
                fields=['suplier', 'status', 'tanggal_jatuh_tempo'],
                name='ix_faktur_sup_status_tempo',
            ),
            models.Index(fields=['entitas', 'status'], name='ix_faktur_ent_status'),
        ]

    def __str__(self):
        return f"{self.nomor_faktur} · {self.suplier.nama}"

    @property
    def terlambat(self):
        return (self.status in (StatusFaktur.BELUM_BAYAR, StatusFaktur.SEBAGIAN)
                and self.tanggal_jatuh_tempo < timezone.localdate())

    @property
    def umur_hari(self):
        """Positif = sudah lewat tempo."""
        return (timezone.localdate() - self.tanggal_jatuh_tempo).days

    def save(self, *args, **kwargs):
        if not self.no_internal:
            self.no_internal = CounterDokumen.berikutnya(
                self.entitas, 'FAKTUR', self.tanggal_faktur,
            )
        self.tanggal_jatuh_tempo = self.tanggal_faktur + timezone.timedelta(
            days=self.termin_hari
        )
        if self._state.adding:
            self.sisa_hutang = self.total_tagihan
        super().save(*args, **kwargs)

    def clean(self):
        if self.jenis == JenisFaktur.BARANG and not self.penerimaan_id:
            raise ValidationError(
                {'penerimaan': 'Faktur barang wajib merujuk ke penerimaan gudang.'}
            )
        if self.penerimaan_id and self.penerimaan.purchase_order.entitas_id != self.entitas_id:
            raise ValidationError(
                {'entitas': 'Entitas faktur harus sama dengan entitas PO.'}
            )

    def delete(self, *args, **kwargs):
        raise ValidationError('Faktur tidak bisa dihapus. Terbitkan koreksi.')


class KartuHutang(models.Model):
    """Append-only. Tidak pernah di-update maupun di-delete."""

    faktur  = models.ForeignKey(
        FakturPembelian, on_delete=models.PROTECT, related_name='mutasi',
    )
    tanggal = models.DateField(db_index=True)
    jenis   = models.CharField(max_length=8, choices=JenisMutasiHutang.choices)

    # debit mengurangi hutang, kredit menambah hutang
    debit  = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0'),
    )
    kredit = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0'),
    )

    referensi = models.CharField(max_length=64, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'akunting_kartu_hutang'
        ordering = ['tanggal', 'id']
        verbose_name_plural = 'Kartu hutang'
        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gte=0) & Q(kredit__gte=0), name='ck_kh_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(debit=0) | Q(kredit=0), name='ck_kh_satu_sisi',
            ),
        ]
        indexes = [
            models.Index(fields=['faktur', 'tanggal'], name='ix_kh_faktur_tgl'),
        ]

    def __str__(self):
        sisi = f"D {self.debit}" if self.debit else f"K {self.kredit}"
        return f"{self.faktur.nomor_faktur} · {self.get_jenis_display()} · {sisi}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('KartuHutang append-only, baris tidak boleh diubah.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('KartuHutang append-only, baris tidak boleh dihapus.')


class UangMukaSuplier(TimeStampedModel):
    """
    Kelebihan bayar yang belum dialokasikan ke faktur mana pun.
    Diisi oleh alokasi_pembayaran() saat nominal melebihi total faktur terbuka.
    """

    entitas = models.ForeignKey('core.Entitas', on_delete=models.PROTECT)
    suplier = models.ForeignKey(
        'master.Suplier', on_delete=models.PROTECT, related_name='uang_muka',
    )
    tanggal = models.DateField()

    nominal = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    sisa = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, editable=False,
    )

    referensi = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = 'akunting_uang_muka_suplier'
        ordering = ['tanggal', 'id']
        verbose_name_plural = 'Uang muka suplier'
        constraints = [
            models.CheckConstraint(
                condition=Q(sisa__gte=0) & Q(sisa__lte=models.F('nominal')),
                name='ck_um_sisa_dalam_batas',
            ),
        ]
        indexes = [
            models.Index(fields=['suplier', 'entitas'], name='ix_um_sup_ent'),
        ]

    def __str__(self):
        return f"UM {self.suplier.nama} · sisa {self.sisa}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.sisa = self.nominal
        super().save(*args, **kwargs)
