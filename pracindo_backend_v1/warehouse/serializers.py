"""
Serializer gudang — warehouse/serializers.py

ATURAN MUTLAK
    TIDAK ADA SATU PUN field harga atau nilai rupiah di file ini.

    Bukan bernilai null, bukan difilter, tapi memang tidak pernah ada di
    kelasnya. Filter berbasis pop() gampang bocor lewat ?expand=, nested
    serializer, atau endpoint baru yang lupa dipasang.

    Alasannya bukan kerapian: staff gudang yang tahu nilai rupiah punya
    insentif untuk "menyesuaikan" hasil timbangan.

    LaporanSelisih.nilai_selisih dan nilai_klaim SENGAJA dikecualikan dari
    serializer gudang. Akunting melihatnya lewat endpoint mereka sendiri.
"""
from rest_framework import serializers

from akunting.models import PurchaseOrder, PurchaseOrderItem

from .models import (
    JenisKemasan, LaporanSelisih,PenerimaanBarang, PenerimaanItem,
)


class POItemGudangSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source='produk.kode', read_only=True)
    sisa_qty = serializers.DecimalField(max_digits=14, decimal_places=3,
                                        read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'produk', 'produk_kode', 'nama_item', 'satuan',
                  'qty_pesan', 'qty_diterima', 'sisa_qty']


class POGudangSerializer(serializers.ModelSerializer):
    item = POItemGudangSerializer(many=True, read_only=True)
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'no_po', 'tanggal', 'entitas_kode', 'suplier',
                  'suplier_nama', 'status', 'tanggal_kirim_diminta',
                  'catatan', 'item']


class PenerimaanItemSerializer(serializers.ModelSerializer):
    nama_item = serializers.CharField(source='po_item.nama_item', read_only=True)
    satuan    = serializers.CharField(source='po_item.satuan', read_only=True)
    selisih_berat = serializers.DecimalField(max_digits=14, decimal_places=3,
                                             read_only=True)
    persen_selisih_berat = serializers.DecimalField(max_digits=8, decimal_places=2,
                                                    read_only=True)

    class Meta:
        model = PenerimaanItem
        fields = ['id', 'po_item', 'nama_item', 'satuan',
                  'jenis_kemasan', 'jumlah_koli', 'isi_per_koli',
                  'qty_deklarasi', 'qty_diterima', 'qty_ditolak',
                  'alasan_tolak', 'selisih_berat', 'persen_selisih_berat']
        read_only_fields = ['qty_deklarasi']


