"""
Resep dan sesi produksi — produksi/models.py

RESEP menyatakan komposisi satu unit produk jadi. Contoh:
    1 teh kemasan = 1 teh celup + 2 g gula

Resep berversi. Perubahan komposisi tidak boleh menulis ulang sesi lama,
jadi setiap sesi menyimpan resep VERSI MANA yang dipakainya.

SESI PRODUKSI adalah wadah satu putaran produksi:
    DRAFT    -> input dan output masih bisa diubah
    BERJALAN -> bahan sudah diambil dari pool
    SELESAI  -> hasil sudah masuk pool, tidak bisa diubah lagi

Produksi bekerja di lapis POOL sepenuhnya. Tidak ada entitas di sini --
penyelesaian siapa dapat berapa terjadi belakangan lewat klaim.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.constants import QTY_DIGITS, QTY_PLACES
from core.models import CounterDokumen, DiauditModel, TimeStampedModel


# =========================================================
# RESEP
# =========================================================

class Resep(TimeStampedModel):
    produk_jadi = models.ForeignKey(
        'master.Produk', on_delete=models.PROTECT, related_name='resep',
    )
    versi = models.PositiveSmallIntegerField(default=1)
    nama  = models.CharField(max_length=120, blank=True)
    hasil_per_batch = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('1'), validators=[MinValueValidator(Decimal('0.001'))],
    )
    susut_wajar = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0'),
    )

    berlaku_sejak = models.DateField(default=timezone.localdate)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'produksi_resep'
        ordering = ['produk_jadi__kode', '-versi']
        verbose_name_plural = 'Resep'
        constraints = [
            models.UniqueConstraint(fields=['produk_jadi', 'versi'],
                                    name='uq_resep_versi'),
            models.CheckConstraint(condition=Q(hasil_per_batch__gt=0),
                                   name='ck_resep_hasil_positif'),
            models.CheckConstraint(
                condition=Q(susut_wajar__gte=0) & Q(susut_wajar__lt=1),
                name='ck_resep_susut_wajar',
            ),
        ]

    def __str__(self):
        return f"{self.produk_jadi.kode} v{self.versi}"

    @classmethod
    def berlaku(cls, produk_jadi_id, tanggal=None):
        """Resep aktif terbaru untuk tanggal tertentu."""
        tanggal = tanggal or timezone.localdate()
        r = (cls.objects.filter(produk_jadi_id=produk_jadi_id, aktif=True,
                                berlaku_sejak__lte=tanggal)
             .order_by('-berlaku_sejak', '-versi').first())
        if not r:
            raise ValidationError(
                f'Belum ada resep aktif untuk produk {produk_jadi_id}.'
            )
        return r

    def kebutuhan(self, qty_target):
        """
        Bahan yang dibutuhkan untuk memproduksi qty_target unit.
        Return: {produk_id: qty_dibutuhkan}
        """
        faktor = Decimal(qty_target) / self.hasil_per_batch
        return {
            i.bahan_id: (i.qty * faktor).quantize(Decimal('0.001'))
            for i in self.item.all()
        }


class ResepItem(models.Model):
    resep = models.ForeignKey(Resep, on_delete=models.CASCADE,
                              related_name='item')
    bahan = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                              related_name='dipakai_di_resep')
    qty = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0.001'))],
    )

    class Meta:
        db_table = 'produksi_resep_item'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['resep', 'bahan'],
                                    name='uq_resep_item_bahan'),
            models.CheckConstraint(condition=Q(qty__gt=0),
                                   name='ck_resep_item_qty'),
        ]

    def __str__(self):
        return f"{self.bahan.kode} x {self.qty}"

    def clean(self):
        if self.resep_id and self.bahan_id == self.resep.produk_jadi_id:
            raise ValidationError({'bahan': 'Produk tidak boleh jadi bahannya sendiri.'})


# =========================================================
# SESI PRODUKSI
# =========================================================

class StatusSesi(models.TextChoices):
    DRAFT    = 'DRAFT',    'Draft'
    BERJALAN = 'BERJALAN', 'Berjalan'
    SELESAI  = 'SELESAI',  'Selesai'
    BATAL    = 'BATAL',    'Dibatalkan'


class SesiProduksi(DiauditModel):
    """
    Satu putaran produksi. Beroperasi di lapis POOL, tanpa entitas.

    grup_bahan menentukan pool mana yang dipakai. Satu sesi tidak boleh
    melintasi grup -- pool PT dan pool BERSAMA tidak pernah bercampur.
    """

    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT,
                                   related_name='sesi_produksi')
    nomor   = models.CharField(max_length=32, editable=False)
    tanggal = models.DateField(default=timezone.localdate, db_index=True)

    resep = models.ForeignKey(Resep, on_delete=models.PROTECT,
                              related_name='sesi')
    qty_target = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    qty_hasil = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )

    status = models.CharField(max_length=10, choices=StatusSesi.choices,
                              default=StatusSesi.DRAFT, db_index=True)
    tangki_hasil = models.ForeignKey(
        'inventory.Tangki', null=True, blank=True,
        on_delete=models.PROTECT, related_name='sesi_hasil',
    )
    catatan = models.TextField(blank=True)

    class Meta:
        db_table = 'produksi_sesi'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Sesi produksi'
        constraints = [
            models.UniqueConstraint(fields=['grup_bahan', 'nomor'],
                                    name='uq_sesi_nomor'),
            models.CheckConstraint(condition=Q(qty_target__gt=0),
                                   name='ck_sesi_target_positif'),
        ]
        indexes = [
            models.Index(fields=['grup_bahan', 'status', '-tanggal'],
                         name='ix_sesi_grup_status'),
        ]

    def __str__(self):
        return f"{self.nomor} - {self.resep.produk_jadi.kode} x {self.qty_target}"

    @property
    def susut(self):
        return self.qty_target - self.qty_hasil

    @property
    def rendemen(self):
        """Hasil dibagi target. Di bawah 1 berarti ada susut."""
        return (self.qty_hasil / self.qty_target) if self.qty_target else Decimal('0')

    def save(self, *args, **kwargs):
        if not self.nomor:
            # Penomoran per grup memakai entitas pertama dalam grup sebagai
            # pemegang counter. Sesi bukan dokumen milik satu entitas.
            entitas = self.grup_bahan.entitas.order_by('kode').first()
            if not entitas:
                raise ValidationError('Grup bahan belum punya entitas.')
            self.nomor = CounterDokumen.berikutnya(entitas, 'SESI', self.tanggal)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != StatusSesi.DRAFT:
            raise ValidationError('Sesi yang sudah berjalan tidak bisa dihapus.')
        return super().delete(*args, **kwargs)


class SesiInput(models.Model):
    """Bahan yang BENAR-BENAR diambil dari pool, bukan yang direncanakan."""

    sesi  = models.ForeignKey(SesiProduksi, on_delete=models.PROTECT,
                              related_name='input')
    bahan = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                              related_name='+')
    qty_rencana = models.DecimalField(max_digits=QTY_DIGITS,
                                      decimal_places=QTY_PLACES,
                                      default=Decimal('0'))
    qty_aktual = models.DecimalField(max_digits=QTY_DIGITS,
                                     decimal_places=QTY_PLACES,
                                     default=Decimal('0'))
    tangki = models.ForeignKey('inventory.Tangki', null=True, blank=True,
                               on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'produksi_sesi_input'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['sesi', 'bahan'],
                                    name='uq_sesi_input_bahan'),
        ]

    def __str__(self):
        return f"{self.bahan.kode} {self.qty_aktual}"

    @property
    def selisih(self):
        return self.qty_aktual - self.qty_rencana
