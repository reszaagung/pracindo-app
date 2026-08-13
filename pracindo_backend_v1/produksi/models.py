"""
Resep dan sesi produksi | produksi/models.py

Sesi produksi adalah PEMINDAHAN NILAI, bukan penciptaan nilai.

    mulai_sesi()       menarik bahan dari pool, mencatat berapa rupiah
                       yang ikut keluar  -> SesiProduksi.nilai_input
    selesaikan_sesi()  mengembalikan rupiah SEBANDING RENDEMEN ke pool;
                       nilai yang melekat pada bagian susut dibebankan
    gagalkan_sesi()    seluruh rupiah musnah -> dibebankan pro-rata ke
                       pemegang klaim lewat MutasiKlaim RUGI

Tiga jalan itu menutup semua kemungkinan. Tidak ada rupiah yang menguap
tanpa ada yang menanggungnya.

PERUBAHAN STRUKTUR
    SesiInput sekarang unik per (sesi, bahan, TANGKI), bukan per
    (sesi, bahan). Satu bahan sering tersimpan di dua tangki, dan
    memaksanya jadi satu baris berarti stok di tangki kedua tidak pernah
    terpakai -- kapasitas bilang cukup, penarikan bilang habis.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.constants import NILAI_DIGITS, NILAI_PLACES, QTY_DIGITS, QTY_PLACES
from core.models import CounterDokumen, DiauditModel, TimeStampedModel


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
        """Bahan yang dibutuhkan untuk qty_target unit. {produk_id: qty}"""
        faktor = Decimal(qty_target) / self.hasil_per_batch
        return {
            i.bahan_id: (i.qty * faktor).quantize(Decimal('0.001'))
            for i in self.item.all()
        }

    @property
    def hasil_minimum_wajar(self):
        """Fraksi hasil terendah yang masih dianggap normal."""
        return Decimal('1') - self.susut_wajar


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
            raise ValidationError(
                {'bahan': 'Produk tidak boleh jadi bahannya sendiri.'})


class StatusSesi(models.TextChoices):
    DRAFT    = 'DRAFT',    'Draft'
    BERJALAN = 'BERJALAN', 'Berjalan'
    SELESAI  = 'SELESAI',  'Selesai'
    GAGAL    = 'GAGAL',    'Gagal'
    BATAL    = 'BATAL',    'Dibatalkan'


class JenisSesi(models.TextChoices):
    PRODUKSI = 'PRODUKSI', 'Produksi Rutin'
    RND      = 'RND',      'R&D / Percobaan'


class KategoriKegagalan(models.TextChoices):
    PROSES = 'PROSES', 'Kesalahan proses (suhu, waktu, pengaduk)'
    BAHAN  = 'BAHAN',  'Bahan tidak sesuai'
    ALAT   = 'ALAT',   'Kerusakan alat'
    UJI    = 'UJI',    'Tidak lulus uji'
    LAIN   = 'LAIN',   'Lain-lain'


class SesiProduksi(DiauditModel):
    """
    Satu putaran produksi. Beroperasi di lapis POOL, tanpa entitas.
    Satu sesi tidak boleh melintasi grup -- pool PT dan pool BERSAMA
    tidak pernah bercampur.
    """
    grup_bahan = models.ForeignKey('core.GrupBahan', on_delete=models.PROTECT,
                                   related_name='sesi_produksi')
    nomor   = models.CharField(max_length=32, editable=False)
    tanggal = models.DateField(default=timezone.localdate, db_index=True)

    jenis_sesi = models.CharField(max_length=10, choices=JenisSesi.choices,
                                  default=JenisSesi.PRODUKSI, db_index=True)
    resep = models.ForeignKey(Resep, on_delete=models.PROTECT,
                              related_name='sesi', null=True, blank=True)
    produk_jadi = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                                    related_name='+')

    qty_target = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    qty_hasil = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
        default=Decimal('0'), editable=False,
    )
    nilai_input = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )
    nilai_hasil = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        default=Decimal('0'), editable=False,
    )

    status = models.CharField(max_length=10, choices=StatusSesi.choices,
                              default=StatusSesi.DRAFT, db_index=True)
    tangki_hasil = models.ForeignKey(
        'inventory.Tangki', null=True, blank=True,
        on_delete=models.PROTECT, related_name='sesi_hasil',
    )
    catatan = models.TextField(blank=True)

    hasil_masuk_pool = models.BooleanField(default=True)
    nilai_kerugian = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
        null=True, blank=True, editable=False,
    )
    kategori_kegagalan = models.CharField(
        max_length=15, choices=KategoriKegagalan.choices, blank=True)

    class Meta:
        db_table = 'produksi_sesi'
        ordering = ['-tanggal', '-id']
        verbose_name_plural = 'Sesi produksi'
        constraints = [
            models.UniqueConstraint(fields=['grup_bahan', 'nomor'],
                                    name='uq_sesi_nomor'),
            models.CheckConstraint(condition=Q(qty_target__gt=0),
                                   name='ck_sesi_target_positif'),
            # Sesi rutin wajib berresep. Dulu hanya dijaga clean(), yang
            # tidak pernah dipanggil karena services memakai .create().
            models.CheckConstraint(
                condition=Q(jenis_sesi='RND') | Q(resep__isnull=False),
                name='ck_sesi_rutin_wajib_resep',
            ),
        ]
        indexes = [
            models.Index(fields=['grup_bahan', 'status', '-tanggal'],
                         name='ix_sesi_grup_status'),
        ]

    def __str__(self):
        return f"{self.nomor} - {self.produk_jadi.kode} x {self.qty_target}"

    def clean(self):
        if self.jenis_sesi == JenisSesi.PRODUKSI:
            if not self.resep_id:
                raise ValidationError(
                    {'resep': 'Sesi produksi rutin wajib menggunakan resep.'})
            if self.produk_jadi_id and self.produk_jadi_id != self.resep.produk_jadi_id:
                raise ValidationError(
                    {'produk_jadi': 'Produk jadi harus sama dengan resep.'})
        if self.tangki_hasil_id and self.tangki_hasil.grup_bahan_id != self.grup_bahan_id:
            raise ValidationError(
                {'tangki_hasil': 'Tangki hasil berada di grup bahan lain.'})

    @property
    def susut(self):
        return self.qty_target - self.qty_hasil

    @property
    def rendemen(self):
        """Hasil dibagi target. Di bawah 1 berarti ada susut."""
        return (self.qty_hasil / self.qty_target) if self.qty_target else Decimal('0')

    @property
    def harga_hasil_per_satuan(self):
        """
        Rupiah per satuan yang melekat pada hasil.

        Angka ini TIDAK naik karena susut: nilai yang menguap ikut
        hilang, tidak dititipkan ke produk yang selamat. Jadi harga
        per satuan konsisten antar batch, dan yang mengklaim dari batch
        bersusut tinggi tidak dihukum.
        """
        if not self.qty_hasil:
            return Decimal('0')
        return (self.nilai_hasil / self.qty_hasil).quantize(Decimal('0.0001'))

    def save(self, *args, **kwargs):
        if self.jenis_sesi == JenisSesi.PRODUKSI and self.resep_id:
            self.produk_jadi_id = self.resep.produk_jadi_id
        if not self.nomor:
            entitas = self.grup_bahan.entitas.order_by('kode').first()
            if not entitas:
                raise ValidationError('Grup bahan belum punya entitas.')
            kode = 'RND' if self.jenis_sesi == JenisSesi.RND else 'SESI'
            self.nomor = CounterDokumen.berikutnya(entitas, kode, self.tanggal)
        self.full_clean(exclude=['nomor'], validate_unique=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != StatusSesi.DRAFT:
            raise ValidationError('Sesi yang sudah berjalan tidak bisa dihapus.')
        return super().delete(*args, **kwargs)


class SesiInput(models.Model):
    """
    Bahan yang BENAR-BENAR diambil dari pool, per tangki asal.

    `nilai_aktual` diisi mulai_sesi() dari nilai yang ikut keluar. Itu
    bukan qty x tarif tabel, melainkan porsi nilai riil yang melekat di
    tangki asal saat itu.
    """
    sesi  = models.ForeignKey(SesiProduksi, on_delete=models.PROTECT,
                              related_name='input')
    bahan = models.ForeignKey('master.Produk', on_delete=models.PROTECT,
                              related_name='+')
    tangki = models.ForeignKey('inventory.Tangki', null=True, blank=True,
                               on_delete=models.PROTECT, related_name='+')

    qty_rencana = models.DecimalField(max_digits=QTY_DIGITS,
                                      decimal_places=QTY_PLACES,
                                      default=Decimal('0'))
    qty_aktual = models.DecimalField(max_digits=QTY_DIGITS,
                                     decimal_places=QTY_PLACES,
                                     default=Decimal('0'))
    nilai_aktual = models.DecimalField(max_digits=NILAI_DIGITS,
                                       decimal_places=NILAI_PLACES,
                                       default=Decimal('0'), editable=False)

    class Meta:
        db_table = 'produksi_sesi_input'
        ordering = ['id']
        constraints = [
            # Kunci mencakup tangki: satu bahan boleh ditarik dari dua
            # tangki dalam satu sesi.
            models.UniqueConstraint(
                fields=['sesi', 'bahan', 'tangki'],
                condition=Q(tangki__isnull=False), name='uq_sesi_input_tangki',
            ),
            models.UniqueConstraint(
                fields=['sesi', 'bahan'],
                condition=Q(tangki__isnull=True), name='uq_sesi_input_rak',
            ),
            models.CheckConstraint(condition=Q(qty_aktual__gte=0),
                                   name='ck_sesi_input_nonneg'),
        ]

    def __str__(self):
        return f"{self.bahan.kode} {self.qty_aktual}"

    @property
    def selisih(self):
        return self.qty_aktual - self.qty_rencana

    @property
    def harga_per_satuan(self):
        if not self.qty_aktual:
            return Decimal('0')
        return (self.nilai_aktual / self.qty_aktual).quantize(Decimal('0.0001'))


class HasilKomponen(models.Model):
    """
    Traceability hasil: setiap hasil X menyimpan komponen formula yang
    membentuknya. Baris ini adalah jejak produksi, bukan sumber harga baru.

    Nilai komponen dihitung proporsional dari `SesiInput.nilai_aktual`;
    jumlah seluruh nilai komponen harus sama persis dengan `nilai_hasil`.
    """
    sesi = models.ForeignKey(
        SesiProduksi, on_delete=models.PROTECT, related_name='komponen_hasil',
    )
    sesi_input = models.ForeignKey(
        SesiInput, on_delete=models.PROTECT, related_name='komponen_hasil',
    )
    bahan = models.ForeignKey(
        'master.Produk', on_delete=models.PROTECT, related_name='+',
    )
    qty = models.DecimalField(
        max_digits=QTY_DIGITS, decimal_places=QTY_PLACES,
    )
    nilai = models.DecimalField(
        max_digits=NILAI_DIGITS, decimal_places=NILAI_PLACES,
    )

    class Meta:
        db_table = 'produksi_hasil_komponen'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['sesi', 'sesi_input'],
                name='uq_hasil_komponen_sesi_input',
            ),
            models.CheckConstraint(condition=Q(qty__gte=0),
                                   name='ck_hasil_komponen_qty_nonneg'),
            models.CheckConstraint(condition=Q(nilai__gte=0),
                                   name='ck_hasil_komponen_nilai_nonneg'),
        ]

    def clean(self):
        if self.sesi_input_id and self.sesi_id != self.sesi_input.sesi_id:
            raise ValidationError('Input komponen harus berasal dari sesi yang sama.')
        if self.bahan_id and self.sesi_input_id and self.bahan_id != self.sesi_input.bahan_id:
            raise ValidationError('Bahan komponen harus sama dengan bahan input.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TipeNilaiPengukuran(models.TextChoices):
    ANGKA = 'ANGKA', 'Angka'
    TEKS  = 'TEKS',  'Teks'
    BOOL  = 'BOOL',  'Ya/Tidak'


class TahapPengukuran(models.TextChoices):
    PROSES = 'PROSES', 'Proses'
    UJI    = 'UJI',    'Hasil uji'


class JenisPengukuran(TimeStampedModel):
    kode = models.CharField(max_length=32, unique=True)
    nama = models.CharField(max_length=120)
    satuan = models.CharField(max_length=20, blank=True)
    tipe_nilai = models.CharField(max_length=10,
                                  choices=TipeNilaiPengukuran.choices,
                                  default=TipeNilaiPengukuran.ANGKA)
    nilai_min = models.DecimalField(max_digits=10, decimal_places=4,
                                    null=True, blank=True)
    nilai_max = models.DecimalField(max_digits=10, decimal_places=4,
                                    null=True, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'produksi_jenis_pengukuran'
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} ({self.satuan})" if self.satuan else self.nama


class SesiPengukuran(models.Model):
    """
    Pencatatan aktual suhu, durasi, dll. APPEND-ONLY -- dijaga save(),
    bukan hanya dijanjikan docstring. Salah catat diperbaiki dengan baris
    baru yang menunjuk `mengoreksi`.
    """
    sesi = models.ForeignKey(SesiProduksi, on_delete=models.CASCADE,
                             related_name='pengukuran')
    tahap = models.CharField(max_length=10, choices=TahapPengukuran.choices,
                             default=TahapPengukuran.PROSES)
    nama = models.ForeignKey(JenisPengukuran, on_delete=models.PROTECT,
                             related_name='+')

    nilai = models.DecimalField(max_digits=14, decimal_places=4,
                                null=True, blank=True)
    nilai_teks = models.CharField(max_length=255, blank=True)

    waktu = models.DateTimeField(default=timezone.now)
    catatan = models.TextField(blank=True)
    mengoreksi = models.ForeignKey('self', null=True, blank=True,
                                   on_delete=models.PROTECT,
                                   related_name='dikoreksi_oleh')
    dicatat_oleh = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'produksi_sesi_pengukuran'
        ordering = ['waktu', 'id']
        indexes = [
            models.Index(fields=['sesi', 'nama', 'waktu'],
                         name='ix_ukur_sesi_jenis'),
        ]

    def __str__(self):
        return f"{self.nama.kode} {self.nilai or self.nilai_teks}"

    def clean(self):
        jenis = self.nama
        if jenis.tipe_nilai == TipeNilaiPengukuran.ANGKA:
            if self.nilai is None:
                raise ValidationError({'nilai': f'{jenis.nama} butuh angka.'})
            if jenis.nilai_min is not None and self.nilai < jenis.nilai_min:
                raise ValidationError(
                    {'nilai': f'Di bawah batas {jenis.nilai_min}.'})
            if jenis.nilai_max is not None and self.nilai > jenis.nilai_max:
                raise ValidationError(
                    {'nilai': f'Di atas batas {jenis.nilai_max}.'})
        elif not self.nilai_teks:
            raise ValidationError({'nilai_teks': f'{jenis.nama} butuh isian.'})

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(
                'Pengukuran append-only. Catat baris baru dengan '
                'mengoreksi=<id lama>.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Pengukuran append-only.')


class SesiCatatan(models.Model):
    """Observasi teks. Append-only."""
    sesi = models.ForeignKey(SesiProduksi, on_delete=models.CASCADE,
                             related_name='catatan_eksperimen')
    waktu = models.DateTimeField(default=timezone.now)
    teks = models.TextField()
    penulis = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'produksi_sesi_catatan'
        ordering = ['waktu', 'id']

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('Catatan append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Catatan append-only.')