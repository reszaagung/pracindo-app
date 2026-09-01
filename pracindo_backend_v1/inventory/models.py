from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils import timezone
from django.db import transaction
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


class StatusDokumen(models.TextChoices):
    DRAFT  = "DRAFT",  "Draft"
    POSTED = "POSTED", "Diposting"
    VOID   = "VOID",   "Dibatalkan"


class SumberPembelian(models.TextChoices):
    PENERIMAAN = "PENERIMAAN", "Dari penerimaan gudang"
    MANUAL     = "MANUAL",     "Input manual (saldo awal / koreksi)"


class PoolResource(TimeStampedModel):
    """
    Stok Fisik Raw Material (Pool Patungan).
    Tidak memiliki relasi ke entitas atau grup bahan. 
    Semua stok fisik untuk satu produk menyatu di sini.
    """
    produk = models.ForeignKey("master.Produk", on_delete=models.PROTECT, related_name="pool_resource")
    qty_kg = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    nilai  = models.DecimalField(max_digits=20, decimal_places=2, default=D0)

    class Meta:
        db_table = "inventory_pool_resource"
        ordering = ["produk"]
        verbose_name_plural = "Pool Resources"
        constraints = [
            UniqueConstraint(fields=["produk"], name="inv_pool_res_unik_per_produk"),
            CheckConstraint(condition=Q(qty_kg__gte=0), name="inv_pool_res_qty_non_negatif"),
            CheckConstraint(condition=Q(nilai__gte=0), name="inv_pool_res_nilai_non_negatif"),
            CheckConstraint(condition=~Q(qty_kg=0) | Q(nilai=0), name="inv_pool_res_kosong_tanpa_nilai"),
        ]

    def __str__(self):
        return f"{self.produk.kode} - {self.produk.nama}: {self.qty_kg}"

    @property
    def harga_rata(self):
        return harga(self.nilai / self.qty_kg) if self.qty_kg > 0 else D0


class Pembelian(DiauditModel):
    nomor        = models.CharField(max_length=48, unique=True, editable=False)
    no_po        = models.CharField(max_length=64, blank=True, default="", db_index=True)
    entitas      = models.ForeignKey("core.Entitas", on_delete=models.PROTECT, related_name="pembelian_pool")
    grup_bahan   = models.ForeignKey("core.GrupBahan", on_delete=models.PROTECT, related_name="pembelian_pool")
    produk       = models.ForeignKey("master.Produk", on_delete=models.PROTECT, related_name="pembelian_pool")
    qty_kg       = models.DecimalField(max_digits=18, decimal_places=3)
    harga_per_kg = models.DecimalField(max_digits=20, decimal_places=6)
    nilai        = models.DecimalField(max_digits=20, decimal_places=2)
    tanggal      = models.DateField(db_index=True)
    waktu        = models.DateTimeField(default=timezone.now, db_index=True)
    status       = models.CharField(max_length=10, choices=StatusDokumen.choices, default=StatusDokumen.DRAFT, db_index=True)
    sumber       = models.CharField(max_length=12, choices=SumberPembelian.choices, default=SumberPembelian.MANUAL, db_index=True)
    penerimaan_item = models.OneToOneField("warehouse.PenerimaanItem", on_delete=models.PROTECT, null=True, blank=True, related_name="pembelian")
    catatan   = models.TextField(blank=True, default="")
    posted_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        db_table = "inventory_pembelian"
        ordering = ["-waktu", "-id"]
        verbose_name_plural = "Pembelian"
        indexes = [
            models.Index(fields=["entitas", "waktu"], name="ix_beli_entitas"),
            models.Index(fields=["tanggal", "status"], name="ix_beli_tanggal"),
        ]
        constraints = [
            CheckConstraint(condition=Q(qty_kg__gt=0), name="ck_beli_qty_positif"),
            CheckConstraint(condition=Q(harga_per_kg__gte=0), name="ck_beli_harga_non_negatif"),
            CheckConstraint(condition=Q(nilai__gte=0), name="ck_beli_nilai_non_negatif"),
            CheckConstraint(condition=~Q(sumber=SumberPembelian.PENERIMAAN) | Q(penerimaan_item__isnull=False), name="ck_beli_penerimaan_ada_jejak"),
        ]

    def __str__(self):
        return self.nomor

    def delete(self, *args, **kwargs):
        raise models.ProtectedError("Pembelian tidak bisa dihapus. Terbitkan VOID", [self])


