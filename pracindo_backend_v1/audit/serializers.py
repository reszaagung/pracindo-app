"""Serializer jejak aktivitas — audit/serializers.py"""
from rest_framework import serializers

from .models import JejakAktivitas


class JejakAktivitasSerializer(serializers.ModelSerializer):
    oleh_nama = serializers.CharField(source='oleh.nama_lengkap',
                                      read_only=True, default='sistem')
    aksi_label = serializers.CharField(source='get_aksi_display', read_only=True)
    entitas_kode = serializers.CharField(source='entitas.kode',
                                         read_only=True, default=None)
    model = serializers.CharField(source='content_type.model', read_only=True)
    perpindahan = serializers.CharField(read_only=True)

    class Meta:
        model = JejakAktivitas
        fields = ['id', 'waktu', 'oleh', 'oleh_nama', 'aksi', 'aksi_label',
                  'model', 'object_id', 'label_objek',
                  'entitas', 'entitas_kode',
                  'status_lama', 'status_baru', 'perpindahan',
                  'alasan', 'rincian', 'ip']
