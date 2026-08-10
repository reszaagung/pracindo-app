"""
Model fondasi — app `core`.

App ini TIDAK PERNAH mengimpor app lokal lain. Semua ketergantungan
mengarah masuk ke sini, tidak pernah keluar. Aturan itu yang menjamin
graf migrasi tetap asiklik.

Isinya empat model konkret dan dua abstract base. Target ukuran 4-6 model —
kalau lewat, kemungkinan besar ada yang salah tempat.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


# =========================================================
# ABSTRACT BASE
# =========================================================

class TimeStampedModel(models.Model):
    """Untuk master data dan model tanpa jejak pengguna."""

    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diubah_pada = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DiauditModel(TimeStampedModel):
    """Untuk model transaksional. Siapa yang membuat wajib tercatat."""

    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='+', editable=False,
    )

    class Meta:
        abstract = True


# =========================================================
# ENTITAS & POOL BAHAN
# =========================================================

class GrupBahan(TimeStampedModel):
    """
    Unit pooling bahan secara fisik. Anggota satu grup berbagi isi tanki
    sesuai spesifikasi SZA.

    Seed: PT (sendiri) dan BERSAMA (CV + Agus + Marsini).
    """

    kode = models.CharField(max_length=16, unique=True)
    nama = models.CharField(max_length=120)

    class Meta:
        db_table = 'core_grup_bahan'
        ordering = ['kode']
        verbose_name_plural = 'Grup bahan'

    def __str__(self):
        return f"{self.kode} — {self.nama}"


class JenisEntitas(models.TextChoices):
    BADAN_HUKUM = 'BADAN_HUKUM', 'Badan hukum'   # PT, CV
    PERORANGAN  = 'PERORANGAN',  'Perorangan'    # Agus, Marsini


class Entitas(TimeStampedModel):
    """
    Unit PEMBUKUAN. Setiap entitas punya set buku yang seimbang sendiri.

    Perhatikan bedanya dengan GrupBahan: entitas menjawab "siapa yang
    berhutang dan memiliki modal", grup bahan menjawab "bahan siapa
    bercampur dengan bahan siapa di tanki". Dua sumbu berbeda.
    """

    kode  = models.CharField(max_length=8, unique=True)
    nama  = models.CharField(max_length=120)
    jenis = models.CharField(max_length=12, choices=JenisEntitas.choices)
    npwp  = models.CharField(max_length=20, blank=True)

    grup_bahan = models.ForeignKey(
        GrupBahan, on_delete=models.PROTECT, related_name='entitas',
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_entitas'
        ordering = ['kode']
        verbose_name_plural = 'Entitas'

    def __str__(self):
        return f"{self.kode} — {self.nama}"

    @property
    def pkp(self):
        """Pengusaha Kena Pajak. Menentukan apakah modul pajak berlaku."""
        return bool(self.npwp)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Entitas tidak boleh dihapus. Set aktif=False sebagai gantinya.'
        )


# =========================================================
# PENOMORAN DOKUMEN
# =========================================================

class CounterDokumen(models.Model):
    """
    Penomoran atomik per entitas, per jenis dokumen, per bulan.

    Melayani nomor PO dan jurnal (akunting), GRN dan BAS (warehouse),
    voucher bayar (keuangan), serta sesi produksi. Tidak ada satu app pun
    yang berhak mengklaimnya -- itu sebabnya dia tinggal di core.

    KENAPA MENYIMPAN COUNTER, BUKAN count()+1

    count() menghitung baris yang ADA, bukan nomor yang pernah TERPAKAI.
    Kalau PO ke-7 dihapus, count() kembali jadi 6 dan PO berikutnya
    mendapat nomor 007 lagi -- bentrok dengan unique constraint, atau
    lebih buruk, dokumen ganda kalau constraint belum terpasang.

    Baris counter di sini hanya bertambah. Nomor terpakai tidak pernah
    kembali, bahkan setelah dokumennya dihapus atau dibatalkan.

    TIDAK dipakai untuk nomor faktur pajak -- itu diatur DJP dan
    dikelola app `pajak`.
    """

    entitas = models.ForeignKey(Entitas, on_delete=models.PROTECT)
    jenis   = models.CharField(max_length=16)   # PO | GRN | FAKTUR | JURNAL | BAS | SESI
    periode = models.CharField(max_length=6)    # YYYYMM
    urutan  = models.PositiveIntegerField(default=0)

    BULAN_ROMAWI = [
        'I', 'II', 'III', 'IV', 'V', 'VI',
        'VII', 'VIII', 'IX', 'X', 'XI', 'XII',
    ]

    # Lebar nomor urut per jenis dokumen. Default 3 digit.
    LEBAR = {
        'JURNAL': 4,    # jurnal jauh lebih banyak per bulan
    }

    class Meta:
        db_table = 'core_counter_dokumen'
        ordering = ['entitas', 'jenis', '-periode']
        verbose_name_plural = 'Counter dokumen'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'jenis', 'periode'],
                name='uq_counter_dokumen',
            ),
        ]

    def __str__(self):
        return f"{self.jenis}/{self.entitas.kode}/{self.periode} = {self.urutan}"

    # ---------- format ----------

    @classmethod
    def format_nomor(cls, entitas, jenis, tanggal, urutan):
        """
        Format rumah Pracindo:  PO/PCJM/2026/VIII/001

        Bulan memakai angka Romawi, bukan digit -- membedakan sekilas
        antara komponen tahun dan bulan tanpa harus menghitung posisi.
        """
        romawi = cls.BULAN_ROMAWI[tanggal.month - 1]
        lebar = cls.LEBAR.get(jenis, 3)
        return f"{jenis}/{entitas.kode}/{tanggal.year}/{romawi}/{urutan:0{lebar}d}"

    # ---------- penomoran ----------

    @classmethod
    def berikutnya(cls, entitas, jenis, tanggal):
        """
        WAJIB dipanggil di dalam transaction.atomic().

        select_for_update() menyerialkan penomoran per counter -- dua PO
        bersamaan di entitas dan bulan yang sama akan antre, bukan dapat
        nomor kembar. Counter untuk entitas atau jenis berbeda tidak
        saling mengunci, jadi PT dan CV bisa membuat PO bersamaan tanpa
        saling tunggu.

        Rollback transaksi ikut mengembalikan counter, jadi tidak ada
        nomor yang terlewat.
        """
        periode = tanggal.strftime('%Y%m')
        counter, _ = cls.objects.select_for_update().get_or_create(
            entitas=entitas, jenis=jenis, periode=periode,
        )
        counter.urutan += 1
        counter.save(update_fields=['urutan'])
        return cls.format_nomor(entitas, jenis, tanggal, counter.urutan)

    @classmethod
    def preview(cls, entitas, jenis, tanggal):
        """
        Preview SAJA, tanpa lock dan tanpa menaikkan counter.

        Angka final bisa bergeser kalau ada dokumen lain dibuat di antara
        preview dan submit. berikutnya() yang jadi sumber kebenaran.
        """
        periode = tanggal.strftime('%Y%m')
        counter = cls.objects.filter(
            entitas=entitas, jenis=jenis, periode=periode,
        ).first()
        urutan = (counter.urutan if counter else 0) + 1
        return cls.format_nomor(entitas, jenis, tanggal, urutan)


# =========================================================
# PERIODE AKUNTANSI
# =========================================================

class PeriodeAkuntansi(TimeStampedModel):
    """
    Penguncian periode. Dicek oleh warehouse.terima_barang(),
    akunting.posting(), keuangan.post_mutasi(), dan penyesuaian stok.

    Ditutup per entitas, bukan global — PT bisa tutup Juli sementara
    CV belum. Koreksi atas periode tertutup dilakukan lewat jurnal balik
    bertanggal periode berjalan, bukan dengan membuka periode lama.
    """

    entitas = models.ForeignKey(
        Entitas, on_delete=models.PROTECT, related_name='periode',
    )
    tahun = models.PositiveSmallIntegerField()
    bulan = models.PositiveSmallIntegerField()

    ditutup      = models.BooleanField(default=False, db_index=True)
    ditutup_pada = models.DateTimeField(null=True, blank=True, editable=False)
    ditutup_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name='+', editable=False,
    )
    alasan_buka = models.TextField(blank=True)

    class Meta:
        db_table = 'core_periode_akuntansi'
        ordering = ['-tahun', '-bulan']
        verbose_name_plural = 'Periode akuntansi'
        constraints = [
            models.UniqueConstraint(
                fields=['entitas', 'tahun', 'bulan'],
                name='uq_periode_entitas',
            ),
            models.CheckConstraint(
                check=Q(bulan__gte=1) & Q(bulan__lte=12),
                name='ck_periode_bulan_valid',
            ),
        ]
        indexes = [
            models.Index(
                fields=['entitas', 'tahun', 'bulan', 'ditutup'],
                name='ix_periode_lookup',
            ),
        ]

    def __str__(self):
        status = 'tertutup' if self.ditutup else 'terbuka'
        return f"{self.entitas.kode} {self.bulan:02d}/{self.tahun} ({status})"