class Kemasan(TimeStampedModel):
    nama     = models.CharField(max_length=40, unique=True) 
    bobot_kg = models.DecimalField(max_digits=10, decimal_places=3)
    aktif    = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_kemasan"
        ordering = ["nama"]
        verbose_name_plural = "Kemasan"
        constraints = [
            CheckConstraint(condition=Q(bobot_kg__gt=0), name="ck_kemasan_bobot_positif"),
        ]

    def __str__(self):
        return self.nama

class Packing(DiauditModel):
    class Status(models.TextChoices):
        PROGRESS = "PROCESSING", "PROCESSING"
        SELESAI  = "SELESAI",  "Selesai"


    nomor = models.CharField(
        max_length=48,
        unique=True,
        editable=False,
    )

    entitas = models.ForeignKey(
        "core.Entitas",
        on_delete=models.PROTECT,
        related_name="packing",
    )

    batch = models.ForeignKey(
        "produksi.Batch",
        on_delete=models.PROTECT,
        related_name="packing_set",
    )

    nama_hasil = models.ForeignKey(
        "master.MasterProduk",
        on_delete=models.PROTECT,
        related_name="packing_hasil",
    )

    kemasan = models.ForeignKey(
        "PoolKemasan",
        on_delete=models.PROTECT,
        related_name="packing",
    )

    total_unit = models.IntegerField()
    qty_kg = models.DecimalField(max_digits=18, decimal_places=3)
    harga_per_kg = models.DecimalField(max_digits=20, decimal_places=6, default=D0)
    cost_nom = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    menghabiskan = models.BooleanField(default=False)

    tanggal = models.DateField(default=timezone.localdate, db_index=True)
    waktu = models.DateTimeField(default=timezone.now, db_index=True)

    status = models.CharField(
        max_length=10,
        choices=StatusDokumen.choices,
        default=StatusDokumen.DRAFT,
        db_index=True,
    )

    posted_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        db_table = "inventory_packing"
        ordering = ["-waktu", "-id"]
        verbose_name_plural = "Packing"

        indexes = [
            models.Index(fields=["batch", "status"], name="ix_pack_batch"),
            models.Index(fields=["entitas", "waktu"], name="ix_pack_entitas"),
            models.Index(fields=["nama_hasil", "status"], name="ix_pack_hasil"),
        ]

        constraints = [
            CheckConstraint(condition=Q(qty_kg__gt=0), name="ck_pack_qty_positif"),
            CheckConstraint(condition=Q(total_unit__gt=0), name="ck_pack_unit_positif"),
            CheckConstraint(condition=Q(cost_nom__gte=0), name="ck_pack_nilai_non_negatif"),
        ]

    def save(self, *args, **kwargs):
        # Hitung otomatis HPP/cost_nom jika harga per kg ada dan cost_nom masih 0
        if self.harga_per_kg > 0 and self.cost_nom == D0:
            self.cost_nom = rp(self.qty_kg * self.harga_per_kg)

        if not self.nomor:
            with transaction.atomic():
                last = (
                    Packing.objects
                    .select_for_update()
                    .filter(entitas=self.entitas)
                    .order_by("-id")
                    .first()
                )
                urutan = 1
                if last and last.nomor:
                    try:
                        urutan = int(last.nomor.split("-")[-1]) + 1
                    except (ValueError, IndexError):
                        urutan = 1
                self.nomor = f"PKG-{self.entitas_id}-{urutan:03d}"
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nomor


