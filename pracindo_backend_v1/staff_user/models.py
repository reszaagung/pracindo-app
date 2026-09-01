"""
Pengguna, peran, dan data kepegawaian — staff_user/models.py

DUA PEMISAHAN YANG MENENTUKAN STRUKTUR

  Jabatan bukan Role
      Jabatan  gelar organisasi ("Kepala Gudang"), untuk dokumen dan
               struktur organisasi
      Role     izin sistem (GUDANG), menentukan modul mana yang terbuka

      Jabatan bisa berubah tanpa izin berubah, dan sebaliknya. Kalau
      digabung, setiap promosi jadi perubahan izin yang tidak disengaja.

  Data login bukan data kepegawaian
      NIK dan NPWP adalah data pribadi. Kalau ditaruh di tabel user,
      dia ikut termuat di SETIAP pemeriksaan autentikasi dan gampang
      bocor lewat serializer yang lupa memfilter. Di tabel terpisah,
      dia tidak pernah ikut kecuali diminta.

ROLE ADALAH KUNCI PORTAL. Modul mana yang terbuka ditentukan sepenuhnya
oleh role, dan petanya ada di permissions.py sebagai data.

Akun TIDAK PERNAH dihapus. Semua model transaksional memakai
on_delete=PROTECT ke dibuat_oleh -- menghapus user berarti menghancurkan
jejak audit.
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.models import TimeStampedModel


# =========================================================
# ROLE
# =========================================================

class Role(models.TextChoices):
    SUPERVISOR = 'SUPERVISOR', 'Supervisor'
    ADMIN      = 'ADMIN',      'Admin'
    AKUNTING   = 'AKUNTING',   'Akunting'
    KEUANGAN   = 'KEUANGAN',   'Keuangan'
    GUDANG     = 'GUDANG',     'Gudang'
    PRODUKSI   = 'PRODUKSI',   'Produksi'
    SALES      = 'SALES',      'Sales'
    STAFF      = 'STAFF',      'Staff',
    KURIR      = 'KURIR',      'Kurir'    


class StatusKerja(models.TextChoices):
    AKTIF = 'AKTIF', 'Aktif'
    CUTI  = 'CUTI',  'Cuti'
    KELUAR = 'KELUAR', 'Sudah keluar'


class Departemen(models.TextChoices):
    GUDANG    = 'GUDANG',    'Gudang'
    AKUNTING  = 'AKUNTING',  'Akunting'
    KEUANGAN  = 'KEUANGAN',  'Keuangan'
    PRODUKSI  = 'PRODUKSI',  'Produksi'
    PENJUALAN = 'PENJUALAN', 'Penjualan'
    UMUM      = 'UMUM',      'Umum'



class Jabatan(TimeStampedModel):
    """
    Gelar organisasi. Untuk ditampilkan di dokumen dan struktur, BUKAN
    untuk menentukan izin.
    """

    kode       = models.CharField(max_length=16, unique=True)
    nama       = models.CharField(max_length=120)
    departemen = models.CharField(max_length=12, choices=Departemen.choices,
                                  default=Departemen.UMUM)
    level = models.PositiveSmallIntegerField(default=5)
    aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'staff_user_jabatan'
        ordering = ['level', 'nama']
        verbose_name_plural = 'Jabatan'

    def __str__(self):
        return self.nama


class ProfilManager(UserManager):

    def aktif(self):
        return self.filter(is_active=True, status_kerja=StatusKerja.AKTIF)

    def menunggu_persetujuan(self):
        return self.filter(is_active=False, disetujui_oleh__isnull=True,
                           ditolak_pada__isnull=True)

    def berperan(self, *roles):
        return self.aktif().filter(role__in=roles)


class Profil(AbstractUser):
    """
    Menggantikan auth.User sepenuhnya (AUTH_USER_MODEL).

    Pendaftaran memaksa role=STAFF dan is_active=False. Peran sebenarnya
    ditetapkan Supervisor saat menyetujui -- itu satu-satunya jalan
    seseorang mendapat akses modul.
    """

    nip = models.CharField(
        max_length=24, unique=True, null=True, blank=True,
        help_text='Nomor induk pegawai. Dicantumkan di dokumen.',
    )
    role = models.CharField(
        max_length=12, choices=Role.choices, default=Role.STAFF, db_index=True,
    )
    jabatan = models.ForeignKey(
        Jabatan, null=True, blank=True, on_delete=models.PROTECT,
        related_name='pemegang',
    )
    foto = models.ImageField(upload_to='profil/%Y/%m/', null=True, blank=True)
    nomor_hp = models.CharField(max_length=20, blank=True)

    atasan = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT,
        related_name='bawahan',
    )

    entitas_default = models.ForeignKey(
        'core.Entitas', null=True, blank=True,
        on_delete=models.PROTECT, related_name='pengguna_default',
    )
    # KOSONG = boleh semua entitas. Isi hanya kalau perlu dibatasi.
    entitas_diizinkan = models.ManyToManyField(
        'core.Entitas', blank=True, related_name='pengguna_diizinkan',
    )

    status_kerja  = models.CharField(max_length=8, choices=StatusKerja.choices,
                                     default=StatusKerja.AKTIF, db_index=True)
    tanggal_masuk  = models.DateField(null=True, blank=True)
    tanggal_keluar = models.DateField(null=True, blank=True)

    # ---- jejak persetujuan ----
    disetujui_oleh = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT,
        related_name='akun_disetujui', editable=False,
    )
    disetujui_pada = models.DateTimeField(null=True, blank=True, editable=False)
    ditolak_pada   = models.DateTimeField(null=True, blank=True, editable=False)
    alasan_tolak   = models.TextField(blank=True)

    objects = ProfilManager()

    class Meta:
        db_table = 'staff_user_profil'
        ordering = ['username']
        verbose_name = 'Profil'
        verbose_name_plural = 'Profil'
        constraints = [
            models.CheckConstraint(
                condition=Q(tanggal_keluar__isnull=True)
                | Q(tanggal_masuk__isnull=True)
                | Q(tanggal_keluar__gte=models.F('tanggal_masuk')),
                name='ck_profil_tanggal_urut',
            ),
        ]
        indexes = [
            models.Index(fields=['role', 'is_active'], name='ix_profil_role_aktif'),
        ]

    def __str__(self):
        return f"{self.nama_lengkap} ({self.get_role_display()})"


    @property
    def nama_lengkap(self):
        return self.get_full_name() or self.username

    @property
    def supervisor(self):
        return self.role == Role.SUPERVISOR or self.is_superuser

    @property
    def bisa_login(self):
        return self.is_active and self.status_kerja != StatusKerja.KELUAR

    @property
    def menunggu_persetujuan(self):
        return (not self.is_active
                and self.disetujui_oleh_id is None
                and self.ditolak_pada is None)

    def punya_role(self, *roles):
        """Superuser selalu lolos. Sisanya harus cocok persis."""
        return self.is_superuser or self.role in roles

    def modul_terbuka(self):
        """
        Daftar modul yang boleh dimasuki role ini. Dipakai frontend
        untuk merender kartu dashboard.
        """
        from .permissions import modul_untuk_role
        return modul_untuk_role(self.role, self.is_superuser)

    def bisa_akses_modul(self, modul):
        from .permissions import role_boleh_modul
        return role_boleh_modul(self.role, modul, self.is_superuser)

    def bisa_akses_entitas(self, entitas_id):
        """Kosong = boleh semua. Ini pilihan default yang aman."""
        if self.is_superuser:
            return True
        izin = self.entitas_diizinkan.all()
        return not izin.exists() or izin.filter(pk=entitas_id).exists()

    def entitas_terlihat(self):
        from core.models import Entitas
        if self.is_superuser or not self.entitas_diizinkan.exists():
            return Entitas.objects.filter(aktif=True)
        return self.entitas_diizinkan.filter(aktif=True)

    # ---------- perilaku ----------

    def clean(self):
        if self.atasan_id == self.pk and self.pk:
            raise ValidationError({'atasan': 'Tidak bisa jadi atasan diri sendiri.'})
        if self.status_kerja == StatusKerja.KELUAR and not self.tanggal_keluar:
            raise ValidationError(
                {'tanggal_keluar': 'Wajib diisi kalau status sudah keluar.'}
            )

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Akun tidak boleh dihapus -- jejak audit transaksi merujuk ke sini. '
            'Nonaktifkan saja.'
        )


class JenisKelamin(models.TextChoices):
    L = 'L', 'Laki-laki'
    P = 'P', 'Perempuan'


class StatusPajak(models.TextChoices):
    TK0 = 'TK/0', 'TK/0 - Tidak kawin, tanpa tanggungan'
    TK1 = 'TK/1', 'TK/1'
    TK2 = 'TK/2', 'TK/2'
    TK3 = 'TK/3', 'TK/3'
    K0  = 'K/0',  'K/0 - Kawin, tanpa tanggungan'
    K1  = 'K/1',  'K/1'
    K2  = 'K/2',  'K/2'
    K3  = 'K/3',  'K/3'


class DataKepegawaian(TimeStampedModel):
    """
    Data pribadi yang sensitif. Sengaja terpisah dari Profil supaya tidak
    ikut termuat di setiap pemeriksaan autentikasi.

    Hanya Supervisor dan pemilik akun sendiri yang boleh melihatnya.
    """

    profil = models.OneToOneField(
        Profil, on_delete=models.PROTECT, related_name='kepegawaian',
    )

    nik_ktp = models.CharField(max_length=16, blank=True)
    npwp    = models.CharField(max_length=20, blank=True)

    tempat_lahir  = models.CharField(max_length=80, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices,
                                     blank=True)
    alamat = models.TextField(blank=True)

    status_pajak = models.CharField(max_length=4, choices=StatusPajak.choices,
                                    blank=True)

    bank          = models.CharField(max_length=40, blank=True)
    no_rekening   = models.CharField(max_length=40, blank=True)
    nama_rekening = models.CharField(max_length=120, blank=True)

    kontak_darurat_nama     = models.CharField(max_length=120, blank=True)
    kontak_darurat_hubungan = models.CharField(max_length=40, blank=True)
    kontak_darurat_hp       = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'staff_user_data_kepegawaian'
        verbose_name = 'Data kepegawaian'
        verbose_name_plural = 'Data kepegawaian'

    def __str__(self):
        return f"Data {self.profil.nama_lengkap}"

    @property
    def usia(self):
        if not self.tanggal_lahir:
            return None
        hari_ini = timezone.localdate()
        return (hari_ini.year - self.tanggal_lahir.year
                - ((hari_ini.month, hari_ini.day)
                   < (self.tanggal_lahir.month, self.tanggal_lahir.day)))


class RiwayatAkses(models.Model):
    """
    Jejak login, append-only. Percobaan GAGAL ikut dicatat -- deretan
    kegagalan pada satu username adalah sinyal pertama serangan tebak
    kata sandi.
    """

    profil = models.ForeignKey(
        Profil, null=True, blank=True, on_delete=models.PROTECT,
        related_name='riwayat_akses',
    )
    username_dicoba = models.CharField(max_length=150)
    waktu = models.DateTimeField(auto_now_add=True, db_index=True)

    berhasil     = models.BooleanField(db_index=True)
    alasan_gagal = models.CharField(max_length=80, blank=True)

    ip         = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'staff_user_riwayat_akses'
        ordering = ['-waktu']
        verbose_name_plural = 'Riwayat akses'
        indexes = [
            models.Index(fields=['username_dicoba', '-waktu'],
                         name='ix_akses_username'),
            models.Index(fields=['berhasil', '-waktu'], name='ix_akses_hasil'),
        ]

    def __str__(self):
        tanda = 'OK' if self.berhasil else 'GAGAL'
        return f"[{tanda}] {self.username_dicoba} {self.waktu:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('RiwayatAkses append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('RiwayatAkses append-only.')