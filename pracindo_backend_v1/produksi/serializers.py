"""
Serializer produksi — produksi/serializers.py

Nilai rupiah hanya muncul di serializer yang dipakai supervisor dan
akunting. Operator lantai melihat qty, tangki, dan rendemen — tidak
melihat rupiah. Alasannya sama seperti di gudang penerimaan: orang yang
tahu nilai rupiah punya insentif menyesuaikan hasil timbangan.

IDEMPOTENSI
    BuatSesiProduksiSerializer dan BuatSesiRndSerializer menerima
    `idem_key`. Sebelumnya tidak, sehingga frontend yang mengirimkannya
    tidak dicegah apa-apa: DRF Serializer membuang key asing TANPA SUARA,
    jadi klik ganda tetap melahirkan dua sesi DRAFT sementara UI
    menampilkan "kirim ulang aman". Lebih berbahaya daripada tidak ada
    penjaga sama sekali, karena operator justru didorong mengulang.
"""
from decimal import Decimal

from rest_framework import serializers

from .models import (
    HasilKomponen, JenisPengukuran, Resep, SesiCatatan, SesiInput,
    SesiPengukuran, SesiProduksi,
)


# =========================================================
# BACA
# =========================================================

class SesiListSerializer(serializers.ModelSerializer):
    """Daftar sesi. TANPA rupiah."""
    produk_jadi_kode = serializers.CharField(source='produk_jadi.kode', read_only=True)
    produk_jadi_nama = serializers.CharField(source='produk_jadi.nama', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    satuan_kode = serializers.CharField(source='produk_jadi.satuan_kode',
                                        read_only=True, default='unit')
    tangki_hasil_kode = serializers.CharField(source='tangki_hasil.kode',
                                              read_only=True, default=None)
    dibuat_oleh_nama = serializers.CharField(source='dibuat_oleh.get_full_name',
                                             read_only=True, default='Sistem')

    class Meta:
        model = SesiProduksi
        fields = [
            'id', 'nomor', 'tanggal', 'status', 'grup_bahan_kode',
            'produk_jadi_kode', 'produk_jadi_nama', 'qty_target', 'qty_hasil',
            'rendemen', 'satuan_kode', 'jenis_sesi', 'hasil_masuk_pool',
            'tangki_hasil_kode', 'dibuat_oleh_nama',
        ]


class SesiListAkuntingSerializer(SesiListSerializer):
    """Idem, dengan rupiah. Hanya untuk yang punya akses modul akunting."""
    harga_hasil_per_satuan = serializers.DecimalField(
        max_digits=18, decimal_places=4, read_only=True)

    class Meta(SesiListSerializer.Meta):
        fields = SesiListSerializer.Meta.fields + [
            'nilai_input', 'nilai_hasil', 'nilai_kerugian',
            'harga_hasil_per_satuan',
        ]


class ResepSerializer(serializers.ModelSerializer):
    produk_jadi_kode = serializers.CharField(source='produk_jadi.kode', read_only=True)
    produk_jadi_nama = serializers.CharField(source='produk_jadi.nama', read_only=True)
    susut_wajar_persen = serializers.SerializerMethodField()

    class Meta:
        model = Resep
        fields = ['id', 'produk_jadi', 'produk_jadi_kode', 'produk_jadi_nama',
                  'versi', 'nama', 'hasil_per_batch', 'susut_wajar',
                  'susut_wajar_persen', 'berlaku_sejak']

    def get_susut_wajar_persen(self, obj):
        return obj.susut_wajar * 100


class HasilKomponenSerializer(serializers.ModelSerializer):
    bahan_kode = serializers.CharField(source='bahan.kode', read_only=True)
    bahan_nama = serializers.CharField(source='bahan.nama', read_only=True)

    class Meta:
        model = HasilKomponen
        fields = ['id', 'bahan', 'bahan_kode', 'bahan_nama',
                  'sesi_input', 'qty', 'nilai']
        read_only_fields = fields


class SesiInputSerializer(serializers.ModelSerializer):
    bahan_kode = serializers.CharField(source='bahan.kode', read_only=True)
    bahan_nama = serializers.CharField(source='bahan.nama', read_only=True)
    tangki_kode = serializers.CharField(source='tangki.kode', read_only=True,
                                        default=None)

    class Meta:
        model = SesiInput
        fields = ['id', 'bahan', 'bahan_kode', 'bahan_nama', 'tangki',
                  'tangki_kode', 'qty_rencana', 'qty_aktual', 'selisih']


# =========================================================
# TULIS
# =========================================================

class BuatSesiProduksiSerializer(serializers.Serializer):
    grup_bahan_id = serializers.IntegerField()
    resep_id = serializers.IntegerField()
    qty_target = serializers.DecimalField(max_digits=14, decimal_places=3,
                                          min_value=Decimal('0.001'))
    tanggal = serializers.DateField()
    tangki_hasil_id = serializers.IntegerField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')
    # Kunci idempotensi. Dibuat SEKALI saat form dibuka dan dipakai ulang di
    # setiap percobaan kirim -- kalau diganti tiap retry, tidak mencegah apa
    # pun. Dikosongkan berarti tanpa penjaga: klik ganda melahirkan dua sesi.
    idem_key = serializers.CharField(required=False, allow_blank=True,
                                     default='', max_length=96)


class RndBarisInputSerializer(serializers.Serializer):
    bahan_id = serializers.IntegerField()
    qty_rencana = serializers.DecimalField(max_digits=14, decimal_places=3,
                                           min_value=Decimal('0.001'))
    tangki_id = serializers.IntegerField(required=False, allow_null=True)


class BuatSesiRndSerializer(serializers.Serializer):
    grup_bahan_id = serializers.IntegerField()
    produk_jadi_id = serializers.IntegerField()
    qty_target = serializers.DecimalField(max_digits=14, decimal_places=3,
                                          min_value=Decimal('0.001'))
    tanggal = serializers.DateField()
    hasil_masuk_pool = serializers.BooleanField(default=True)
    tangki_hasil_id = serializers.IntegerField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True,
                                     default='', max_length=96)
    baris = RndBarisInputSerializer(many=True, allow_empty=False)


