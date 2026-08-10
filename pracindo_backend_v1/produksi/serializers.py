from rest_framework import serializers
from .models import SesiProduksi, SesiInput

class SesiListSerializer(serializers.ModelSerializer):
    """
    Serializer read-only untuk OperationsLedger.vue
    """
    produk_jadi_kode = serializers.CharField(source='resep.produk_jadi.kode', read_only=True)
    produk_jadi_nama = serializers.CharField(source='resep.produk_jadi.nama', read_only=True)
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    satuan_kode = serializers.CharField(source='resep.produk_jadi.satuan_kode', read_only=True)
    jenis_sesi = serializers.SerializerMethodField()
    hasil_masuk_pool = serializers.SerializerMethodField()
    entitas_penanggung_kode = serializers.SerializerMethodField()
    dibuat_oleh_nama = serializers.CharField(source='dibuat_oleh.get_full_name', read_only=True, default='Sistem')

    class Meta:
        model = SesiProduksi
        fields = [
            'id', 'nomor', 'tanggal', 'status', 'grup_bahan_kode', 
            'produk_jadi_kode', 'produk_jadi_nama', 'qty_target', 'qty_hasil', 
            'rendemen', 'satuan_kode', 'jenis_sesi', 'hasil_masuk_pool', 
            'entitas_penanggung_kode', 'dibuat_oleh_nama'
        ]

    def get_jenis_sesi(self, obj):
        return getattr(obj, 'jenis_sesi', 'PRODUKSI')
        
    def get_hasil_masuk_pool(self, obj):
        return getattr(obj, 'hasil_masuk_pool', True)
        
    def get_entitas_penanggung_kode(self, obj):
        entitas = getattr(obj, 'entitas_penanggung', None)
        return entitas.kode if entitas else None


class BuatSesiSerializer(serializers.Serializer):
    grup_bahan_id = serializers.IntegerField()
    produk_jadi_id = serializers.IntegerField()
    qty_target = serializers.DecimalField(max_digits=14, decimal_places=3)
    tanggal = serializers.DateField()
    tangki_hasil_id = serializers.IntegerField(required=False, allow_null=True)
    catatan = serializers.CharField(required=False, allow_blank=True, default='')

class MulaiSesiBarisSerializer(serializers.Serializer):
    bahan_id = serializers.IntegerField()
    qty_aktual = serializers.DecimalField(max_digits=14, decimal_places=3)
    tangki_id = serializers.IntegerField(required=False, allow_null=True)

class MulaiSesiSerializer(serializers.Serializer):
    baris = MulaiSesiBarisSerializer(many=True)

class SelesaikanSesiSerializer(serializers.Serializer):
    qty_hasil = serializers.DecimalField(max_digits=14, decimal_places=3)

class BatalSesiSerializer(serializers.Serializer):
    alasan = serializers.CharField(required=True, allow_blank=False)