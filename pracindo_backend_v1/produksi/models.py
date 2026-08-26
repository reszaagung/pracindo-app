"""
Model inti produksi — produksi/models.py

KONSEP KUNCI: POOL PATUNGAN

Batch TIDAK menyimpan grup_bahan atau entitas apa pun. Bahan baku ditarik
dari inventory.PoolResource — satu saldo per produk, digabung lintas
entitas dan lintas grup bahan ("patungan"). Konsekuensinya:

  - Mixing menarik nilai langsung dari PoolResource, dicatat per baris di
    BatchInputRaw. harga_per_kg & nilai di baris itu adalah SNAPSHOT
    harga_rata pool pada saat ditarik.
  - Blending menarik nilai dari batch lain yang sudah POSTED (dicatat di
    TransferWip), bukan dari pool mentah.
  - Kedua proses ini murni memindahkan nilai fisik (pool -> WIP batch,
    atau WIP batch -> WIP batch). TIDAK ADA satu baris MutasiKlaim pun
    yang tercipta di sini.
  - Siapa berhak atas berapa rupiah baru dihitung saat Packing menarik
    barang jadi dari batch dan membebankan ke SaldoEntitas si penarik.
    Itulah satu-satunya titik "klaim" — bukan di titik produksi.

Karena itu JANGAN PERNAH menambahkan field grup_bahan/entitas ke Batch,
BatchInputRaw, atau TransferWip. Kode di modul lain yang memfilter
Batch pakai grup_bahan_id (langsung atau lewat relasi) adalah bug
peninggalan arsitektur lama dan harus dihapus filternya, bukan
diperbaiki jalur relasinya.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.utils import timezone

from core.models import DiauditModel, TimeStampedModel

D0 = Decimal("0")
Q_RP = Decimal("0.01")
Q_QTY = Decimal("0.001")
Q_HARGA = Decimal("0.000001")


def rp(x):
    return Decimal(x).quantize(Q_RP, rounding=ROUND_HALF_UP)


def qty(x):
    return Decimal(x).quantize(Q_QTY, rounding=ROUND_HALF_UP)


def harga(x):
    return Decimal(x).quantize(Q_HARGA, rounding=ROUND_HALF_UP)


class StatusBatch(models.TextChoices):
    DRAFT  = "DRAFT",  "Draft"
    POSTED = "POSTED", "Diposting"
    VOID   = "VOID",   "Dibatalkan"


class TipeProses(models.TextChoices):
    MIXING   = "MIXING",   "Mixing (racik dari pool bersama)"
    BLENDING = "BLENDING", "Blending (racik dari batch lain)"


class Tangki(TimeStampedModel):
    """Tangki produksi — resource bersama, tidak dimiliki entitas/grup manapun."""
    kode         = models.CharField(max_length=20, unique=True)
    nama         = models.CharField(max_length=80, blank=True, default="")
    kapasitas_kg = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)
    aktif        = models.BooleanField(default=True)

    class Meta:
        db_table = "produksi_tangki"
        ordering = ["kode"]
        verbose_name_plural = "Tangki"

    def __str__(self):
        return self.kode


class Batch(DiauditModel):
    nomor      = models.CharField(max_length=48, unique=True, editable=False)   # Batch ID (Auto-Gen)
    jenis      = models.CharField(max_length=10, choices=TipeProses.choices)    # MIXING / BLENDING
    nama_hasil = models.CharField(max_length=120)                               # Yield Nomenclature — label bebas
    tangki     = models.ForeignKey(Tangki, on_delete=models.PROTECT, related_name="batch_set")  # Destination Tank

    qty_hasil   = models.DecimalField(max_digits=18, decimal_places=3, default=D0)  # output aktual setelah posting
    nilai_hasil = models.DecimalField(max_digits=20, decimal_places=2, default=D0)  # nilai WIP batch ini

    susut_kg    = models.DecimalField(max_digits=18, decimal_places=3, default=D0)  # Shrinkage/Deficit (Kg), input user
    nilai_susut = models.DecimalField(max_digits=20, decimal_places=2, default=D0)  # dihitung services saat posting

    tanggal   = models.DateField(default=timezone.localdate, db_index=True)
    waktu     = models.DateTimeField(default=timezone.now, db_index=True)
    status    = models.CharField(max_length=10, choices=StatusBatch.choices, default=StatusBatch.DRAFT, db_index=True)
    posted_at = models.DateTimeField(null=True, blank=True, editable=False)
    catatan   = models.TextField(blank=True, default="")

    class Meta:
        db_table = "produksi_batch"
        ordering = ["-waktu", "-id"]
        verbose_name_plural = "Batch"
        indexes = [
            models.Index(fields=["tangki", "status"], name="ix_batch_tangki"),
            models.Index(fields=["jenis", "status"], name="ix_batch_jenis"),
        ]
        constraints = [
            CheckConstraint(condition=Q(qty_hasil__gte=0), name="ck_batch_qty_non_negatif"),
            CheckConstraint(condition=Q(nilai_hasil__gte=0), name="ck_batch_nilai_non_negatif"),
            CheckConstraint(condition=Q(susut_kg__gte=0), name="ck_batch_susut_non_negatif"),
        ]

    def __str__(self):
        return self.nomor

    @property
    def harga_per_kg(self):
        """Harga WIP per kg batch ini. 0 selama masih DRAFT (qty_hasil belum terisi)."""
        return harga(self.nilai_hasil / self.qty_hasil) if self.qty_hasil > 0 else D0

    def delete(self, *args, **kwargs):
        raise models.ProtectedError("Batch tidak bisa dihapus langsung. Terbitkan VOID.", [self])


class BatchInputRaw(models.Model):
    """
    Satu baris BOM Mixing = satu produk ditarik dari inventory.PoolResource
    (pool bersama, tanpa dimensi grup_bahan/entitas).

    harga_per_kg & nilai adalah SNAPSHOT harga_rata pool pada saat baris
    ini diposting — bukan dihitung ulang setiap saat, karena harga pool
    terus bergerak seiring setoran/penarikan lain sesudahnya. Hanya
    dipakai untuk batch berjenis MIXING.
    """
    batch        = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="input_raw")
    produk       = models.ForeignKey("master.Produk", on_delete=models.PROTECT, related_name="+")
    qty_kg       = models.DecimalField(max_digits=18, decimal_places=3)                          # Consumed Qty
    harga_per_kg = models.DecimalField(max_digits=20, decimal_places=6, default=D0, editable=False)  # Unit Cost, snapshot
    nilai        = models.DecimalField(max_digits=20, decimal_places=2, default=D0, editable=False)  # Subtotal

    class Meta:
        db_table = "produksi_batch_input_raw"
        ordering = ["id"]
        verbose_name_plural = "Batch input raw"
        constraints = [
            CheckConstraint(condition=Q(qty_kg__gt=0), name="ck_input_raw_qty_positif"),
            UniqueConstraint(fields=["batch", "produk"], name="uq_input_raw_per_batch_produk"),
        ]

    def __str__(self):
        return f"{self.batch.nomor} <- {self.produk} {self.qty_kg}kg"


class TransferWip(models.Model):
    """
    Satu baris Blending = memindahkan sebagian/seluruh nilai WIP dari
    batch sumber (POSTED) ke batch tujuan (baru). Tidak menyentuh
    PoolResource maupun MutasiKlaim sama sekali — murni transfer nilai
    antar batch. Hanya dipakai untuk batch berjenis BLENDING.
    """
    batch_sumber = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="transfer_keluar")
    batch_tujuan = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="transfer_masuk")
    qty_kg       = models.DecimalField(max_digits=18, decimal_places=3)
    nilai        = models.DecimalField(max_digits=20, decimal_places=2, default=D0, editable=False)
    waktu        = models.DateTimeField(default=timezone.now)
    dibuat_oleh  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", editable=False)

    class Meta:
        db_table = "produksi_transfer_wip"
        ordering = ["id"]
        verbose_name_plural = "Transfer WIP"
        constraints = [
            CheckConstraint(condition=Q(qty_kg__gt=0), name="ck_transfer_qty_positif"),
            CheckConstraint(condition=~Q(batch_sumber=F("batch_tujuan")), name="ck_transfer_beda_batch"),
        ]

    def __str__(self):
        return f"{self.batch_sumber.nomor} -> {self.batch_tujuan.nomor}: {self.qty_kg}kg"