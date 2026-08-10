# akunting/models/piutang.py
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.constants import NILAI_DIGITS, NILAI_PLACES
from core.models import CounterDokumen, DiauditModel

class StatusFakturJual(models.TextChoices):
    BELUM_BAYAR = 'BELUM_BAYAR', 'Belum dibayar'
    SEBAGIAN    = 'SEBAGIAN',    'Dibayar sebagian'
    LUNAS       = 'LUNAS',       'Lunas'
    BATAL       = 'BATAL',       'Dibatalkan'

class JenisMutasiPiutang(models.TextChoices):
    FAKTUR  = 'FAKTUR',  'Faktur diterbitkan'
    TERIMA  = 'TERIMA',  'Pembayaran diterima'
    RETUR   = 'RETUR',   'Retur penjualan'
    KOREKSI = 'KOREKSI', 'Koreksi / pembatalan'

class FakturPenjualan(DiauditModel):
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='faktur_penjualan'
    )
    pelanggan = models.ForeignKey(
        'master.Pelanggan', on_delete=models.PROTECT, related_name='faktur_penjualan'
    )
    
    
    no_internal   = models.CharField(max_length=32, editable=False)
    nomor_faktur  = models.CharField(max_length=64, unique=True)
    tanggal_faktur      = models.DateField(default=timezone.localdate)
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
    sisa_piutang = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )
    
    status = models.CharField(
        max_length=12, choices=StatusFakturJual.choices,
        default=StatusFakturJual.BELUM_BAYAR, db_index=True,
    )
    catatan = models.TextField(blank=True)

    class Meta:
        db_table = 'akunting_faktur_penjualan'
        ordering = ['tanggal_jatuh_tempo', 'id']
        verbose_name_plural = 'Faktur Penjualan'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'no_internal'], name='uq_fakturjual_no_internal',
            ),
            models.CheckConstraint(
                condition=Q(sisa_piutang__gte=0), name='ck_fakturjual_sisa_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(total_dibayar__gte=0) & Q(total_dibayar__lte=models.F('total_tagihan')),
                name='ck_fakturjual_dibayar_dalam_batas',
            ),
        ]

    def __str__(self):
        return f"{self.nomor_faktur} - {self.pelanggan.nama}"

    def save(self, *args, **kwargs):
        if not self.no_internal:
            self.no_internal = CounterDokumen.berikutnya(self.entitas, 'INV', self.tanggal_faktur)
        self.tanggal_jatuh_tempo = self.tanggal_faktur + timezone.timedelta(days=self.termin_hari)
        
        if self._state.adding:
            self.sisa_piutang = self.total_tagihan
        super().save(*args, **kwargs)

    # BUG FIX: Cegah faktur dihapus dari database
    def delete(self, *args, **kwargs):
        raise ValidationError('Faktur penjualan tidak bisa dihapus. Terbitkan koreksi.')

class KartuPiutang(models.Model):
    """Sama seperti KartuHutang, tabel ini append-only sebagai sumber kebenaran (Ledger)."""
    faktur = models.ForeignKey(
        FakturPenjualan, on_delete=models.PROTECT, related_name='mutasi'
    )
    tanggal = models.DateField(db_index=True)
    jenis   = models.CharField(max_length=8, choices=JenisMutasiPiutang.choices)

    debit  = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0')
    )
    kredit = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES, default=Decimal('0')
    )
    referensi = models.CharField(max_length=64, blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'akunting_kartu_piutang'
        ordering = ['tanggal', 'id']
        verbose_name_plural = 'Kartu Piutang'
        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gte=0) & Q(kredit__gte=0), name='ck_kp_nonneg',
            ),
            models.CheckConstraint(
                condition=Q(debit=0) | Q(kredit=0), name='ck_kp_satu_sisi',
            ),
        ]
        indexes = [
            models.Index(fields=['faktur', 'tanggal'], name='ix_kp_faktur_tgl'),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('KartuPiutang append-only, baris tidak boleh diubah.')
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('KartuPiutang append-only, baris tidak boleh dihapus.')