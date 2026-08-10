from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from django.core.exceptions import ValidationError as DjangoValidationError

from staff_user.permissions import AksesModul
from .models import SesiProduksi, SesiInput
from . import serializers, services

def _galat(e):
    pesan = e.message if hasattr(e, 'message') else str(e)
    return Response({'detail': pesan}, status=status.HTTP_400_BAD_REQUEST)

class SesiViewSet(viewsets.ModelViewSet):
    permission_classes = [AksesModul]
    modul = 'produksi'
    
    queryset = SesiProduksi.objects.select_related(
        'resep__produk_jadi', 'grup_bahan', 'dibuat_oleh'
    ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.SesiListSerializer
        return serializers.SesiListSerializer

    def retrieve(self, request, *args, **kwargs):
        sesi = self.get_object()
        data = services.ringkasan_sesi(sesi.id)
        return Response(data)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "PUT/PATCH", 
            detail="Sesi tidak diubah lewat PUT. Gunakan aksi mulai, selesaikan, gagalkan, atau batalkan."
        )

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE", 
            detail="Sesi tidak dihapus. Gunakan aksi batalkan (DRAFT) atau gagalkan (BERJALAN)."
        )

    def create(self, request, *args, **kwargs):
        ser = serializers.BuatSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            sesi = services.buat_sesi(
                user=request.user,
                **ser.validated_data
            )
            return Response({'id': sesi.id, 'nomor': sesi.nomor}, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=True, methods=['post'])
    def mulai(self, request, pk=None):
        ser = serializers.MulaiSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()
        
        qty_aktual_dict = {}
        for baris in ser.validated_data['baris']:
            bahan_id = baris['bahan_id']
            qty_aktual_dict[bahan_id] = baris['qty_aktual']
            
            tangki_id = baris.get('tangki_id')
            if tangki_id:
                SesiInput.objects.filter(sesi=sesi, bahan_id=bahan_id).update(tangki_id=tangki_id)
                
        try:
            services.mulai_sesi(sesi_id=sesi.id, qty_aktual=qty_aktual_dict)
            return Response(services.ringkasan_sesi(sesi.id))
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=True, methods=['post'])
    def selesaikan(self, request, pk=None):
        ser = serializers.SelesaikanSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()
        try:
            services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=ser.validated_data['qty_hasil'])
            return Response(services.ringkasan_sesi(sesi.id))
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=True, methods=['post'])
    def batalkan(self, request, pk=None):
        ser = serializers.BatalSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()
        try:
            services.batalkan_sesi(sesi_id=sesi.id, alasan=ser.validated_data['alasan'])
            return Response(services.ringkasan_sesi(sesi.id))
        except DjangoValidationError as e:
            return _galat(e)