from rest_framework import serializers
from .models import Batch, Tangki

class TangkiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tangki
        fields = ["id", "kode", "nama", "aktif"]

class BatchSerializer(serializers.ModelSerializer):
    tangki_kode = serializers.CharField(source="tangki.kode", read_only=True)
    tangki_tujuan_nama = serializers.CharField(source="tangki.nama", read_only=True)
    batch = serializers.CharField(source="nomor", read_only=True)
    sisa_qty = serializers.SerializerMethodField()
    harga_per_kg = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = "__all__"

    def get_sisa_qty(self, obj):
        from .services import saldo_batch
        return str(saldo_batch(obj).sisa_qty)

    def get_harga_per_kg(self, obj):
        from .services import saldo_batch
        return str(saldo_batch(obj).harga_per_kg)