"""
Serializer persediaan — inventory/serializers.py

DUA SERIALIZER UNTUK STOK, kelas terpisah (bukan filter pop()), sama
seperti warehouse/serializers.py:

    StokGudangSerializer     qty, produk, lapis, grup, tangki -- TIDAK ADA
                             nilai atau harga apa pun.
    StokAkuntingSerializer   + nilai dan harga_rata, dihitung dari
                             SaldoEntitas. Hanya untuk modul akunting.

Alasannya sama seperti gudang penerimaan: staff gudang yang tahu nilai
rupiah punya insentif menyesuaikan hasil timbangan.
"""
from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Lapis, MutasiKlaim, MutasiStok, NilaiEkuivalen, PosisiKlaim, SaldoEntitas,
    Stok, Tangki,
)

Q2 = Decimal('0.01')


# =========================================================
# TANGKI
# =========================================================

class TangkiSerializer(serializers.ModelSerializer):
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    produk_terisi_kode = serializers.CharField(source='produk_terisi.kode',
                                               read_only=True, default=None)
    ruang_kosong_kg = serializers.DecimalField(max_digits=14, decimal_places=3,
                                               read_only=True)
    persen_terisi = serializers.DecimalField(max_digits=5, decimal_places=1,
                                             read_only=True)

    class Meta:
        model = Tangki
        fields = ['id', 'kode', 'nama', 'grup_bahan', 'grup_bahan_kode',
                  'kapasitas_kg', 'isi_kg', 'produk_terisi',
                  'produk_terisi_kode', 'ruang_kosong_kg', 'persen_terisi',
                  'aktif']


# =========================================================
# STOK -- rincian kepemilikan (detail)
# =========================================================

class KepemilikanGudangSerializer(serializers.ModelSerializer):
    """Siapa memiliki berapa. TIDAK ADA nilai rupiah."""

    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)

    class Meta:
        model = SaldoEntitas
        fields = ['entitas', 'entitas_kode', 'qty']


class KepemilikanAkuntingSerializer(KepemilikanGudangSerializer):
    class Meta(KepemilikanGudangSerializer.Meta):
        fields = KepemilikanGudangSerializer.Meta.fields + ['nilai']


# =========================================================
# STOK -- sisi gudang (TANPA HARGA)
# =========================================================

class StokGudangSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    lapis_label = serializers.CharField(source='get_lapis_display', read_only=True)
    tangki_kode = serializers.CharField(source='tangki.kode', read_only=True,
                                        default=None)

    class Meta:
        model = Stok
        # nilai dan harga TIDAK ADA. Jangan ditambahkan -- lihat
        # StokAkuntingSerializer.
        fields = ['id', 'produk', 'produk_kode', 'grup_bahan',
                  'grup_bahan_kode', 'lapis', 'lapis_label', 'tangki',
                  'tangki_kode', 'qty']


class StokGudangDetailSerializer(StokGudangSerializer):
    kepemilikan = KepemilikanGudangSerializer(many=True, read_only=True)

    class Meta(StokGudangSerializer.Meta):
        fields = StokGudangSerializer.Meta.fields + ['kepemilikan']


# =========================================================
# STOK -- sisi akunting (dengan nilai)
# =========================================================

class StokAkuntingSerializer(StokGudangSerializer):
    """Menambahkan nilai dan harga rata-rata dari SaldoEntitas.

    POOL tidak pernah punya SaldoEntitas, jadi keduanya None di lapis itu
    -- itu benar, bukan bug (lihat models.py: kepemilikan pool ada di
    MutasiKlaim/PosisiKlaim, bukan di sini).
    """

    nilai = serializers.SerializerMethodField()
    harga_rata = serializers.SerializerMethodField()

    class Meta(StokGudangSerializer.Meta):
        fields = StokGudangSerializer.Meta.fields + ['nilai', 'harga_rata']

    def get_nilai(self, obj):
        if not obj.berpemilik:
            return None
        return (obj.kepemilikan.aggregate(t=Sum('nilai'))['t']
                or Decimal('0')).quantize(Q2)

    def get_harga_rata(self, obj):
        nilai = self.get_nilai(obj)
        if nilai is None or not obj.qty:
            return None
        return (nilai / obj.qty).quantize(Q2)


class StokAkuntingDetailSerializer(StokAkuntingSerializer):
    kepemilikan = KepemilikanAkuntingSerializer(many=True, read_only=True)

    class Meta(StokAkuntingSerializer.Meta):
        fields = StokAkuntingSerializer.Meta.fields + ['kepemilikan']


# =========================================================
# MUTASI STOK -- append-only
# =========================================================

class MutasiStokSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='stok.produk.kode', read_only=True)
    lapis = serializers.CharField(source='stok.lapis', read_only=True)
    jenis_label = serializers.CharField(source='get_jenis_display', read_only=True)

    class Meta:
        model = MutasiStok
        fields = ['id', 'stok', 'produk_kode', 'lapis', 'urutan', 'tanggal',
                  'jenis', 'jenis_label', 'masuk', 'keluar', 'saldo_akhir',
                  'referensi', 'dibuat_pada']


# =========================================================
# BUKU KLAIM & POSISI -- append-only
# =========================================================

class MutasiKlaimSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    produk_kode = serializers.CharField(source='produk.kode', read_only=True,
                                        default=None)

    class Meta:
        model = MutasiKlaim
        fields = ['id', 'entitas', 'entitas_kode', 'grup_bahan',
                  'grup_bahan_kode', 'tanggal', 'jenis', 'produk',
                  'produk_kode', 'qty', 'tarif', 'nilai', 'referensi',
                  'dibuat_pada']


class PosisiKlaimSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    berhutang = serializers.BooleanField(read_only=True)

    class Meta:
        model = PosisiKlaim
        fields = ['id', 'entitas', 'entitas_kode', 'grup_bahan',
                  'grup_bahan_kode', 'total_setor', 'total_ambil',
                  'nilai_bersih', 'berhutang']


# =========================================================
# NILAI EKUIVALEN
# =========================================================

class NilaiEkuivalenSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)

    class Meta:
        model = NilaiEkuivalen
        fields = ['id', 'produk', 'produk_kode', 'nilai_per_satuan',
                  'berlaku_sejak', 'catatan']


# =========================================================
# PAYLOAD PENULISAN -- diteruskan langsung ke services.*
# =========================================================

class SetorKePoolSerializer(serializers.Serializer):
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    entitas_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_raw_id = serializers.IntegerField(required=False, allow_null=True)
    tangki_pool_id = serializers.IntegerField(required=False, allow_null=True)


class KlaimHasilSerializer(serializers.Serializer):
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    entitas_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_pool_id = serializers.IntegerField(required=False, allow_null=True)
    nilai_perolehan = serializers.DecimalField(max_digits=18, decimal_places=2,
                                               required=False, allow_null=True)


class OpnameSerializer(serializers.Serializer):
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    lapis = serializers.ChoiceField(choices=Lapis.choices)
    qty_fisik = serializers.DecimalField(max_digits=14, decimal_places=3)
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_id = serializers.IntegerField(required=False, allow_null=True)
    entitas_id = serializers.IntegerField(required=False, allow_null=True)
    nilai_penyesuaian = serializers.DecimalField(max_digits=18, decimal_places=2,
                                                 required=False, allow_null=True)
