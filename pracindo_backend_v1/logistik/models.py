"""
Pengiriman dan bukti terima — logistik/models.py

BATAS MODUL YANG TIDAK BOLEH DILANGGAR

    logistik TIDAK PERNAH MENULIS STOK.

Rantainya: sales_order -> akunting -> warehouse -> logistik -> kurir.
Saat sebuah Distribusi sampai ke logistik, stok SUDAH berkurang di warehouse.
Kalau logistik ikut mengurangi, angkanya berkurang dua kali dan tidak ada
error yang muncul -- selisihnya baru ketahuan saat opname, dan saat itu tidak
ada yang bisa menelusuri jalur mana yang salah.

Rujukan ke Distribusi memakai INTEGER, bukan ForeignKey, karena aturan impor
satu arah di repo ini melarang logistik mengimpor model warehouse. Semua
percakapan dengan warehouse lewat integrasi_warehouse.py.

STIKER SUDAH MENUTUP KLAIM
    Barang yang sampai di sini sudah berstiker, dan barang berstiker tidak
    bisa diklaim lagi. Atribusi badan hukum selesai di hulu. Karena itu tidak
    ada MutasiKlaim di modul ini, dan logistik tidak punya cara merusak
    invariant konservasi nilai.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.models import CounterDokumen, DiauditModel, TimeStampedModel


# =========================================================
# ACUAN
# =========================================================

class Kendaraan(TimeStampedModel):
    kode = models.CharField(max_length=16, unique=True)
    nama = models.CharField(max_length=120)
    plat_nomor = models.CharField(max_length=16, blank=True)
    kapasitas_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'logistik_kendaraan'
        ordering = ['kode']
        verbose_name_plural = 'Kendaraan'

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class TarifOngkos(TimeStampedModel):
    """
    Tarif berversi tanggal. Perkiraan ongkos lama TIDAK ikut berubah saat
    tarif naik -- perkiraan yang disimpan di Pengiriman adalah angka pada
    saat perjalanan itu, bukan hasil hitung ulang.
    """
    berlaku_sejak = models.DateField(default=timezone.localdate)
    tarif_per_km = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))])
    biaya_tetap = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))])

    class Meta:
        db_table = 'logistik_tarif_ongkos'
        ordering = ['-berlaku_sejak']
        verbose_name_plural = 'Tarif ongkos'

    def __str__(self):
        return f"Rp {self.tarif_per_km}/km sejak {self.berlaku_sejak}"

    @classmethod
    def berlaku(cls, tanggal=None):
        tanggal = tanggal or timezone.localdate()
        return cls.objects.filter(berlaku_sejak__lte=tanggal).first()


# =========================================================
# PENGIRIMAN
# =========================================================

class StatusPengiriman(models.TextChoices):
    DISIAPKAN = 'DISIAPKAN', 'Disiapkan'
    BERANGKAT = 'BERANGKAT', 'Berangkat'
    SELESAI   = 'SELESAI',   'Selesai'
    BATAL     = 'BATAL',     'Dibatalkan'


class Pengiriman(DiauditModel):
    """
    Satu perjalanan kurir. Bisa membawa muatan beberapa pelanggan sekaligus,
    dan muatan itu boleh milik badan hukum berbeda -- stiker sudah menutup
    klaimnya masing-masing, jadi tidak ada yang perlu diselesaikan di sini.

    `entitas` di sini adalah pemilik ARMADA, bukan pemilik barang. Dipakai
    untuk penomoran dan pembebanan biaya perjalanan.
    """

    nomor = models.CharField(max_length=32, editable=False)
    entitas = models.ForeignKey(
        'core.Entitas', on_delete=models.PROTECT, related_name='pengiriman')
    tanggal = models.DateField(default=timezone.localdate, db_index=True)

    kurir = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pengiriman_dibawa')
    kendaraan = models.ForeignKey(
        Kendaraan, null=True, blank=True,
        on_delete=models.PROTECT, related_name='pengiriman')

    status = models.CharField(
        max_length=12, choices=StatusPengiriman.choices,
        default=StatusPengiriman.DISIAPKAN, db_index=True)

    waktu_berangkat = models.DateTimeField(null=True, blank=True, editable=False)
    waktu_selesai = models.DateTimeField(null=True, blank=True, editable=False)

    jarak_total_km = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0'))
    # Disimpan, bukan dihitung ulang saat dibaca. Tarif bisa berubah, dan
    # perkiraan yang berubah sendiri setelah perjalanan selesai tidak bisa
    # dibandingkan dengan biaya sebenarnya.
    ongkos_perkiraan = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'))

    catatan = models.TextField(blank=True)

    class Meta:
        db_table = 'logistik_pengiriman'
        ordering = ['-tanggal', '-id']
        constraints = [
            models.UniqueConstraint(fields=['entitas', 'nomor'],
                                    name='uq_pengiriman_nomor'),
        ]
        indexes = [
            models.Index(fields=['kurir', 'status', '-tanggal'],
                         name='ix_kirim_kurir_status'),
            models.Index(fields=['status', '-tanggal'],
                         name='ix_kirim_status'),
        ]

    def __str__(self):
        return f"{self.nomor} - {self.kurir}"

    @property
    def jumlah_perhentian(self):
        return self.perhentian.count()

    @property
    def semua_perhentian_tuntas(self):
        return not self.perhentian.filter(
            status__in=[StatusPerhentian.MENUNGGU, StatusPerhentian.SAMPAI]
        ).exists()

    def save(self, *args, **kwargs):
        if not self.nomor:
            self.nomor = CounterDokumen.berikutnya(
                self.entitas, 'KIRIM', self.tanggal)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != StatusPengiriman.DISIAPKAN:
            raise ValidationError(
                'Pengiriman yang sudah berangkat tidak bisa dihapus.')
        return super().delete(*args, **kwargs)


class StatusPerhentian(models.TextChoices):
    MENUNGGU = 'MENUNGGU', 'Menunggu'
    SAMPAI   = 'SAMPAI',   'Sampai di lokasi'
    DITERIMA = 'DITERIMA', 'Diterima'
    DIRETUR  = 'DIRETUR',  'Diretur'


class Perhentian(models.Model):
    """
    Satu tujuan dalam perjalanan, mewakili satu Distribusi dari warehouse.

    `urutan` dan `urutan_usulan` disimpan TERPISAH dengan sengaja. Setelah
    beberapa bulan, selisih keduanya menunjukkan seberapa sering usulan
    sistem ditolak kurir -- dan itu satu-satunya cara mengetahui apakah
    optimasi rute benar-benar berguna atau cuma diabaikan.
    """

    pengiriman = models.ForeignKey(
        Pengiriman, on_delete=models.CASCADE, related_name='perhentian')

    # Rujukan lintas app: INTEGER, bukan FK. Lihat catatan kepala berkas.
    distribusi_id = models.PositiveIntegerField(db_index=True)
    # Salinan untuk tampilan, diambil sekali saat perakitan. Disalin supaya
    # riwayat perjalanan tetap terbaca walau data hulu berubah kemudian.
    nomor_distribusi = models.CharField(max_length=32, blank=True)
    pelanggan_nama = models.CharField(max_length=200, blank=True)

    urutan = models.PositiveSmallIntegerField(default=1)
    urutan_usulan = models.PositiveSmallIntegerField(null=True, blank=True)

    alamat = models.TextField(blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    jarak_dari_sebelum_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'))
    estimasi_menit = models.PositiveSmallIntegerField(default=0)

    status = models.CharField(
        max_length=10, choices=StatusPerhentian.choices,
        default=StatusPerhentian.MENUNGGU, db_index=True)
    waktu_sampai = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        db_table = 'logistik_perhentian'
        ordering = ['pengiriman', 'urutan']
        constraints = [
            models.UniqueConstraint(fields=['pengiriman', 'distribusi_id'],
                                    name='uq_perhentian_distribusi'),
        ]

    def __str__(self):
        return f"{self.urutan}. {self.pelanggan_nama or self.nomor_distribusi}"

    @property
    def tuntas(self):
        return self.status in (StatusPerhentian.DITERIMA, StatusPerhentian.DIRETUR)


# =========================================================
# PELACAKAN
# =========================================================

class JejakPosisi(models.Model):
    """
    Titik posisi kurir. HANYA direkam saat pengiriman berstatus BERANGKAT --
    di luar itu perekaman ditolak service, bukan cuma tidak dipanggil klien.

    Masa simpan terbatas (lihat services.bersihkan_jejak_lama). Menyimpan
    lebih lama menambah risiko tanpa menambah kegunaan: sengketa pengiriman
    selalu muncul dalam hitungan hari, bukan bulan.
    """

    pengiriman = models.ForeignKey(
        Pengiriman, on_delete=models.CASCADE, related_name='jejak')
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    akurasi_m = models.PositiveSmallIntegerField(null=True, blank=True)
    # Waktu server. Jam perangkat kurir tidak dipercaya untuk jejak yang
    # nantinya dipakai menelusuri sengketa.
    waktu = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'logistik_jejak_posisi'
        ordering = ['pengiriman', 'waktu']
        indexes = [
            models.Index(fields=['pengiriman', 'waktu'], name='ix_jejak_kirim'),
        ]

    def __str__(self):
        return f"{self.pengiriman_id} @ {self.waktu:%H:%M}"


# =========================================================
# BUKTI TERIMA & RETUR
# =========================================================

class BuktiTerima(models.Model):
    """
    Bukti terima berupa FOTO. Bukan tanda tangan, bukan formulir.

    Append-only: koreksi berupa unggahan baru, foto lama tidak pernah
    dihapus. Satu perhentian boleh punya beberapa foto.
    """

    perhentian = models.ForeignKey(
        Perhentian, on_delete=models.PROTECT, related_name='bukti')
    foto = models.ImageField(upload_to='logistik/bukti/%Y/%m/')

    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    waktu = models.DateTimeField(auto_now_add=True)

    catatan = models.TextField(blank=True)
    diunggah_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bukti_terima_diunggah')

    # Dibuat klien. Antrean offline yang dikirim ulang harus memakai kunci
    # yang sama supaya tidak jadi dua foto untuk satu peristiwa.
    idem_key = models.CharField(max_length=128, blank=True, db_index=True)

    class Meta:
        db_table = 'logistik_bukti_terima'
        ordering = ['perhentian', 'waktu']
        constraints = [
            models.UniqueConstraint(
                fields=['idem_key'], name='uq_bukti_idem',
                condition=~Q(idem_key=''),
            ),
        ]

    def __str__(self):
        return f"Bukti {self.perhentian_id} {self.waktu:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('BuktiTerima append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('BuktiTerima append-only.')


class Retur(models.Model):
    """
    Barang ditolak pelanggan.

    Stok TIDAK langsung kembali. Butuh persetujuan Supervisor, dan
    pengembaliannya dieksekusi warehouse -- logistik hanya mencatat
    peristiwanya dan memicu.

    Karena stiker sudah menutup klaim, barang kembali ke stok badan hukum
    yang tertera di stikernya, tidak pernah ke pool bersama. Penentuan
    itu terjadi di warehouse, bukan di sini.
    """

    perhentian = models.OneToOneField(
        Perhentian, on_delete=models.PROTECT, related_name='retur')
    alasan = models.TextField()
    foto = models.ImageField(upload_to='logistik/retur/%Y/%m/', null=True, blank=True)

    dicatat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='retur_dicatat')
    dicatat_pada = models.DateTimeField(auto_now_add=True)

    disetujui_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name='retur_disetujui')
    disetujui_pada = models.DateTimeField(null=True, blank=True)
    stok_dikembalikan = models.BooleanField(default=False)

    idem_key = models.CharField(max_length=128, blank=True, db_index=True)

    class Meta:
        db_table = 'logistik_retur'
        ordering = ['-dicatat_pada']
        constraints = [
            models.UniqueConstraint(
                fields=['idem_key'], name='uq_retur_idem',
                condition=~Q(idem_key=''),
            ),
        ]

    def __str__(self):
        return f"Retur {self.perhentian_id}"

    @property
    def menunggu_persetujuan(self):
        return self.disetujui_pada is None
