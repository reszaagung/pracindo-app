"""
Serializer persediaan — inventory/serializers.py

DUA SERIALIZER UNTUK STOK, kelas terpisah (bukan filter pop()):

    StokGudangSerializer     qty, produk, lapis, grup, tangki -- TIDAK ADA
                             nilai atau harga apa pun.
    StokAkuntingSerializer   + nilai dan harga_rata.

Alasannya: staff gudang yang tahu nilai rupiah punya insentif
menyesuaikan hasil timbangan.

CATATAN TARIF
    `harga_rata` di sini angka TAMPILAN. Jangan pernah dipakai klien
    untuk menghitung sendiri berapa hak yang akan berkurang -- hasilnya
    akan meleset dari server karena server memakai proporsi, bukan
    qty x tarif. Pakai endpoint /rencana-kemasan/ untuk pratinjau.
"""
from decimal import Decimal

from rest_framework import serializers
from inventory.services import verifikasi_pool_bersih
from .models import (
    Kemasan, Lapis, MutasiKlaim, MutasiStok, NilaiEkuivalen, PosisiKlaim,
    SaldoEntitas, Stok, Tangki,
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
# KEMASAN
# =========================================================

class KemasanSerializer(serializers.ModelSerializer):
    produk_curah_kode = serializers.CharField(source='produk_curah.kode',
                                              read_only=True)
    produk_kemasan_kode = serializers.CharField(source='produk_kemasan.kode',
                                                read_only=True)
    produk_kemasan_nama = serializers.CharField(source='produk_kemasan.nama',
                                                read_only=True)

    class Meta:
        model = Kemasan
        fields = ['id', 'produk_curah', 'produk_curah_kode', 'produk_kemasan',
                  'produk_kemasan_kode', 'produk_kemasan_nama', 'isi', 'aktif']


# =========================================================
# STOK -- rincian kepemilikan
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


class StokGudangSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    lapis_label = serializers.CharField(source='get_lapis_display', read_only=True)
    tangki_kode = serializers.CharField(source='tangki.kode', read_only=True,
                                        default=None)

    class Meta:
        model = Stok
        # nilai dan harga TIDAK ADA. Jangan ditambahkan.
        fields = ['id', 'produk', 'produk_kode', 'grup_bahan',
                  'grup_bahan_kode', 'lapis', 'lapis_label', 'tangki',
                  'tangki_kode', 'qty']


class StokGudangDetailSerializer(StokGudangSerializer):
    kepemilikan = KepemilikanGudangSerializer(many=True, read_only=True)

    class Meta(StokGudangSerializer.Meta):
        fields = StokGudangSerializer.Meta.fields + ['kepemilikan']


class StokGudangListRinciSerializer(StokGudangSerializer):
    """
    DAFTAR stok + rincian kepemilikan. Tetap TANPA rupiah.

    Dipakai form setor-ke-pool, yang harus tahu "PT punya 6 kg dari 10 kg
    di baris ini". Tanpa ini frontend tidak punya cara menentukan pemilik
    baris RAW selain memanggil /stok/{id}/ satu per satu -- dan versi
    sebelumnya menebaknya dari grup_bahan, lalu mengirim id GrupBahan
    sebagai entitas_id.

    Aktif lewat ?rinci=1. Sengaja TIDAK punya padanan akunting: yang butuh
    nilai per entitas memakai endpoint detail. Menambahkan rupiah ke daftar
    berarti setiap layar gudang yang memuat daftar stok ikut membawanya.

    CATATAN untuk klien: batas qty yang boleh disetor entitas X adalah
    kepemilikan[X].qty, BUKAN stok.qty. Menyetor melebihi hak sendiri
    menembus hak pemilik lain di baris yang sama, dan _geser_pemilik()
    akan menolaknya dengan ValidationError.
    """
    kepemilikan = KepemilikanGudangSerializer(many=True, read_only=True)

    class Meta(StokGudangSerializer.Meta):
        fields = StokGudangSerializer.Meta.fields + ['kepemilikan']


class StokAkuntingSerializer(StokGudangSerializer):
    """
    Nilai dibaca langsung dari kolom, bukan dihitung ulang dari
    SaldoEntitas. POOL memang tidak punya SaldoEntitas dan tetap
    bernilai -- itu inti perubahannya.
    """
    harga_rata = serializers.DecimalField(max_digits=18, decimal_places=4,
                                          read_only=True)

    class Meta(StokGudangSerializer.Meta):
        fields = StokGudangSerializer.Meta.fields + ['nilai', 'harga_rata']


class StokAkuntingDetailSerializer(StokAkuntingSerializer):
    kepemilikan = KepemilikanAkuntingSerializer(many=True, read_only=True)

    class Meta(StokAkuntingSerializer.Meta):
        fields = StokAkuntingSerializer.Meta.fields + ['kepemilikan']


# =========================================================
# MUTASI -- append-only
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


class MutasiStokAkuntingSerializer(MutasiStokSerializer):
    class Meta(MutasiStokSerializer.Meta):
        fields = MutasiStokSerializer.Meta.fields + [
            'nilai_masuk', 'nilai_keluar', 'saldo_nilai']


class MutasiKlaimSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    produk_kode = serializers.CharField(source='produk.kode', read_only=True,
                                        default=None)
    jenis_label = serializers.CharField(source='get_jenis_display', read_only=True)

    class Meta:
        model = MutasiKlaim
        fields = ['id', 'entitas', 'entitas_kode', 'grup_bahan',
                  'grup_bahan_kode', 'tanggal', 'jenis', 'jenis_label',
                  'produk', 'produk_kode', 'qty', 'tarif', 'nilai',
                  'referensi', 'dibuat_pada']


class PosisiKlaimSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    berhutang = serializers.BooleanField(read_only=True)

    class Meta:
        model = PosisiKlaim
        fields = ['id', 'entitas', 'entitas_kode', 'grup_bahan',
                  'grup_bahan_kode', 'total_setor', 'total_ambil',
                  'total_rugi', 'nilai_bersih', 'berhutang']


class NilaiEkuivalenSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)

    class Meta:
        model = NilaiEkuivalen
        fields = ['id', 'produk', 'produk_kode', 'nilai_per_satuan',
                  'berlaku_sejak', 'catatan']


