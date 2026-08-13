import os
from rest_framework import serializers
from django.conf import settings
from .models import Lampiran, JenisLampiran

# Batas ukuran file mengikuti pengaturan global atau default 2.5MB
MAKS_BYTE = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440) 

# Daftar putih ekstensi dan MIME type yang diizinkan
MIME_SAH = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
}

class LampiranSerializer(serializers.ModelSerializer):
    jenis_label = serializers.CharField(source='get_jenis_display', read_only=True)
    berkas_url = serializers.SerializerMethodField()
    pemilik_tipe = serializers.SerializerMethodField()
    dibuat_oleh_nama = serializers.CharField(source='dibuat_oleh.nama_lengkap', read_only=True, default=None)

    class Meta:
        model = Lampiran
        fields = [
            'id', 'jenis', 'jenis_label', 'berkas_url', 'nama_asli', 'ukuran_byte', 
            'keterangan', 'content_type', 'object_id', 'pemilik_tipe', 
            'digantikan_oleh', 'masih_berlaku', 'dibuat_oleh_nama', 'dibuat_pada'
        ]
        read_only_fields = fields

    def get_berkas_url(self, obj):
        request = self.context.get('request')
        if obj.berkas and hasattr(obj.berkas, 'url'):
            return request.build_absolute_uri(obj.berkas.url) if request else obj.berkas.url
        return None

    def get_pemilik_tipe(self, obj):
        if obj.content_type:
            return f"{obj.content_type.app_label}.{obj.content_type.model}"
        return None


class UnggahLampiranSerializer(serializers.Serializer):
    berkas = serializers.FileField(required=True)
    jenis = serializers.ChoiceField(choices=JenisLampiran.choices, required=True)
    keterangan = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    content_type = serializers.IntegerField(required=False, allow_null=True)
    object_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_berkas(self, berkas):
        if berkas.size > MAKS_BYTE:
            raise serializers.ValidationError(f'Ukuran maksimum {MAKS_BYTE / 1024 / 1024:.1f} MB, berkas ini {berkas.size / 1024 / 1024:.1f} MB.')
        
        ext = os.path.splitext(berkas.name)[1].lower()
        
        # Perlindungan ekstra dari injeksi script via SVG
        if ext == '.svg':
            raise serializers.ValidationError('SVG SENGAJA TIDAK DIIZINKAN meski ia adalah gambar.')
            
        if ext not in MIME_SAH:
            raise serializers.ValidationError(f'Ekstensi {ext or "(tanpa ekstensi)"} tidak diizinkan. Yang boleh: {", ".join(sorted(MIME_SAH.keys()))}')
        
        return berkas

    def validate(self, data):
        # Memastikan tidak ada berkas yatim (punya content_type tapi tidak punya object_id, atau sebaliknya)
        if bool(data.get('content_type')) != bool(data.get('object_id')):
            raise serializers.ValidationError('content_type dan object_id harus diisi bersamaan.')
        return data


class GantiLampiranSerializer(serializers.Serializer):
    berkas = serializers.FileField(required=True)
    keterangan = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    jenis = serializers.ChoiceField(choices=JenisLampiran.choices, required=False)

    def validate_berkas(self, berkas):
        if berkas.size > MAKS_BYTE:
            raise serializers.ValidationError(f'Ukuran maksimum {MAKS_BYTE / 1024 / 1024:.1f} MB, berkas ini {berkas.size / 1024 / 1024:.1f} MB.')
        
        ext = os.path.splitext(berkas.name)[1].lower()
        
        if ext == '.svg':
            raise serializers.ValidationError('SVG SENGAJA TIDAK DIIZINKAN meski ia adalah gambar.')
            
        if ext not in MIME_SAH:
            raise serializers.ValidationError(f'Ekstensi {ext or "(tanpa ekstensi)"} tidak diizinkan. Yang boleh: {", ".join(sorted(MIME_SAH.keys()))}')
        return berkas