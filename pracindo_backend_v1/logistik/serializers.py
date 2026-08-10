"""
Serializer logistik — logistik/serializers.py

Aturan rumah DRF tetap berlaku: endpoint router terpaginasi, @action
mengembalikan objek atau array polos. Decimal dikirim sebagai string.

`status` selalu KODE MENTAH. Label untuk manusia ada di `status_label`
terpisah. Klien membandingkan kode, dan kode yang berubah jadi label
membuat tombol aksi hilang tanpa error apa pun.
"""
from decimal import Decimal

from rest_framework import serializers

from .models import (
    BuktiTerima, JejakPosisi, Kendaraan, Pengiriman, Perhentian, Retur,
    TarifOngkos,
)


class KendaraanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kendaraan
        fields = ['id', 'kode', 'nama', 'plat_nomor', 'kapasitas_kg', 'aktif']


class TarifOngkosSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarifOngkos
        fields = ['id', 'berlaku_sejak', 'tarif_per_km', 'biaya_tetap']


class BuktiTerimaSerializer(serializers.ModelSerializer):
    diunggah_oleh_nama = serializers.SerializerMethodField()

    class Meta:
        model = BuktiTerima
        fields = ['id', 'foto', 'lat', 'lng', 'waktu', 'catatan',
                  'diunggah_oleh_nama']

    def get_diunggah_oleh_nama(self, obj):
        u = obj.diunggah_oleh
        return (u.get_full_name() or u.get_username()) if u else None


class ReturSerializer(serializers.ModelSerializer):
    dicatat_oleh_nama = serializers.SerializerMethodField()
    disetujui_oleh_nama = serializers.SerializerMethodField()
    pelanggan_nama = serializers.CharField(
        source='perhentian.pelanggan_nama', read_only=True)
    nomor_distribusi = serializers.CharField(
        source='perhentian.nomor_distribusi', read_only=True)
    menunggu_persetujuan = serializers.BooleanField(read_only=True)

    class Meta:
        model = Retur
        fields = ['id', 'perhentian', 'nomor_distribusi', 'pelanggan_nama',
                  'alasan', 'foto', 'dicatat_pada', 'dicatat_oleh_nama',
                  'disetujui_pada', 'disetujui_oleh_nama',
                  'stok_dikembalikan', 'menunggu_persetujuan']

    def get_dicatat_oleh_nama(self, obj):
        u = obj.dicatat_oleh
        return (u.get_full_name() or u.get_username()) if u else None

    def get_disetujui_oleh_nama(self, obj):
        u = obj.disetujui_oleh
        return (u.get_full_name() or u.get_username()) if u else None


class PerhentianSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    bukti = BuktiTerimaSerializer(many=True, read_only=True)
    diretur = serializers.SerializerMethodField()

    class Meta:
        model = Perhentian
        fields = [
            'id', 'distribusi_id', 'nomor_distribusi', 'pelanggan_nama',
            'urutan', 'urutan_usulan', 'alamat', 'lat', 'lng',
            'jarak_dari_sebelum_km', 'estimasi_menit',
            'status', 'status_label', 'waktu_sampai', 'bukti', 'diretur',
        ]

    def get_diretur(self, obj):
        return hasattr(obj, 'retur')


class PengirimanSerializer(serializers.ModelSerializer):
    """Bentuk daftar. Detail memakai turunannya di bawah."""

    status_label = serializers.CharField(source='get_status_display', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    kurir_nama = serializers.SerializerMethodField()
    kendaraan_kode = serializers.SerializerMethodField()
    jumlah_perhentian = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pengiriman
        fields = [
            'id', 'nomor', 'tanggal', 'entitas_kode', 'kurir', 'kurir_nama',
            'kendaraan', 'kendaraan_kode', 'status', 'status_label',
            'waktu_berangkat', 'waktu_selesai', 'jarak_total_km',
            'ongkos_perkiraan', 'jumlah_perhentian', 'catatan',
        ]

    def get_kurir_nama(self, obj):
        u = obj.kurir
        return (u.get_full_name() or u.get_username()) if u else None

    def get_kendaraan_kode(self, obj):
        return obj.kendaraan.kode if obj.kendaraan_id else None


class PengirimanDetailSerializer(PengirimanSerializer):
    perhentian = PerhentianSerializer(many=True, read_only=True)

    class Meta(PengirimanSerializer.Meta):
        fields = PengirimanSerializer.Meta.fields + ['perhentian']


# =========================================================
# TULIS
# =========================================================

class RakitPengirimanSerializer(serializers.Serializer):
    entitas_id = serializers.IntegerField()
    kurir_id = serializers.IntegerField()
    distribusi_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False)
    tanggal = serializers.DateField(required=False, allow_null=True)
    kendaraan_id = serializers.IntegerField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')


class UrutRuteSerializer(serializers.Serializer):
    """Urutan baru dari orang. Menimpa usulan sistem, dan itu disengaja."""
    urutan = serializers.ListField(child=serializers.IntegerField(),
                                   allow_empty=False)


class PakaiUsulanSerializer(serializers.Serializer):
    pakai_usulan = serializers.BooleanField(default=False)


class BuktiTerimaUploadSerializer(serializers.Serializer):
    foto = serializers.ImageField()
    catatan = serializers.CharField(required=False, allow_blank=True, default='')
    lat = serializers.DecimalField(max_digits=10, decimal_places=7,
                                   required=False, allow_null=True)
    lng = serializers.DecimalField(max_digits=10, decimal_places=7,
                                   required=False, allow_null=True)


class CatatReturSerializer(serializers.Serializer):
    alasan = serializers.CharField(allow_blank=False, max_length=1000)
    foto = serializers.ImageField(required=False, allow_null=True)


class PosisiSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    lng = serializers.DecimalField(max_digits=10, decimal_places=7)
    akurasi_m = serializers.IntegerField(required=False, allow_null=True,
                                         min_value=0)


class JejakPosisiSerializer(serializers.ModelSerializer):
    class Meta:
        model = JejakPosisi
        fields = ['id', 'lat', 'lng', 'akurasi_m', 'waktu']


class BatalPengirimanSerializer(serializers.Serializer):
    alasan = serializers.CharField(allow_blank=False, max_length=500)
