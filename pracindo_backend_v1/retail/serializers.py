from rest_framework import serializers

# Pastikan import ini mengambil dari .models, bukan .serializers
from .models import (
    StokRetail, TransaksiPOS, SesiKasir,
    KategoriAkun, AkunBukuBesar, TransaksiJurnal, DetailJurnal,
    SalesRetail, PelangganRetail,
    BukuPiutangRetail, RiwayatBayarPiutang,
    SuratJalan
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
    akun_kode = serializers.CharField(source='akun.kode', read_only=True)
    akun_nama = serializers.CharField(source='akun.nama', read_only=True)

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


class RiwayatBayarPiutangSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiwayatBayarPiutang
        fields = '__all__'


class BukuPiutangRetailSerializer(serializers.ModelSerializer):
    pelanggan_nama = serializers.CharField(source='pelanggan.nama', read_only=True)
    nomor_struk = serializers.CharField(source='transaksi.nomor_struk', read_only=True)
    sisa_piutang = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    umur_piutang_hari = serializers.IntegerField(read_only=True)
    sisa_hari_jatuh_tempo = serializers.IntegerField(read_only=True)
    riwayat_bayar = RiwayatBayarPiutangSerializer(many=True, read_only=True)

    class Meta:
        model = BukuPiutangRetail
        fields = [
            'id', 'pelanggan', 'pelanggan_nama', 'nomor_struk', 
            'tanggal_piutang', 'jatuh_tempo', 'total_piutang', 
            'total_dibayar', 'sisa_piutang', 'status', 
            'umur_piutang_hari', 'sisa_hari_jatuh_tempo', 'riwayat_bayar'
        ]


class SuratJalanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuratJalan
        fields = '__all__'

class MutasiBukuBesarSerializer(serializers.ModelSerializer):
    tanggal = serializers.DateTimeField(source='jurnal.tanggal', read_only=True)
    nomor_jurnal = serializers.CharField(source='jurnal.nomor_jurnal', read_only=True)
    keterangan = serializers.CharField(source='jurnal.keterangan', read_only=True)
    referensi = serializers.CharField(source='jurnal.referensi', read_only=True)

    class Meta:
        model = DetailJurnal
        fields = ['id', 'tanggal', 'nomor_jurnal', 'referensi', 'keterangan', 'debit', 'kredit']