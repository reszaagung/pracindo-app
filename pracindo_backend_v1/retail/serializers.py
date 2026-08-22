from rest_framework import serializers
from .serializers import (
    KatalogPOSSerializer, RiwayatTransaksiSerializer, SesiKasirSerializer,
    AkunBukuBesarSerializer, TransaksiJurnalSerializer,
    PelangganRetailSerializer, SalesRetailSerializer
)

class KatalogPOSSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='produk.id', read_only=True)
    nama = serializers.CharField(source='produk.nama', read_only=True)
    barcode = serializers.CharField(source='produk.barcode', default='NO-BARCODE', read_only=True)

    stok = serializers.IntegerField(source='qty', read_only=True)
    harga = serializers.DecimalField(source='harga_jual', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = StokRetail
        fields = ['id', 'nama', 'barcode', 'stok', 'harga']


class RiwayatTransaksiSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransaksiPOS
        fields = [
            'id', 'nomor_struk', 'waktu_transaksi', 
            'subtotal', 'pajak', 'grand_total', 
            'metode_bayar', 'status'
        ]


class SesiKasirSerializer(serializers.ModelSerializer):
    kasir_nama = serializers.CharField(source='kasir.username', read_only=True)
    cabang_nama = serializers.CharField(source='cabang.nama', read_only=True)

    class Meta:
        model = SesiKasir
        fields = [
            'id', 'cabang_nama', 'kasir_nama', 'waktu_buka', 
            'waktu_tutup', 'saldo_awal', 'total_penjualan', 'status'
        ]


class KategoriAkunSerializer(serializers.ModelSerializer):
    class Meta:
        model = KategoriAkun
        fields = '__all__'


class AkunBukuBesarSerializer(serializers.ModelSerializer):
    kategori_nama = serializers.CharField(source='kategori.nama', read_only=True)
    tipe_saldo = serializers.CharField(source='kategori.tipe_saldo', read_only=True)

    class Meta:
        model = AkunBukuBesar
        fields = ['id', 'kode', 'nama', 'kategori', 'kategori_nama', 'tipe_saldo', 'cabang', 'aktif']


class DetailJurnalSerializer(serializers.ModelSerializer):
    akun_nama = serializers.CharField(source='akun.nama', read_only=True)
    akun_kode = serializers.CharField(source='akun.kode', read_only=True)

    class Meta:
        model = DetailJurnal
        fields = ['id', 'akun', 'akun_kode', 'akun_nama', 'debit', 'kredit']


class TransaksiJurnalSerializer(serializers.ModelSerializer):
    item_jurnal = DetailJurnalSerializer(many=True, read_only=True)
    
    class Meta:
        model = TransaksiJurnal
        fields = ['id', 'nomor_jurnal', 'tanggal', 'referensi', 'keterangan', 'cabang', 'item_jurnal']

class SalesRetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRetail
        fields = ['id', 'nama', 'persentase_bonus']

class PelangganRetailSerializer(serializers.ModelSerializer):
    sales_nama = serializers.CharField(source='sales.nama', read_only=True)

    class Meta:
        model = PelangganRetail
        fields = ['id', 'nama', 'nomor_telepon', 'alamat', 'limit_piutang', 'default_tempo_hari', 'sales', 'sales_nama']