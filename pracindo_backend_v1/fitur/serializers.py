from rest_framework import serializers
from .models import HelperGenerateStikerDoc

class HelperGenerateStikerDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelperGenerateStikerDoc
        fields = '__all__'

from rest_framework import serializers

class CetakStikerPayloadSerializer(serializers.Serializer):
    nama_item = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=100)
    lot = serializers.CharField(max_length=100)
    total_unit = serializers.IntegerField(default=1)
    qty = serializers.CharField(max_length=100)
    satuan = serializers.CharField(max_length=20, default="KGS", required=False)