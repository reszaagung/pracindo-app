"""
Papan Tugas — work_order/models.py

Work Order adalah lapisan koordinasi lintas modul. AKSES_MODUL memberi izin
`work_order` ke SEMUA peran, dan itu bukan kelalaian: ini tempat pekerjaan
yang tidak muat di satu modul manapun -- permintaan produksi dari Sales,
permintaan berkas dari Akunting, instruksi gudang.

TIGA KATEGORI
    UMUM      penugasan biasa, terlihat pembuat dan yang ditandai
    PRODUKSI  permintaan manufaktur, terlihat SEMUA orang
    PRIVATE   hanya pembuat dan yang ditandai. Lihat services.wo_terlihat()

TIGA ATURAN PENYELESAIAN
    SALAH_SATU  siapa pun yang ditandai menutup WO
    SEMUA       tiap orang menandai bagiannya; tertutup setelah yang terakhir
    PIC         hanya penanggung jawab yang bisa menutup

Penomoran memakai baris penghitung yang dikunci, bukan membaca nomor
terakhir. Membaca nomor terakhir punya dua cacat: dua pembuatan bersamaan
menghasilkan nomor identik lalu ditolak unique sebagai 500, dan pengurutan
string salah mulai WO ke-1000 dalam satu bulan.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils.timezone import localdate


class Kategori(models.TextChoices):
    UMUM     = 'UMUM',     'Penugasan / Diskusi Umum'
    PRODUKSI = 'PRODUKSI', 'Pesanan Produksi (Global)'
    PRIVATE  = 'PRIVATE',  'Pesan Pribadi / Rahasia'


class AturanSelesai(models.TextChoices):
    SALAH_SATU = 'SALAH_SATU', 'Cukup Satu Anggota'
    SEMUA      = 'SEMUA',      'Semua Anggota Harus ACC'
    PIC        = 'PIC',        'Hanya Penanggung Jawab (PIC)'


class CounterWorkOrder(models.Model):
    """
    Penghitung nomor per periode. Dikunci select_for_update saat dinaikkan,
    sehingga dua pembuatan bersamaan mendapat nomor berbeda.
    """
    periode = models.CharField(max_length=7, unique=True)   # '2026/08'
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'wo_counter'

    def __str__(self):
        return f"{self.periode}: {self.urutan}"

    @classmethod
    def berikutnya(cls, tanggal=None):
        tanggal = tanggal or localdate()
        periode = tanggal.strftime('%Y/%m')
        with transaction.atomic():
            cls.objects.get_or_create(periode=periode)
            baris = cls.objects.select_for_update().get(periode=periode)
            baris.urutan += 1
            baris.save(update_fields=['urutan'])
        return f"WO/{periode}/{baris.urutan:03d}"


class WorkOrder(models.Model):
    nomor = models.CharField(max_length=50, unique=True, editable=False)
    kategori = models.CharField(max_length=15, choices=Kategori.choices,
                                default=Kategori.UMUM, db_index=True)
    judul = models.CharField(max_length=255)
    deskripsi = models.TextField(
        blank=True, help_text='Teks pembuka diskusi atau instruksi awal')

    aturan_penyelesaian = models.CharField(
        max_length=15, choices=AturanSelesai.choices,
        default=AturanSelesai.SALAH_SATU)

    tanggal = models.DateField(default=localdate)
    deadline = models.DateField(null=True, blank=True, db_index=True)

    selesai = models.BooleanField(default=False, db_index=True)
    catatan_selesai = models.TextField(blank=True)
    waktu_selesai = models.DateTimeField(null=True, blank=True)

    diselesaikan_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='wo_diselesaikan')
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wo_dibuat', editable=False)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wo_work_order'
        ordering = ['-dibuat_pada']
        indexes = [
            models.Index(fields=['selesai', 'kategori', 'deadline'],
                         name='ix_wo_papan'),
        ]
        constraints = [
            # Sesuai kebiasaan repo: kalau selesai, jejaknya harus lengkap.
            models.CheckConstraint(
                condition=Q(selesai=False) | Q(waktu_selesai__isnull=False),
                name='ck_wo_selesai_berwaktu',
            ),
        ]

    def __str__(self):
        return f"{self.nomor} - {self.judul}"

    @property
    def terlambat(self):
        """Dihitung SERVER. Membandingkan dengan jam perangkat membuat
        penanda berbeda antar pengguna di ruangan yang sama."""
        if self.selesai or not self.deadline:
            return False
        return localdate() > self.deadline

    @property
    def jumlah_pesan(self):
        return self.pesan_chat.count()

    @property
    def progres_penyelesaian(self):
        """(sudah, total) -- hanya bermakna untuk aturan SEMUA."""
        total = self.penugasan.count()
        sudah = self.penugasan.filter(is_selesai_personal=True).count()
        return sudah, total

    def save(self, *args, **kwargs):
        if not self.nomor:
            self.nomor = CounterWorkOrder.berikutnya(self.tanggal)
        super().save(*args, **kwargs)


class DetailPesananProduksi(models.Model):
    """Ekstensi 1-ke-1. Hanya untuk WorkOrder berkategori PRODUKSI."""

    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.CASCADE, related_name='detail_produksi')
    nama_item = models.CharField(
        max_length=255, help_text='Varian Pigment (mis. Super White SC)')

    UNIT_CHOICES = [
        ('PCS_1', 'Pcs (1 kg)'),
        ('GALON_5', 'Galon (5 kg)'),
        ('DUS_12', 'Dus (12 kg)'),
        ('PAIL_20', 'Pail (20 kg)'),
        ('PAIL_25', 'Pail (25 kg)'),
        ('PAIL_30', 'Pail (30 kg)'),
    ]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)

    # Stiker menentukan BADAN HUKUM MANA YANG MENJUAL, bukan sekadar merek.
    # Barang berstiker tidak bisa diklaim lagi -- penempelan stiker adalah
    # peristiwa terminal untuk kepemilikan bersama.
    STIKER_CHOICES = [
        ('POLOS', 'Polos (Tanpa Merek)'),
        ('PT', 'Stiker PT'),
        ('CV', 'Stiker CV'),
    ]
    stiker = models.CharField(max_length=10, choices=STIKER_CHOICES)

    class Meta:
        db_table = 'wo_detail_produksi'

    def __str__(self):
        return f"{self.nama_item} - {self.get_unit_display()}"


class WorkOrderPenugasan(models.Model):
    """Staf yang ditandai dalam tugas ini."""

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name='penugasan')
    staff = models.ForeignKey(
        'staff_user.Profil', on_delete=models.CASCADE,
        related_name='wo_ditugaskan')

    is_pic = models.BooleanField(default=False)
    is_selesai_personal = models.BooleanField(default=False)
    ditandai_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wo_penugasan'
        ordering = ['-is_pic', 'id']
        constraints = [
            models.UniqueConstraint(fields=['work_order', 'staff'],
                                    name='uq_wo_penugasan'),
            # Paling banyak satu PIC per WO. Dua PIC membuat aturan
            # penyelesaian PIC tidak lagi menunjuk satu orang.
            models.UniqueConstraint(
                fields=['work_order'], condition=Q(is_pic=True),
                name='uq_wo_pic_tunggal',
            ),
        ]

    def __str__(self):
        return f"{self.work_order_id} - {self.staff_id}"


class WorkOrderPesan(models.Model):
    """
    Diskusi di dalam Work Order. APPEND-ONLY.

    Ini jejak kesepakatan: enam bulan lagi, satu-satunya cara mengetahui
    kenapa sesuatu diputuskan adalah membaca percakapan yang menempel pada
    pekerjaannya.
    """

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name='pesan_chat')
    pengirim = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wo_pesan_terkirim')
    teks = models.TextField()
    # Waktu server. Jam perangkat tidak dipercaya untuk arsip.
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wo_pesan'
        ordering = ['dibuat_pada']
        indexes = [
            models.Index(fields=['work_order', 'dibuat_pada'],
                         name='ix_wo_pesan_urut'),
        ]

    def __str__(self):
        return f"{self.work_order_id}: {self.teks[:40]}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('Pesan Work Order append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Pesan Work Order append-only.')
