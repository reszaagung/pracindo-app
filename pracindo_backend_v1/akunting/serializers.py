"""
Serializer akunting — akunting/serializers.py

CATATAN PENTING
    Serializer di file ini memuat harga dan nilai rupiah. Untuk gudang
    ada serializer TERPISAH di warehouse/serializers.py yang sama sekali
    tidak punya field harga -- bukan bernilai null, tapi field-nya memang
    tidak ada di kelasnya.

    Itu disengaja. Filter berbasis pop() gampang bocor lewat ?expand=,
    nested serializer, atau endpoint baru yang lupa dipasang. Kalau
    field-nya tidak pernah ada, tidak ada jalur kebocoran.
"""
from rest_framework import serializers

from .models import (
    Akun, FakturPembelian, FakturPenjualan, JurnalDetail, JurnalUmum,
    KartuHutang, PurchaseOrder, PurchaseOrderItem, UangMukaSuplier,
)


# =========================================================
# BAGAN AKUN & JURNAL
# =========================================================

class AkunSerializer(serializers.ModelSerializer):
    saldo_normal = serializers.CharField(read_only=True)

    class Meta:
        model = Akun
        fields = ['id', 'kode', 'nama', 'tipe', 'saldo_normal', 'parent',
                  'boleh_diposting', 'aktif']


class JurnalDetailSerializer(serializers.ModelSerializer):
    akun_kode = serializers.CharField(source='akun.kode', read_only=True)
    akun_nama = serializers.CharField(source='akun.nama', read_only=True)

    class Meta:
        model = JurnalDetail
        fields = ['id', 'akun', 'akun_kode', 'akun_nama',
                  'debit', 'kredit', 'keterangan']