class TipeMutasi(models.TextChoices):
    SETOR       = "SETOR",       "Setoran (pembelian raw)"
    TARIK       = "TARIK",       "Penarikan (packing barang jadi)"
    RUGI        = "RUGI",        "Beban susut produksi"
    PENYESUAIAN = "PENYESUAIAN", "Penyesuaian manual"


class MutasiKlaim(models.Model):
    entitas    = models.ForeignKey("core.Entitas", on_delete=models.PROTECT, related_name="mutasi_klaim")
    grup_bahan = models.ForeignKey("core.GrupBahan", on_delete=models.PROTECT, related_name="mutasi_klaim")
    tipe       = models.CharField(max_length=14, choices=TipeMutasi.choices)
    arah       = models.SmallIntegerField()
    qty_kg     = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    nilai      = models.DecimalField(max_digits=20, decimal_places=2)
    ref_type   = models.CharField(max_length=30)
    ref_id     = models.BigIntegerField()
    keterangan = models.TextField(blank=True, default="")
    waktu      = models.DateTimeField(db_index=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    dibuat_oleh = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", editable=False)

    class Meta:
        db_table = "inventory_mutasi_klaim"
        ordering = ["waktu", "id"]
        verbose_name_plural = "Mutasi klaim"
        indexes = [
            models.Index(fields=["entitas", "waktu", "id"], name="ix_mutasi_entitas"),
        ]
        constraints = [
            UniqueConstraint(fields=["ref_type", "ref_id", "tipe", "entitas"], name="uq_mutasi_idempoten"),
            CheckConstraint(condition=Q(arah__in=[-1, 1]), name="ck_mutasi_arah_valid"),
            CheckConstraint(condition=Q(nilai__gte=0), name="ck_mutasi_nilai_non_negatif"),
        ]

    def __str__(self):
        return f"{self.entitas.kode} {self.tipe} {self.arah:+d} {self.nilai}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("MutasiKlaim bersifat append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("MutasiKlaim tidak boleh dihapus.")


class SaldoEntitas(TimeStampedModel):
    """
    Pencatatan finansial hak/klaim per entitas terhadap total aset pool.
    """
    entitas     = models.OneToOneField("core.Entitas", on_delete=models.CASCADE, related_name="saldo_klaim")
    total_setor = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    total_tarik = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    total_rugi  = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    qty_setor   = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    qty_tarik   = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    saldo       = models.DecimalField(max_digits=20, decimal_places=2, default=D0)

    class Meta:
        db_table = "inventory_saldo_entitas"
        verbose_name_plural = "Saldo entitas"

    def __str__(self):
        return f"{self.entitas.kode}: {self.saldo}"

class PoolKemasan(TimeStampedModel):
    """
    Stok Fisik Kemasan (Pool Patungan).
    Menyimpan stok fisik packaging (botol, jerigen, kardus, dll) lintas entitas.
    Semua stok fisik untuk satu produk kemasan menyatu di sini.
    """
    produk = models.ForeignKey("master.Produk", on_delete=models.PROTECT, related_name="pool_kemasan")
    qty_unit = models.IntegerField(default=0)
    nilai = models.DecimalField(max_digits=20, decimal_places=2, default=D0)

    class Meta:
        db_table = "inventory_pool_kemasan"
        ordering = ["produk"]
        verbose_name_plural = "Pool Kemasan"
        constraints = [
            UniqueConstraint(fields=["produk"], name="inv_pool_kms_unik_per_produk"),
            CheckConstraint(condition=Q(qty_unit__gte=0), name="inv_pool_kms_qty_non_negatif"),
            CheckConstraint(condition=Q(nilai__gte=0), name="inv_pool_kms_nilai_non_negatif"),
            CheckConstraint(condition=~Q(qty_unit=0) | Q(nilai=0), name="inv_pool_kms_kosong_tanpa_nilai"),
        ]

    def __str__(self):
        return f"{self.produk.kode} - {self.produk.nama}: {self.qty_unit} Unit"

    @property
    def harga_satuan(self):
        return harga(self.nilai / Decimal(self.qty_unit)) if self.qty_unit > 0 else D0