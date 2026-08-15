"""
Model produksi — produksi/models.py

INVARIANT DITEGAKKAN DI DATABASE, BUKAN HANYA DI PYTHON

    P1  nilai_hasil + nilai_susut == total_nilai_input
    P2  qty_hasil   + tekor_kg    == total_qty_input

    Keduanya juga diperiksa di services.posting_batch(), tapi Python
    hanya menjaga satu pintu. Shell, admin, skrip impor, dan migrasi data
    adalah pintu-pintu lain -- dan invariant tidak peduli lewat mana
    angkanya berubah. Constraint di bawah menutup semuanya sekaligus.

    Keduanya dikecualikan untuk DRAFT: tekor_kg sudah diisi saat draft
    sementara qty_hasil masih nol, jadi P2 memang belum boleh berlaku.

NAMA CONSTRAINT DIPREFIKS

    Nama constraint harus unik di SELURUH database, bukan per app.
    'tekor_non_negatif' akan bertabrakan begitu inventory punya nama yang
    sama, dan tabrakannya baru terlihat saat migrate -- setelah kedua app
    selesai ditulis.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.db.models.functions import Upper
from django.utils import timezone

D0 = Decimal("0")


class Tangki(models.Model):
    kode  = models.CharField(max_length=20, unique=True)
    nama  = models.CharField(max_length=80, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["kode"]
        constraints = [

            CheckConstraint(check=Q(kode=Upper("kode")),
                            name="produksi_tangki_kode_uppercase"),
        ]

    def save(self, *args, **kwargs):
        if self.kode:
            self.kode = self.kode.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.kode


class JenisBatch(models.TextChoices):
    MIXING   = "MIXING",   "Mixing (raw → tangki)"
    BLENDING = "BLENDING", "Blending (WIP ± raw → tangki)"


class StatusBatch(models.TextChoices):
    DRAFT  = "DRAFT",  "Draft"
    POSTED = "POSTED", "Diposting"
    VOID   = "VOID",   "Dibatalkan"


class Batch(models.Model):
    nomor      = models.CharField(max_length=30, unique=True)
    jenis      = models.CharField(max_length=10, choices=JenisBatch.choices,
                                  default=JenisBatch.MIXING)
    nama_hasil = models.CharField(max_length=120)
    tangki     = models.ForeignKey(Tangki, on_delete=models.PROTECT,
                                   related_name="batch_set")
    waktu      = models.DateTimeField(default=timezone.now, db_index=True)

    total_qty_input   = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    total_nilai_input = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    tekor_kg          = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    nilai_susut       = models.DecimalField(max_digits=20, decimal_places=2, default=D0)

    qty_hasil          = models.DecimalField(max_digits=18, decimal_places=3, default=D0)
    nilai_hasil        = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    harga_masuk_per_kg = models.DecimalField(max_digits=20, decimal_places=6, default=D0)
    harga_hasil_per_kg = models.DecimalField(max_digits=20, decimal_places=6, default=D0)

    status  = models.CharField(max_length=8, choices=StatusBatch.choices,
                               default=StatusBatch.DRAFT, db_index=True)
    catatan = models.TextField(blank=True, default="")
    posting_key = models.CharField(max_length=64, null=True, blank=True,
                                   unique=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name="batch_dibuat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name="batch_diposting")
    posted_at  = models.DateTimeField(null=True, blank=True)
    grup_bahan = models.ForeignKey("core.GrupBahan", on_delete=models.PROTECT,
                                   related_name="batch")

    class Meta:
        ordering = ["-waktu", "-id"]
        verbose_name_plural = "Batch"
        indexes = [
            models.Index(fields=["tangki", "status", "waktu"],
                         name="prod_batch_tangki_idx"),
            models.Index(fields=["status", "waktu"],
                         name="prod_batch_status_idx"),
        ]
        constraints = [
            CheckConstraint(
                check=Q(status=StatusBatch.DRAFT) | Q(qty_hasil__gt=0),
                name="produksi_batch_posted_hasil_positif"),
            CheckConstraint(
                check=Q(tekor_kg__gte=0),
                name="produksi_batch_tekor_non_negatif"),
            CheckConstraint(
                check=Q(nilai_susut__gte=0),
                name="produksi_batch_susut_non_negatif"),

            CheckConstraint(
                check=Q(status=StatusBatch.DRAFT)
                      | Q(total_nilai_input=F("nilai_hasil") + F("nilai_susut")),
                name="produksi_batch_p1_konservasi_nilai"),

            CheckConstraint(
                check=Q(status=StatusBatch.DRAFT)
                      | Q(total_qty_input=F("qty_hasil") + F("tekor_kg")),
                name="produksi_batch_p2_konservasi_massa"),

            CheckConstraint(
                check=~Q(status=StatusBatch.POSTED)
                      | (Q(posted_at__isnull=False)),
                name="produksi_batch_posted_ada_jejak"),
        ]

    def __str__(self):
        return self.nomor

    def saldo(self):
        """Impor lokal: services mengimpor models, jadi tidak di atas."""
        from .services import saldo_batch
        return saldo_batch(self)


class BatchInputRaw(models.Model):
    """Konsumsi dari pool raw material."""
    batch  = models.ForeignKey(Batch, on_delete=models.CASCADE,
                               related_name="input_raw")
    produk = models.ForeignKey("master.Produk", on_delete=models.PROTECT,
                               related_name="dipakai_produksi")

    qty_kg       = models.DecimalField(max_digits=18, decimal_places=3)
    harga_per_kg = models.DecimalField(max_digits=20, decimal_places=6,
                                       default=Decimal("0"))
    nilai        = models.DecimalField(max_digits=20, decimal_places=2,
                                       default=Decimal("0"))
    menghabiskan = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            UniqueConstraint(fields=["batch", "produk"],
                             name="produksi_produk_unik_per_batch"),
            CheckConstraint(condition=Q(qty_kg__gt=0),
                            name="produksi_input_raw_qty_positif"),
            CheckConstraint(condition=Q(nilai__gte=0),
                            name="produksi_input_raw_nilai_non_negatif"),
        ]

    def __str__(self):
        return f"{self.batch_id}:{self.produk_id}"


class TransferWip(models.Model):
    """
    Perpindahan WIP antar tangki.

    Menyimpannya di sini, bukan sebagai baris packing, membuat seluruh
    kelas bug lama mustahil secara struktural: buku klaim tidak punya
    akses ke tabel ini, jadi dia tidak bisa salah membacanya sebagai
    penarikan hak.
    """
    batch_tujuan = models.ForeignKey(Batch, on_delete=models.CASCADE,
                                     related_name="input_wip")
    batch_sumber = models.ForeignKey(Batch, on_delete=models.PROTECT,
                                     related_name="keluar_wip")
    qty_kg       = models.DecimalField(max_digits=18, decimal_places=3)
    harga_per_kg = models.DecimalField(max_digits=20, decimal_places=6, default=D0)
    nilai        = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    menghabiskan = models.BooleanField(default=False)
    waktu        = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["id"]
        constraints = [
            UniqueConstraint(fields=["batch_tujuan", "batch_sumber"],
                             name="produksi_sumber_unik_per_batch"),
            CheckConstraint(check=~Q(batch_tujuan=F("batch_sumber")),
                            name="produksi_tidak_transfer_ke_diri_sendiri"),
            CheckConstraint(check=Q(qty_kg__gt=0),
                            name="produksi_input_wip_qty_positif"),
            CheckConstraint(check=Q(nilai__gte=0),
                            name="produksi_input_wip_nilai_non_negatif"),
        ]

    def __str__(self):
        return f"{self.batch_sumber_id} → {self.batch_tujuan_id}"


class SekuensBatch(models.Model):
    awalan   = models.CharField(max_length=10, primary_key=True)   
    periode  = models.CharField(max_length=6)                      
    terakhir = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Sekuens Batch"

    def __str__(self):
        return f"{self.awalan}-{self.periode}: {self.terakhir}"


def nomor_baru(awalan, periode):
    """
    MX-202608-0001, BD-202608-0001, dst.

    get_or_create dan select_for_update DIPISAH dengan sengaja.
    `objects.select_for_update().get_or_create()` tidak mengunci apa pun
    di jalur create -- dua transaksi yang sama-sama membuat baris baru
    lolos berdampingan, dan keduanya mengembalikan nomor 0001.

    Nomor bisa berlubang kalau transaksi luar di-rollback. Itu memang
    konsekuensinya, dan lubang jauh lebih murah daripada tabrakan.
    """
    with transaction.atomic():
        SekuensBatch.objects.get_or_create(
            awalan=awalan, defaults={"periode": periode, "terakhir": 0})
        s = SekuensBatch.objects.select_for_update().get(pk=awalan)
        if s.periode != periode:
            s.periode, s.terakhir = periode, 0
        s.terakhir += 1
        s.save(update_fields=["periode", "terakhir"])
        return f"{awalan}-{periode}-{s.terakhir:04d}"