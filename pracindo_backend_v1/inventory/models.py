"""
Persediaan tiga lapis dan buku klaim — inventory/models.py

LAPIS
    RAW   Bahan diterima, pemilik melekat lewat SaldoEntitas
    POOL  Pool produksi, TIDAK ADA pemilik sama sekali
    JADI  Barang jadi, pemilik melekat lagi setelah diklaim

Kepemilikan tidak hilang saat masuk POOL — dia berubah bentuk dari
kepemilikan fisik menjadi KLAIM. Persis seperti setoran bank: lembar
uangnya bukan milik Anda lagi, tapi Anda memegang saldo.

=========================================================================
PERUBAHAN BESAR: NILAI RIIL MELEKAT DI STOK
=========================================================================

Dulu nilai pool dihitung ulang setiap kali dibaca, dari tarif tetap
NilaiEkuivalen. Itu membuat invariant (2) mustahil dijaga: begitu satu
batch produksi berjalan, nilai bahan yang keluar dan nilai produk yang
masuk tidak pernah sama, dan selisihnya tidak ada yang menanggung.

Sekarang `Stok.nilai` menyimpan nilai rupiah yang BENAR-BENAR melekat
pada kuantitas itu. Produksi memindahkan nilai, tidak menciptakan atau
memusnahkannya:

    Bahan A  10 kg @ Rp1.000  = Rp10.000
    Bahan B  20 kg @ Rp1.500  = Rp30.000
    Bahan C   5 kg @ Rp2.000  = Rp10.000
    -------------------------------------
    Masuk    35 kg              Rp50.000      Rp1.428,57/kg
    Hasil    33 kg              Rp47.142,86   Rp1.428,57/kg
    Susut     2 kg              Rp 2.857,14   -> dibebankan

HARGA PER SATUAN TETAP. Yang susut kehilangan nilainya, tidak
menitipkannya ke produk yang selamat. Kalau sebaliknya, siapa pun yang
kebetulan mengklaim dari batch bersusut tinggi akan membayar lebih mahal
per kg -- padahal susut itu milik bersama.

Saat packaging, entitas mengklaim barang jadi senilai PORSI nilai tangki
pada saat pengambilan. Inilah yang dimaksud "klaim tergantung nominal di
tangki".

Nilai hanya HILANG lewat jalur yang menerbitkan MutasiKlaim RUGI, yang
membagi kerugian pro-rata ke pemegang klaim dalam grup:
    - susut produksi
    - sesi produksi GAGAL
    - sesi R&D yang hasilnya tidak masuk pool
    - opname kurang di lapis POOL

INVARIANT UTAMA
    (1a) SUM(SaldoEntitas.qty)   == Stok.qty    untuk RAW dan JADI
    (1b) SUM(SaldoEntitas.nilai) == Stok.nilai  untuk RAW dan JADI
    (2)  SUM(PosisiKlaim.nilai_bersih) == SUM(Stok.nilai) lapis POOL,
         per grup bahan
    (3)  saldo_akhir baris n == saldo_akhir n-1 + masuk - keluar
         (berlaku untuk qty maupun nilai)

NILAI EKUIVALEN
    Sekarang hanya BENIH, bukan sumber kebenaran. Dipakai kalau barang
    masuk pool tanpa dasar biaya sama sekali: kelebihan opname, atau
    produk R&D yang tidak berasal dari bahan mana pun. Setelah masuk,
    nilai riil yang berlaku.
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
    """
    Kuantitas FISIK beserta nilai rupiah yang melekat padanya.

    Pemilik tidak pernah disimpan di sini. Untuk RAW dan JADI, rincian
    siapa memiliki berapa ada di SaldoEntitas -- dan jumlahnya wajib sama
    dengan qty/nilai baris ini. Untuk POOL tidak ada rincian pemilik sama
    sekali; haknya ada di PosisiKlaim.
    """

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
    # Nilai rupiah yang melekat. Bergerak bersama qty, kecuali saat susut
    # produksi -- di situ qty turun dan nilai tetap.
    nilai = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
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
            models.CheckConstraint(condition=Q(nilai__gte=0),
                                   name='ck_stok_nilai_nonneg'),
            # Stok habis wajib bernilai nol. Tanpa ini, pembulatan
            # meninggalkan receh di baris kosong dan invariant (2)
            # melenceng sedikit demi sedikit tanpa ada yang sadar.
            models.CheckConstraint(condition=Q(qty__gt=0) | Q(nilai=0),
                                   name='ck_stok_kosong_tanpa_nilai'),
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

    @property
    def harga_rata(self):
        """Rupiah per satuan. Inilah tarif klaim saat barang diambil."""
        if not self.qty:
            return Decimal('0')
        return (self.nilai / self.qty).quantize(Decimal('0.0001'))


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
    """
    Append-only. Saldo berjalan qty DAN nilai tersimpan di setiap baris,
    sehingga rantai keduanya bisa diperiksa ulang kapan saja.
    """

    stok    = models.ForeignKey(Stok, on_delete=models.PROTECT, related_name='mutasi')
    urutan  = models.BigIntegerField()
    tanggal = models.DateTimeField(db_index=True)
    jenis   = models.CharField(max_length=8, choices=JenisMutasiStok.choices)

    masuk  = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                                 default=Decimal('0'))
    keluar = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
                                 default=Decimal('0'))
    saldo_akhir = models.DecimalField(max_digits=QTY_DIGITS, decimal_places=QTY_PLACES)

    nilai_masuk = models.DecimalField(max_digits=NILAI_DIGITS,
                                      decimal_places=NILAI_PLACES,
                                      default=Decimal('0'))
    nilai_keluar = models.DecimalField(max_digits=NILAI_DIGITS,
                                       decimal_places=NILAI_PLACES,
                                       default=Decimal('0'))
    saldo_nilai = models.DecimalField(max_digits=NILAI_DIGITS,
                                      decimal_places=NILAI_PLACES,
                                      default=Decimal('0'))

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
            models.CheckConstraint(
                condition=Q(nilai_masuk__gte=0) & Q(nilai_keluar__gte=0),
                name='ck_mutasi_nilai_nonneg',
            ),
            models.CheckConstraint(condition=Q(nilai_masuk=0) | Q(nilai_keluar=0),
                                   name='ck_mutasi_nilai_satu_sisi'),
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
            models.CheckConstraint(condition=Q(qty__gt=0) | Q(nilai=0),
                                   name='ck_saldo_kosong_tanpa_nilai'),
        ]

    def __str__(self):
        return f"{self.entitas.kode}: {self.qty} dari {self.stok.produk.kode}"

    @property
    def harga_rata(self):
        if not self.qty:
            return Decimal('0')
        return (self.nilai / self.qty).quantize(Decimal('0.0001'))

    def clean(self):
        if self.stok_id and self.stok.lapis == Lapis.POOL:
            raise ValidationError(
                'Lapis POOL tidak boleh punya pemilik. Pakai MutasiKlaim.'
            )


# =========================================================
# KEMASAN — jembatan satuan curah ke satuan jual
# =========================================================

class Kemasan(TimeStampedModel):
    """
    Berapa curah yang habis untuk satu unit kemasan.

    Tangki dihitung kg, barang jadi dihitung pcs. Tanpa jembatan ini,
    "10 pcs @ 1 kg" tidak punya tempat disimpan dan angka 10 kg-nya
    hanya ada di kepala operator.

        Monitor Blue curah   satuan kg
        Monitor Blue 1kg     satuan pcs,  isi = 1.000
        Monitor Blue 500g    satuan pcs,  isi = 0.500

    Konversi ini TIDAK menyentuh nilai. Rupiah tetap mengikuti kg yang
    benar-benar keluar dari tangki -- itulah sebabnya "ekuivalen terjadi
    saat klaim": tarifnya dibaca dari isi tangki pada detik pengambilan,
    bukan dari tabel harga yang disiapkan sebelumnya.
    """

    produk_curah = models.ForeignKey(
        'master.Produk', on_delete=models.PROTECT, related_name='kemasan',
        help_text='Produk yang tersimpan di tangki, satuan curah.',
    )
    produk_kemasan = models.ForeignKey(
        'master.Produk', on_delete=models.PROTECT, related_name='dari_curah',
        help_text='Produk yang keluar setelah dikemas, satuan jual.',
    )
    isi = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text='Curah yang habis untuk satu unit kemasan.',
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_kemasan'
        ordering = ['produk_curah__kode', 'isi']
        verbose_name_plural = 'Kemasan'
        constraints = [
            models.UniqueConstraint(fields=['produk_curah', 'produk_kemasan'],
                                    name='uq_kemasan_pasangan'),
            models.CheckConstraint(condition=Q(isi__gt=0), name='ck_kemasan_isi'),
        ]

    def __str__(self):
        return f"{self.produk_kemasan.kode} = {self.isi} {self.produk_curah.kode}"

    def clean(self):
        if self.produk_curah_id == self.produk_kemasan_id:
            raise ValidationError(
                {'produk_kemasan': 'Produk curah dan kemasan harus berbeda.'})

    def curah_untuk(self, jumlah):
        """Kg yang dibutuhkan untuk `jumlah` unit kemasan."""
        return (Decimal(jumlah) * self.isi).quantize(Decimal('0.001'))


# =========================================================
# NILAI EKUIVALEN & BUKU KLAIM
# =========================================================

class NilaiEkuivalen(TimeStampedModel):
    """
    BENIH nilai, bukan sumber kebenaran.

    Dipakai hanya kalau barang masuk pool tanpa dasar biaya apa pun:
    kelebihan opname, atau produk R&D yang tidak menyerap bahan. Begitu
    masuk, `Stok.nilai` yang berlaku dan tarif ini tidak dilihat lagi.

    Perubahan tarif berlaku PROSPEKTIF -- baris MutasiKlaim menyimpan
    tarif yang dipakai saat itu, jadi sejarah tidak pernah ditulis ulang.
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
    def tarif(cls, produk_id, tanggal, wajib=True):
        """
        Tarif benih pada tanggal tertentu.

        wajib=False mengembalikan 0 kalau belum ditetapkan -- dipakai di
        jalur yang boleh memasukkan barang tanpa nilai (opname lebih),
        karena qty bertambah tanpa nilai tetap menjaga invariant (2).
        """
        row = (cls.objects.filter(produk_id=produk_id, berlaku_sejak__lte=tanggal)
                          .order_by('-berlaku_sejak').first())
        if row:
            return row.nilai_per_satuan
        if not wajib:
            return Decimal('0')
        raise ValidationError(
            f'Nilai ekuivalen produk {produk_id} belum ditetapkan '
            f'untuk tanggal {tanggal}.'
        )


class JenisKlaim(models.TextChoices):
    SETOR   = 'SETOR',   'Setor bahan ke pool'
    AMBIL   = 'AMBIL',   'Klaim barang jadi'
    RUGI    = 'RUGI',    'Pembebanan kerugian pool'
    KOREKSI = 'KOREKSI', 'Koreksi'
    LUNAS   = 'LUNAS',   'Penyelesaian antar entitas'


class MutasiKlaim(models.Model):
    """
    Buku klaim, append-only.

    SETOR menambah hak entitas atas pool. AMBIL menguranginya. RUGI
    membebankan nilai yang musnah di pool, dibagi pro-rata ke pemegang
    hak positif dalam grup yang sama.

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
    # Harga per satuan yang berlaku saat baris ini terbit. Untuk SETOR:
    # harga rata bahan milik entitas. Untuk AMBIL: harga rata isi tangki
    # pool pada saat pengambilan.
    tarif = models.DecimalField(max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
                                default=Decimal('0'))

    # Positif menambah hak, negatif mengurangi.
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
    total_rugi = models.DecimalField(max_digits=NILAI_DIGITS,
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