class LaporanSelisihGudangSerializer(serializers.ModelSerializer):
    penerimaan_nomor = serializers.CharField(source='penerimaan.nomor',
                                             read_only=True)
    jenis_label  = serializers.CharField(source='get_jenis_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    umur_hari = serializers.IntegerField(read_only=True)

    class Meta:
        model = LaporanSelisih
        fields = ['id', 'nomor', 'penerimaan', 'penerimaan_nomor',
                  'penerimaan_item', 'tanggal', 'jenis', 'jenis_label',
                  'status', 'status_label', 'qty_selisih', 'uraian',
                  'foto', 'umur_hari']
        read_only_fields = ['nomor', 'status']


class PenerimaanBarangSerializer(serializers.ModelSerializer):
    item = PenerimaanItemSerializer(many=True, read_only=True)
    laporan_selisih = LaporanSelisihGudangSerializer(many=True, read_only=True)
    po_nomor = serializers.CharField(source='purchase_order.no_po', read_only=True)
    suplier_nama = serializers.CharField(source='purchase_order.suplier.nama',
                                         read_only=True)
    total_koli = serializers.IntegerField(read_only=True)
    dibuat_oleh_nama = serializers.CharField(source='dibuat_oleh.nama_lengkap',
                                             read_only=True)

    class Meta:
        model = PenerimaanBarang
        fields = ['id', 'nomor', 'tanggal', 'purchase_order', 'po_nomor',
                  'suplier_nama', 'no_surat_jalan', 'dokumen',
                  'ada_selisih', 'total_koli', 'catatan',
                  'dibuat_oleh_nama', 'dibuat_pada',
                  'item', 'laporan_selisih']
        read_only_fields = ['nomor', 'ada_selisih', 'dibuat_oleh', 'dibuat_pada']


class PenerimaanListSerializer(serializers.ModelSerializer):
    po_nomor = serializers.CharField(source='purchase_order.no_po', read_only=True)
    suplier_nama = serializers.CharField(source='purchase_order.suplier.nama',
                                         read_only=True)

    class Meta:
        model = PenerimaanBarang
        fields = ['id', 'nomor', 'tanggal', 'po_nomor', 'suplier_nama',
                  'no_surat_jalan', 'ada_selisih']


class BarisTerimaSerializer(serializers.Serializer):
    po_item_id    = serializers.IntegerField()
    jenis_kemasan = serializers.ChoiceField(choices=JenisKemasan.choices,
                                            default=JenisKemasan.CURAH)
    jumlah_koli   = serializers.IntegerField(required=False, allow_null=True)
    isi_per_koli  = serializers.DecimalField(max_digits=14, decimal_places=3,
                                             required=False, allow_null=True)
    qty_diterima  = serializers.DecimalField(max_digits=14, decimal_places=3)
    qty_ditolak   = serializers.DecimalField(max_digits=14, decimal_places=3,
                                             required=False, default=0)
    alasan_tolak  = serializers.CharField(required=False, allow_blank=True,
                                          default='')

    def validate(self, data):
        if data.get('jenis_kemasan') != JenisKemasan.CURAH:
            if not data.get('jumlah_koli') or not data.get('isi_per_koli'):
                raise serializers.ValidationError(
                    'Kemasan selain curah wajib mengisi jumlah koli dan '
                    'isi per koli.'
                )
        if data.get('qty_ditolak') and not data.get('alasan_tolak'):
            raise serializers.ValidationError(
                'Alasan tolak wajib diisi kalau ada qty ditolak.'
            )
        return data


class TerimaBarangSerializer(serializers.Serializer):
    po_id          = serializers.IntegerField()
    no_surat_jalan = serializers.CharField(max_length=64)
    tanggal        = serializers.DateField()
    dokumen_id     = serializers.IntegerField(required=False, allow_null=True)
    catatan        = serializers.CharField(required=False, allow_blank=True,
                                           default='')
    baris          = BarisTerimaSerializer(many=True)


class LaporanSelisihAkuntingSerializer(LaporanSelisihGudangSerializer):
    suplier_nama = serializers.CharField(source='suplier.nama', read_only=True)
    resolusi_label = serializers.CharField(source='get_resolusi_display',
                                           read_only=True, default=None)

    class Meta(LaporanSelisihGudangSerializer.Meta):
        fields = LaporanSelisihGudangSerializer.Meta.fields + [
            'suplier_nama', 'nilai_selisih', 'resolusi', 'resolusi_label',
            'nilai_klaim', 'catatan_resolusi', 'diselesaikan_pada',
        ]
        read_only_fields = ['nomor', 'status', 'nilai_selisih',
                            'diselesaikan_pada']


class LaporanManualSerializer(serializers.Serializer):
    penerimaan_id      = serializers.IntegerField()
    penerimaan_item_id = serializers.IntegerField(required=False, allow_null=True)
    jenis       = serializers.CharField(max_length=14)
    qty_selisih = serializers.DecimalField(max_digits=14, decimal_places=3)
    uraian      = serializers.CharField()
    foto_id     = serializers.IntegerField(required=False, allow_null=True)


class SelesaikanSelisihSerializer(serializers.Serializer):
    resolusi    = serializers.CharField(max_length=8)
    nilai_klaim = serializers.DecimalField(max_digits=18, decimal_places=2,
                                           required=False, allow_null=True)
    catatan     = serializers.CharField(required=False, allow_blank=True,
                                        default='')


class TutupSelisihSerializer(serializers.Serializer):
    alasan = serializers.CharField()

