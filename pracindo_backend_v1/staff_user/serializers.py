"""Serializer pengguna — staff_user/serializers.py"""
from rest_framework import serializers

from .models import (
    DataKepegawaian, Jabatan, Profil, RiwayatAkses, Role, StatusKerja,
)


class JabatanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jabatan
        fields = ['id', 'kode', 'nama', 'departemen', 'level', 'aktif']


class ProfilRingkasSerializer(serializers.ModelSerializer):
    """Untuk dropdown dan referensi. Tidak memuat apa pun yang sensitif."""

    nama = serializers.CharField(source='nama_lengkap', read_only=True)
    jabatan_nama = serializers.CharField(source='jabatan.nama',
                                         read_only=True, default=None)

    class Meta:
        model = Profil
        fields = ['id', 'username', 'nama', 'nip', 'role', 'jabatan_nama', 'foto']


class ProfilSerializer(serializers.ModelSerializer):
    nama = serializers.CharField(source='nama_lengkap', read_only=True)
    jabatan_nama = serializers.CharField(source='jabatan.nama',
                                         read_only=True, default=None)
    atasan_nama = serializers.CharField(source='atasan.nama_lengkap',
                                        read_only=True, default=None)
    entitas_default_kode = serializers.CharField(
        source='entitas_default.kode', read_only=True, default=None,
    )

    class Meta:
        model = Profil
        fields = [
            'id', 'username', 'first_name', 'last_name', 'nama', 'email',
            'nip', 'role', 'jabatan', 'jabatan_nama', 'foto', 'nomor_hp',
            'atasan', 'atasan_nama', 'entitas_default', 'entitas_default_kode',
            'entitas_diizinkan', 'status_kerja', 'tanggal_masuk',
            'tanggal_keluar', 'is_active', 'last_login',
        ]
        # role dan is_active hanya berubah lewat service, tidak pernah
        # lewat PATCH biasa -- itu jalur eskalasi hak akses.
        read_only_fields = ['role', 'is_active', 'nip', 'last_login',
                            'tanggal_keluar']


class PendaftaranSerializer(serializers.Serializer):
    """
    Field mengikuti form frontend: nama_lengkap dan telepon.

    Nama utuh disimpan di first_name, last_name dibiarkan kosong. Memaksa
    pemecahan nama depan/belakang adalah asumsi Barat -- banyak nama
    Indonesia tidak punya nama keluarga, dan memecahnya selalu menebak.
    get_full_name() tetap mengembalikan nama utuh.
    """

    nama_lengkap = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=10)
    email    = serializers.EmailField(required=False, allow_blank=True)
    telepon  = serializers.CharField(max_length=20, required=False,
                                     allow_blank=True, default='')

    def validate_nama_lengkap(self, v):
        if not v.strip():
            raise serializers.ValidationError('Nama lengkap wajib diisi.')
        return v.strip()

    def validate_username(self, v):
        v = v.strip()
        if ' ' in v:
            raise serializers.ValidationError('Username tidak boleh mengandung spasi.')
        return v


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AktivasiSerializer(serializers.Serializer):
    role    = serializers.ChoiceField(choices=Role.choices)
    jabatan = serializers.IntegerField(required=False, allow_null=True)
    nip     = serializers.CharField(max_length=24, required=False, allow_blank=True)
    entitas_default   = serializers.IntegerField(required=False, allow_null=True)
    entitas_diizinkan = serializers.ListField(
        child=serializers.IntegerField(), required=False,
    )
    atasan        = serializers.IntegerField(required=False, allow_null=True)
    tanggal_masuk = serializers.DateField(required=False, allow_null=True)


class PenolakanSerializer(serializers.Serializer):
    alasan = serializers.CharField()


class UbahRoleSerializer(serializers.Serializer):
    role   = serializers.ChoiceField(choices=Role.choices)
    alasan = serializers.CharField(required=False, allow_blank=True)


class GantiPasswordSerializer(serializers.Serializer):
    password_lama = serializers.CharField(write_only=True)
    password_baru = serializers.CharField(write_only=True, min_length=10)


class ResetPasswordSerializer(serializers.Serializer):
    password_baru = serializers.CharField(write_only=True, min_length=10)


class NonaktifSerializer(serializers.Serializer):
    tanggal_keluar = serializers.DateField(required=False, allow_null=True)
    alasan = serializers.CharField(required=False, allow_blank=True)


class DataKepegawaianSerializer(serializers.ModelSerializer):
    """Sensitif. Hanya pemilik dan Supervisor yang boleh membacanya."""

    usia = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataKepegawaian
        fields = [
            'id', 'profil', 'nik_ktp', 'npwp', 'tempat_lahir', 'tanggal_lahir',
            'usia', 'jenis_kelamin', 'alamat', 'status_pajak',
            'bank', 'no_rekening', 'nama_rekening',
            'kontak_darurat_nama', 'kontak_darurat_hubungan', 'kontak_darurat_hp',
        ]
        read_only_fields = ['profil']


class RiwayatAksesSerializer(serializers.ModelSerializer):
    nama = serializers.CharField(source='profil.nama_lengkap',
                                 read_only=True, default=None)

    class Meta:
        model = RiwayatAkses
        fields = ['id', 'nama', 'username_dicoba', 'waktu', 'berhasil',
                  'alasan_gagal', 'ip']