# =========================================================
# PAYLOAD PENULISAN
# =========================================================

class SetorKePoolSerializer(serializers.Serializer):
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    entitas_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3,
                                   min_value=Decimal('0.001'))
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_raw_id = serializers.IntegerField(required=False, allow_null=True)
    tangki_pool_id = serializers.IntegerField(required=False, allow_null=True)


class KlaimHasilSerializer(serializers.Serializer):
    """Klaim curah sebagai curah. Satuan tidak berubah."""
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    entitas_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3,
                                   min_value=Decimal('0.001'))
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_pool_id = serializers.IntegerField(required=False, allow_null=True)


class KlaimKemasanSerializer(serializers.Serializer):
    """
    Pengepakan. `jumlah` dalam satuan kemasan (pcs), bukan kg.

    `qty_curah_aktual` diisi kalau timbangan menunjukkan curah yang
    keluar berbeda dari jumlah x isi. Kosongkan kalau normal.
    """
    kemasan_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    entitas_id = serializers.IntegerField()
    jumlah = serializers.DecimalField(max_digits=14, decimal_places=3,
                                      min_value=Decimal('0.001'))
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_pool_id = serializers.IntegerField(required=False, allow_null=True)
    qty_curah_aktual = serializers.DecimalField(
        max_digits=14, decimal_places=3, required=False, allow_null=True)


class OpnameSerializer(serializers.Serializer):
    produk_id = serializers.IntegerField()
    grup_bahan_id = serializers.IntegerField()
    lapis = serializers.ChoiceField(choices=Lapis.choices)
    qty_fisik = serializers.DecimalField(max_digits=14, decimal_places=3,
                                         min_value=Decimal('0'))
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    tangki_id = serializers.IntegerField(required=False, allow_null=True)
    entitas_id = serializers.IntegerField(required=False, allow_null=True)
    nilai_penyesuaian = serializers.DecimalField(max_digits=18, decimal_places=2,
                                                 required=False, allow_null=True)


class LunasSerializer(serializers.Serializer):
    """Pelunasan WAJIB dua sisi supaya total klaim grup tidak bergeser."""
    grup_bahan_id = serializers.IntegerField()
    entitas_bayar_id = serializers.IntegerField()
    entitas_terima_id = serializers.IntegerField()
    nilai = serializers.DecimalField(max_digits=18, decimal_places=2,
                                     min_value=Decimal('0.01'))
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')


class LuruskanSerializer(serializers.Serializer):
    grup_bahan_id = serializers.IntegerField()
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True,
                                      default='Selisih pembulatan')
    idem_key = serializers.CharField(required=False, allow_blank=True, default='')
    batas = serializers.DecimalField(max_digits=18, decimal_places=2,
                                     required=False, default=Decimal('1.00'))