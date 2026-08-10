"""
Serializer core — core/serializers.py
"""
from rest_framework import serializers

from .models import Entitas, GrupBahan, PeriodeAkuntansi


class GrupBahanSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupBahan
        fields = ['id', 'kode', 'nama']


class EntitasSerializer(serializers.ModelSerializer):
    grup_bahan_kode = serializers.CharField(source='grup_bahan.kode', read_only=True)
    jenis_label = serializers.CharField(source='get_jenis_display', read_only=True)

    class Meta:
        model = Entitas
        fields = [
            'id', 'kode', 'nama', 'jenis', 'jenis_label', 
            'npwp', 'grup_bahan', 'grup_bahan_kode', 'aktif'
        ]
        read_only_fields = ['kode']


class PeriodeAkuntansiSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source='entitas.kode', read_only=True, default=None)
    ditutup_oleh_nama = serializers.CharField(source='ditutup_oleh.nama_lengkap', read_only=True, default=None)

    class Meta:
        model = PeriodeAkuntansi
        fields = [
            'id', 'entitas', 'entitas_kode', 'tahun', 'bulan',
            'ditutup', 'ditutup_pada', 'ditutup_oleh', 'ditutup_oleh_nama', 'alasan_buka'
        ]


class TutupPeriodeSerializer(serializers.Serializer):
    entitas_id = serializers.IntegerField()
    tahun = serializers.IntegerField(min_value=2000, max_value=2100)
    bulan = serializers.IntegerField(min_value=1, max_value=12)


class BukaPeriodeSerializer(serializers.Serializer):
    entitas_id = serializers.IntegerField()
    tahun = serializers.IntegerField(min_value=2000, max_value=2100)
    bulan = serializers.IntegerField(min_value=1, max_value=12)
    alasan = serializers.CharField()

    def validate_alasan(self, v):
        if not v.strip():
            raise serializers.ValidationError('Alasan wajib diisi.')
        return v.strip()