class JurnalUmumSerializer(serializers.ModelSerializer):
    baris = JurnalDetailSerializer(many=True, read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    total_debit  = serializers.DecimalField(max_digits=18, decimal_places=2,
                                            read_only=True)
    total_kredit = serializers.DecimalField(max_digits=18, decimal_places=2,
                                            read_only=True)
    seimbang = serializers.BooleanField(read_only=True)
    sudah_dibalik = serializers.BooleanField(read_only=True)

    class Meta:
        model = JurnalUmum
        fields = ['id', 'nomor', 'tanggal', 'entitas', 'entitas_kode',
                  'kejadian', 'referensi', 'keterangan',
                  'total_debit', 'total_kredit', 'seimbang',
                  'sudah_dibalik', 'baris']


# =========================================================
# PURCHASE ORDER
# =========================================================

class JurnalBalikSerializer(serializers.Serializer):
    tanggal = serializers.DateField()
    alasan  = serializers.CharField()

    def validate_alasan(self, v):
        if not v.strip():
            raise serializers.ValidationError('Alasan wajib diisi.')
        return v


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)
    sisa_qty = serializers.DecimalField(max_digits=14, decimal_places=3,
                                        read_only=True)
    sudah_lengkap = serializers.BooleanField(read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'produk', 'produk_kode', 'nama_item', 'satuan',
                  'qty_pesan', 'qty_diterima', 'sisa_qty', 'sudah_lengkap',
                  'harga_per_kg', 'amount']
        read_only_fields = ['nama_item', 'qty_diterima', 'amount']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    item = PurchaseOrderItemSerializer(many=True, read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    
    subtotal     = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    ppn_nominal  = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    grand_total  = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    
    boleh_diubah = serializers.BooleanField(read_only=True)
    dibuat_oleh_nama = serializers.CharField(source='dibuat_oleh.nama_lengkap', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'no_po', 'tanggal', 'entitas', 'entitas_kode',
                  'suplier', 'suplier_nama', 'status', 'boleh_diubah',
                  'tanggal_kirim_diminta', 'catatan', 'ppn_persen',
                  'subtotal', 'ppn_nominal', 'grand_total',
                  'dibuat_oleh', 'dibuat_oleh_nama', 'dibuat_pada', 'item']
        read_only_fields = ['no_po', 'status', 'dibuat_oleh', 'dibuat_pada']


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    # subtotal, ppn_nominal, dan grand_total adalah @property di model,
    # dihitung dari item -- bukan kolom database.
    #
    # ModelSerializer hanya memetakan field database secara otomatis.
    # Properti yang disebut di Meta.fields tanpa deklarasi ini DIBUANG
    # dari respons tanpa satu pun galat, dan di layar hasilnya Rp 0 --
    # terlihat seperti data kosong, bukan seperti field yang hilang.
    #
    # PurchaseOrderSerializer sudah melakukannya sejak awal; serializer
    # list dibuat belakangan dan langkah ini terlewat.
    subtotal = serializers.DecimalField(max_digits=18, decimal_places=2,
                                        read_only=True)
    ppn_nominal = serializers.DecimalField(max_digits=18, decimal_places=2,
                                           read_only=True)
    grand_total = serializers.DecimalField(max_digits=18, decimal_places=2,
                                           read_only=True)
    # subtotal, ppn_nominal, dan grand_total adalah @property di model,
    # dihitung dari item -- bukan kolom database.
    #
    # ModelSerializer hanya memetakan field database secara otomatis.
    # Properti yang disebut di Meta.fields tanpa deklarasi ini DIBUANG
    # dari respons tanpa satu pun galat, dan di layar hasilnya Rp 0 yang
    # terlihat seperti data kosong, bukan seperti field yang hilang.
    subtotal = serializers.DecimalField(max_digits=20, decimal_places=2,
                                        read_only=True)
    ppn_nominal = serializers.DecimalField(max_digits=20, decimal_places=2,
                                           read_only=True)
    grand_total = serializers.DecimalField(max_digits=20, decimal_places=2,
                                           read_only=True)
    """Tanpa nested item, untuk halaman daftar. Total lewat annotate."""

    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    
    subtotal     = serializers.DecimalField(source='subtotal_agg', max_digits=18, decimal_places=2, read_only=True)
    ppn_nominal  = serializers.DecimalField(source='ppn_nominal_agg', max_digits=18, decimal_places=2, read_only=True)
    grand_total  = serializers.DecimalField(source='grand_total_agg', max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'no_po', 'tanggal', 'entitas_kode', 'suplier_nama',
                  'status', 'subtotal', 'ppn_nominal', 'grand_total', 'tanggal_kirim_diminta']


class ItemMasukSerializer(serializers.Serializer):
    produk_id    = serializers.IntegerField()
    qty_pesan    = serializers.DecimalField(max_digits=14, decimal_places=3)
    harga_per_kg = serializers.DecimalField(max_digits=14, decimal_places=2)
    satuan       = serializers.CharField(max_length=8, required=False, default='kg')


class BuatPOSerializer(serializers.Serializer):
    entitas_id = serializers.IntegerField()
    suplier_id = serializers.IntegerField()
    tanggal    = serializers.DateField()
    tanggal_kirim_diminta = serializers.DateField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')
    ppn_persen = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    items   = ItemMasukSerializer(many=True)


class UbahItemPOSerializer(serializers.Serializer):
    items = ItemMasukSerializer(many=True)


class BatalPOSerializer(serializers.Serializer):
    alasan = serializers.CharField()


# =========================================================
# HUTANG
# =========================================================

class KartuHutangSerializer(serializers.ModelSerializer):
    class Meta:
        model = KartuHutang
        fields = ['id', 'tanggal', 'jenis', 'debit', 'kredit', 'referensi']


class FakturPembelianSerializer(serializers.ModelSerializer):
    mutasi = KartuHutangSerializer(many=True, read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    penerimaan_nomor = serializers.CharField(source='penerimaan.nomor',
                                             read_only=True, default=None)
    terlambat  = serializers.BooleanField(read_only=True)
    umur_hari  = serializers.IntegerField(read_only=True)

    class Meta:
        model = FakturPembelian
        fields = ['id', 'no_internal', 'nomor_faktur', 'jenis',
                  'entitas', 'entitas_kode', 'suplier', 'suplier_nama',
                  'penerimaan', 'penerimaan_nomor',
                  'tanggal_faktur', 'termin_hari', 'tanggal_jatuh_tempo',
                  'total_tagihan', 'total_dibayar', 'sisa_hutang',
                  'status', 'terlambat', 'umur_hari', 'dokumen', 'catatan',
                  'mutasi']
        read_only_fields = ['no_internal', 'tanggal_jatuh_tempo',
                            'total_tagihan', 'total_dibayar',
                            'sisa_hutang', 'status']


class FakturListSerializer(serializers.ModelSerializer):
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    terlambat = serializers.BooleanField(read_only=True)

    class Meta:
        model = FakturPembelian
        fields = ['id', 'nomor_faktur', 'entitas_kode', 'suplier_nama',
                  'tanggal_faktur', 'tanggal_jatuh_tempo', 'total_tagihan',
                  'sisa_hutang', 'status', 'terlambat']


class TerbitkanFakturSerializer(serializers.Serializer):
    """Payload untuk POST faktur/dari-penerimaan/{id}/"""

    nomor_faktur   = serializers.CharField(max_length=64)
    tanggal_faktur = serializers.DateField()
    total_tagihan  = serializers.DecimalField(max_digits=18, decimal_places=2)
    termin_hari    = serializers.IntegerField(required=False, allow_null=True)
    dokumen_id     = serializers.IntegerField(required=False, allow_null=True)
    catatan        = serializers.CharField(required=False, allow_blank=True, default='')
    abaikan_klaim_terbuka = serializers.BooleanField(required=False, default=False)


class BayarSerializer(serializers.Serializer):
    entitas_id = serializers.IntegerField()
    suplier_id = serializers.IntegerField()
    nominal    = serializers.DecimalField(max_digits=18, decimal_places=2)
    tanggal    = serializers.DateField()
    referensi  = serializers.CharField(required=False, allow_blank=True, default='')


class UangMukaSerializer(serializers.ModelSerializer):
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)

    class Meta:
        model = UangMukaSuplier
        fields = ['id', 'entitas', 'entitas_kode', 'suplier', 'suplier_nama',
                  'tanggal', 'nominal', 'sisa', 'referensi',
                  'dibuat_pada', 'diubah_pada']
        read_only_fields = ['sisa', 'dibuat_pada', 'diubah_pada']     




class FakturPenjualanSerializer(serializers.ModelSerializer):
    pelanggan_nama = serializers.CharField(source='pelanggan.nama', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)

    class Meta:
        model = FakturPenjualan
        fields = [
            'id', 'no_internal', 'nomor_faktur', 'entitas', 'entitas_kode',
            'pelanggan', 'pelanggan_nama', 'tanggal_faktur', 'termin_hari', 'tanggal_jatuh_tempo',
            'total_tagihan', 'total_dibayar', 'sisa_piutang', 'status', 'catatan'
        ]
        read_only_fields = ['no_internal', 'tanggal_jatuh_tempo', 'total_dibayar', 'sisa_piutang', 'status']

class TerbitkanFakturJualSerializer(serializers.Serializer):
    nomor_faktur = serializers.CharField(max_length=64)
    tanggal_faktur = serializers.DateField()
    termin_hari = serializers.IntegerField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')

class TerimaPiutangSerializer(serializers.Serializer):
    faktur_id = serializers.IntegerField()
    nominal = serializers.DecimalField(max_digits=18, decimal_places=2)
    tanggal = serializers.DateField()
    referensi = serializers.CharField(required=False, allow_blank=True, default='')

   

from .models.pengeluaran import PengeluaranKas

class PengeluaranKasSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)
    kategori_beban_nama = serializers.CharField(source='kategori_beban.nama', read_only=True)
    sumber_dana_nama = serializers.CharField(source='sumber_dana.nama', read_only=True)

    class Meta:
        model = PengeluaranKas
        fields = '__all__'
        read_only_fields = ['nomor_bukti', 'status', 'dibuat_oleh', 'dibuat_pada', 'diubah_pada']