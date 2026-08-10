"""
Persediaan tiga lapis dan buku klaim — inventory/models.py

LAPIS
    RAW   Bahan diterima, pemilik melekat lewat SaldoEntitas
    POOL  Pool produksi, TIDAK ADA pemilik sama sekali
    JADI  Barang jadi, pemilik melekat lagi setelah diklaim

Kepemilikan tidak hilang saat masuk POOL — dia berubah bentuk dari
kepemilikan fisik menjadi KLAIM. Persis seperti setoran bank: lembar
uangnya bukan milik Anda lagi, tapi Anda memegang saldo.

INVARIANT UTAMA
    SUM(PosisiKlaim.nilai_bersih untuk satu grup) == nilai sisa POOL

Kalau melenceng, perhitungan siapa berhutang ke siapa sudah salah tanpa
ada error yang muncul.

NILAI EKUIVALEN
    Tarif tetap per produk, bukan harga pasar. Dipakai menyetarakan barang
    yang berbeda jenis supaya posisi multi-produk runtuh jadi satu angka.
    Tarif yang dipakai DISIMPAN di setiap baris MutasiKlaim, sehingga
    perubahan tarif di kemudian hari tidak menulis ulang sejarah.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from core.constants import NILAI_DIGITS, NILAI_PLACES, QTY_DIGITS, QTY_PLACES
from core.models import TimeStampedModel


class Lapis(models.TextChoices):
    RAW  = 'RAW',  'Bahan bertuan'
    POOL = 'POOL', 'Pool produksi'
    JADI = 'JADI', 'Barang jadi'


# =========================================================
# TANGKI & STOK FISIK
# =========================================================

class Tangki(TimeStampedModel):
    kode = models.CharField(max_length=16, unique=True)
    nama = models.CharField(max_length=120)

    grup_bahan = models.ForeignKey(
        'core.GrupBahan', on_delete=models.PROTECT, related_name='tangki',
    )
    kapasitas_kg = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES)
    isi_kg = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )
    # Satu tangki hanya boleh berisi satu produk. Mencampur dua produk
    # berbeda tidak bisa dibatalkan.
    produk_terisi = models.ForeignKey(
        'master.Produk', null=True, blank=True,
        on_delete=models.PROTECT, related_name='+', editable=False,
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_tangki'
        ordering = ['kode']
        verbose_name_plural = 'Tangki'
        constraints = [
            models.CheckConstraint(condition=Q(kapasitas_kg__gt=0),
                                   name='ck_tangki_kapasitas'),
            models.CheckConstraint(
                condition=Q(isi_kg__gte=0) & Q(isi_kg__lte=models.F('kapasitas_kg')),
                name='ck_tangki_isi_dalam_kapasitas',
            ),
        ]

    def __str__(self):
        return f"{self.kode} - {self.nama}"

    @property
    def ruang_kosong_kg(self):
        return self.kapasitas_kg - self.isi_kg

    @property
    def persen_terisi(self):
        if not self.kapasitas_kg:
            return Decimal('0')
        return (self.isi_kg / self.kapasitas_kg * 100).quantize(Decimal('0.1'))


class Stok(TimeStampedModel):
    """Kuantitas FISIK. Pemilik tidak pernah disimpan di sini."""

    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                               related_name='stok')
    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT,
                                   related_name='stok')
    lapis = models.CharField(max_length=4, choices=Lapis.choices, db_index=True)
    tangki = models.ForeignKey(Tangki, null=True, blank=True,
                               on_delete=models.PROTECT, related_name='stok')

    qty = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )
    urutan_terakhir = models.BigIntegerField(default=0, editable=False)

    class Meta:
        db_table = 'inventory_stok'
        ordering = ['lapis', 'produk__kode']
        verbose_name_plural = 'Stok'
        constraints = [
            models.UniqueConstraint(
                fields=['produk', 'grup_bahan', 'lapis', 'tangki'],
                condition=Q(tangki__isnull=False), name='uq_stok_tangki',
            ),
            models.UniqueConstraint(
                fields=['produk', 'grup_bahan', 'lapis'],
                condition=Q(tangki__isnull=True), name='uq_stok_rak',
            ),
            models.CheckConstraint(condition=Q(qty__gte=0), name='ck_stok_nonneg'),
        ]
        indexes = [
            models.Index(fields=['grup_bahan', 'lapis'], name='ix_stok_grup_lapis'),
        ]

    def __str__(self):
        return f"[{self.lapis}] {self.produk.kode} @ {self.grup_bahan.kode} = {self.qty}"

    @property
    def berpemilik(self):
        """POOL tidak pernah punya SaldoEntitas."""
        return self.lapis in (Lapis.RAW, Lapis.JADI)


class JenisMutasiStok(models.TextChoices):
    TERIMA = 'TERIMA', 'Penerimaan barang'
    SETOR  = 'SETOR',  'Setor ke pool'
    PAKAI  = 'PAKAI',  'Pemakaian produksi'
    HASIL  = 'HASIL',  'Hasil produksi'
    KLAIM  = 'KLAIM',  'Klaim barang jadi'
    KIRIM  = 'KIRIM',  'Pengiriman'
    RETUR  = 'RETUR',  'Retur'
    OPNAME = 'OPNAME', 'Penyesuaian opname'
    SUSUT  = 'SUSUT',  'Susut / penguapan'


class MutasiStok(models.Model):
    """Append-only, saldo berjalan tersimpan di setiap baris."""

    stok    = models.ForeignKey(Stok, on_delete=models.PROTECT, related_name='mutasi')
    urutan  = models.BigIntegerField()
    tanggal = models.DateTimeField(db_index=True)
    jenis   = models.CharField(max_length=8, choices=JenisMutasiStok.choices)

    masuk  = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                                 default=Decimal('0'))
    keluar = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                                 default=Decimal('0'))
    saldo_akhir = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES)

    referensi = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=96, unique=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_mutasi_stok'
        ordering = ['stok', 'urutan']
        verbose_name_plural = 'Mutasi stok'
        constraints = [
            models.UniqueConstraint(fields=['stok', 'urutan'],
                                    name='uq_mutasi_stok_urutan'),
            models.CheckConstraint(condition=Q(masuk__gte=0) & Q(keluar__gte=0),
                                   name='ck_mutasi_stok_nonneg'),
            models.CheckConstraint(condition=Q(masuk=0) | Q(keluar=0),
                                   name='ck_mutasi_stok_satu_sisi'),
        ]
        indexes = [models.Index(fields=['stok', '-urutan'], name='ix_mutasi_stok_urut')]

    def __str__(self):
        arah = f"+{self.masuk}" if self.masuk else f"-{self.keluar}"
        return f"{self.stok.produk.kode} {arah} = {self.saldo_akhir}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('MutasiStok append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('MutasiStok append-only.')


class SaldoEntitas(TimeStampedModel):
    """
    Kepemilikan fisik. HANYA untuk lapis RAW dan JADI.

    Untuk lapis POOL, kepemilikan ada di PosisiKlaim, bukan di sini.
    """

    stok    = models.ForeignKey(Stok, on_delete=models.PROTECT,
                                related_name='kepemilikan')
    entitas = models.ForeignKey('core.Entitas', on_delete=models.PROTECT,
                                related_name='saldo_bahan')

    qty = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                              default=Decimal('0'), editable=False)
    nilai = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                default=Decimal('0'), editable=False)

    class Meta:
        db_table = 'inventory_saldo_entitas'
        ordering = ['stok', 'entitas__kode']
        verbose_name_plural = 'Saldo entitas'
        constraints = [
            models.UniqueConstraint(fields=['stok', 'entitas'],
                                    name='uq_saldo_entitas'),
            models.CheckConstraint(condition=Q(qty__gte=0),
                                   name='ck_saldo_entitas_nonneg'),
        ]

    def __str__(self):
        return f"{self.entitas.kode}: {self.qty} dari {self.stok.produk.kode}"

    def clean(self):
        if self.stok_id and self.stok.lapis == Lapis.POOL:
            raise ValidationError(
                'Lapis POOL tidak boleh punya pemilik. Pakai MutasiKlaim.'
            )


# =========================================================
# NILAI EKUIVALEN & BUKU KLAIM
# =========================================================

class NilaiEkuivalen(TimeStampedModel):
    """
    Tarif tetap penyetaraan antar produk. BUKAN harga pasar.

    Contoh: gula 1 per gram, teh celup 50 per pcs. Dengan ini setoran
    35 g gula dan pengambilan 12 teh kemasan bisa dibandingkan langsung.

    Perubahan tarif berlaku PROSPEKTIF — baris MutasiKlaim menyimpan tarif
    yang dipakai saat itu, jadi sejarah tidak pernah ditulis ulang.
    """

    produk = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                               related_name='nilai_ekuivalen')
    nilai_per_satuan = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    berlaku_sejak = models.DateField()
    catatan = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'inventory_nilai_ekuivalen'
        ordering = ['produk__kode', '-berlaku_sejak']
        verbose_name_plural = 'Nilai ekuivalen'
        constraints = [
            models.UniqueConstraint(fields=['produk', 'berlaku_sejak'],
                                    name='uq_ekuivalen_produk_tanggal'),
        ]

    def __str__(self):
        return f"{self.produk.kode} = {self.nilai_per_satuan}/{self.produk.satuan.kode}"

    @classmethod
    def tarif(cls, produk_id, tanggal):
        """Tarif yang berlaku pada tanggal tertentu. Raise kalau belum ada."""
        row = (cls.objects.filter(produk_id=produk_id, berlaku_sejak__lte=tanggal)
                          .order_by('-berlaku_sejak').first())
        if not row:
            raise ValidationError(
                f'Nilai ekuivalen produk {produk_id} belum ditetapkan '
                f'untuk tanggal {tanggal}.'
            )
        return row.nilai_per_satuan


class JenisKlaim(models.TextChoices):
    SETOR   = 'SETOR',   'Setor bahan ke pool'
    AMBIL   = 'AMBIL',   'Klaim barang jadi'
    KOREKSI = 'KOREKSI', 'Koreksi'
    LUNAS   = 'LUNAS',   'Penyelesaian antar entitas'


class MutasiKlaim(models.Model):
    """
    Buku klaim, append-only.

    SETOR menambah hak entitas atas pool. AMBIL menguranginya.
    Posisi bersih negatif berarti entitas itu mengambil lebih banyak
    daripada yang disetor -- dia berhutang ke entitas lain dalam grup.
    """

    entitas    = models.ForeignKey('core.Entitas', on_delete=models.PROTECT,
                                   related_name='klaim')
    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT,
                                   related_name='klaim')
    tanggal = models.DateField(db_index=True)
    jenis   = models.CharField(max_length=8, choices=JenisKlaim.choices)

    produk = models.ForeignKey('master.Produk', null=True, blank=True,
                               on_delete=models.PROTECT, related_name='klaim')
    qty = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                              default=Decimal('0'))
    tarif = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                default=Decimal('0'))

    # Positif menambah hak, negatif mengurangi. qty x tarif, bertanda.
    nilai = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES)

    referensi = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=96, unique=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_mutasi_klaim'
        ordering = ['grup_bahan', 'tanggal', 'id']
        verbose_name_plural = 'Mutasi klaim'
        indexes = [
            models.Index(fields=['grup_bahan', 'entitas', 'tanggal'],
                         name='ix_klaim_grup_ent'),
        ]

    def __str__(self):
        return f"{self.entitas.kode} {self.get_jenis_display()} {self.nilai:+}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('MutasiKlaim append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('MutasiKlaim append-only. Terbitkan KOREKSI.')


class PosisiKlaim(TimeStampedModel):
    """
    Cache posisi bersih per entitas per grup. Sumber kebenarannya tetap
    MutasiKlaim -- ini hanya supaya membaca posisi = baca satu kolom.

    nilai_bersih negatif = entitas berhutang ke grup.
    """

    entitas    = models.ForeignKey('core.Entitas', on_delete=models.PROTECT,
                                   related_name='posisi_klaim')
    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT,
                                   related_name='posisi_klaim')

    total_setor = models.DecimalField(max_digits=NILAI_DIGITS,
                                      decimal_places=NILAI_PLACES,
                                      default=Decimal('0'), editable=False)
    total_ambil = models.DecimalField(max_digits=NILAI_DIGITS,
                                      decimal_places=NILAI_PLACES,
                                      default=Decimal('0'), editable=False)
    nilai_bersih = models.DecimalField(max_digits=NILAI_DIGITS,
                                       decimal_places=NILAI_PLACES,
                                       default=Decimal('0'), editable=False)

    class Meta:
        db_table = 'inventory_posisi_klaim'
        ordering = ['grup_bahan', 'entitas__kode']
        verbose_name_plural = 'Posisi klaim'
        constraints = [
            models.UniqueConstraint(fields=['entitas', 'grup_bahan'],
                                    name='uq_posisi_klaim'),
        ]

    def __str__(self):
        arah = 'berhutang' if self.nilai_bersih < 0 else 'berpiutang'
        return f"{self.entitas.kode} {arah} {abs(self.nilai_bersih)}"

    @property
    def berhutang(self):
        return self.nilai_bersih < 0