class MulaiSesiBarisSerializer(serializers.Serializer):
    bahan_id = serializers.IntegerField()
    # Nol DIIZINKAN: cara operator bilang bahan ini tidak jadi dipakai.
    qty_aktual = serializers.DecimalField(max_digits=14, decimal_places=3,
                                          min_value=Decimal('0'))
    tangki_id = serializers.IntegerField(required=False, allow_null=True)


class MulaiSesiSerializer(serializers.Serializer):
    baris = MulaiSesiBarisSerializer(many=True, required=False, default=list)


class SelesaikanSesiSerializer(serializers.Serializer):
    qty_hasil = serializers.DecimalField(max_digits=14, decimal_places=3,
                                         min_value=Decimal('0.001'))
    # Menembus batas susut wajar. Ditolak view kalau bukan supervisor.
    abaikan_susut = serializers.BooleanField(default=False)


class GagalkanSesiSerializer(serializers.Serializer):
    alasan = serializers.CharField(allow_blank=False)
    kategori_kegagalan = serializers.CharField(allow_blank=False)


class BatalSesiSerializer(serializers.Serializer):
    alasan = serializers.CharField(allow_blank=False)


# =========================================================
# PENGUKURAN & CATATAN
# =========================================================

class JenisPengukuranSerializer(serializers.ModelSerializer):
    class Meta:
        model = JenisPengukuran
        fields = ['id', 'kode', 'nama', 'satuan', 'tipe_nilai',
                  'nilai_min', 'nilai_max', 'aktif']


class SesiPengukuranSerializer(serializers.ModelSerializer):
    nama_kode = serializers.CharField(source='nama.kode', read_only=True)
    nama_label = serializers.CharField(source='nama.nama', read_only=True)
    satuan = serializers.CharField(source='nama.satuan', read_only=True)
    dicatat_oleh_nama = serializers.CharField(source='dicatat_oleh.get_full_name',
                                              read_only=True, default='Sistem')

    class Meta:
        model = SesiPengukuran
        fields = ['id', 'sesi', 'tahap', 'nama', 'nama_kode', 'nama_label',
                  'satuan', 'nilai', 'nilai_teks', 'waktu', 'catatan',
                  'mengoreksi', 'dicatat_oleh_nama']
        read_only_fields = ['id', 'sesi', 'waktu', 'dicatat_oleh']


class SesiCatatanSerializer(serializers.ModelSerializer):
    penulis_nama = serializers.CharField(source='penulis.get_full_name',
                                         read_only=True, default='Sistem')

    class Meta:
        model = SesiCatatan
        fields = ['id', 'sesi', 'waktu', 'teks', 'penulis_nama']
        read_only_fields = ['id', 'sesi', 'waktu', 'penulis']