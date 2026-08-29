"""Serializer master data — master/serializers.py"""
from rest_framework import serializers

from .models import Kategori, Pelanggan, Produk, Satuan, Suplier , MasterProduk


class KategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategori
        fields = ['id', 'kode', 'nama']


class SatuanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Satuan
        fields = ['id', 'kode', 'nama']


class ProdukSerializer(serializers.ModelSerializer):
    kategori_nama = serializers.CharField(source='kategori.nama',
                                          read_only=True, default=None)
    satuan_kode = serializers.CharField(source='satuan.kode', read_only=True)
    jenis_label = serializers.CharField(source='get_jenis_display', read_only=True)

    class Meta:
        model = Produk
        fields = ['id', 'kode', 'nama', 'jenis', 'jenis_label',
                  'kategori', 'kategori_nama', 'satuan', 'satuan_kode',
                  'disimpan_di_tanki', 'aktif', 'suplier']


class ProdukRingkasSerializer(serializers.ModelSerializer):
    """Untuk dropdown. Cukup yang dibutuhkan form PO."""

    satuan_kode = serializers.CharField(source='satuan.kode', read_only=True)

    class Meta:
        model = Produk
        fields = ['id', 'kode', 'nama', 'satuan_kode', 'jenis', 'suplier']


class SuplierSerializer(serializers.ModelSerializer):
    pkp = serializers.BooleanField(read_only=True)

    class Meta:
        model = Suplier
        fields = ['id', 'kode', 'nama', 'npwp', 'pkp', 'alamat',
                  'kontak_nama', 'kontak_hp', 'email',
                  'termin_hari_default', 'aktif']


class SuplierRingkasSerializer(serializers.ModelSerializer):
    """
    Untuk dropdown form PO. termin_hari_default ikut supaya form faktur
    nanti bisa mengisi nilai awal tanpa request tambahan.
    """

    class Meta:
        model = Suplier
        fields = ['id', 'kode', 'nama', 'termin_hari_default']


class PelangganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pelanggan
        fields = ['id', 'kode', 'nama', 'npwp', 'alamat',
                  'kontak_nama', 'kontak_hp',
                  'termin_hari_default', 'plafon_kredit', 'aktif']

class PelangganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pelanggan
        fields = ['id', 'kode', 'nama', 'npwp', 'alamat',
                  'kontak_nama', 'kontak_hp',
                  'termin_hari_default', 'plafon_kredit', 'aktif']

class MasterProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterProduk
        fields = ['id', 'nama_item']