from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from staff_user.permissions import AksesModul
from .models import Lampiran
from .serializers import (
    GantiLampiranSerializer, 
    LampiranSerializer, 
    UnggahLampiranSerializer
)

def _galat(e):
    pesan = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(pesan, status=status.HTTP_400_BAD_REQUEST)


class LampiranViewSet(viewsets.ModelViewSet):
    modul = 'dokumen'
    permission_classes = [AksesModul]
    parser_classes = [MultiPartParser, FormParser]
    
    serializer_class = LampiranSerializer
    filterset_fields = ['jenis', 'content_type', 'object_id']
    search_fields = ['nama_asli', 'keterangan']

    def get_queryset(self):
        return Lampiran.objects.select_related('dibuat_oleh', 'content_type').order_by('-dibuat_pada')

    def create(self, request):
        s = UnggahLampiranSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                lampiran = Lampiran.objects.create(
                    dibuat_oleh=request.user,
                    **s.validated_data
                )
        except DjangoValidationError as e:
            return _galat(e)
            
        return Response(
            LampiranSerializer(lampiran, context={'request': request}).data, 
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Lampiran tidak bisa diubah. Unggah pengganti lewat POST lampiran/{id}/ganti/.'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Lampiran append-only. Unggah pengganti lewat POST lampiran/{id}/ganti/ supaya jejaknya tetap ada.'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def ganti(self, request, pk=None):
        """
        Mengunggah pengganti. Yang lama TIDAK dihapus, hanya ditandai `digantikan_oleh`.
        """
        lama = self.get_object()
        
        if lama.digantikan_oleh_id:
            return Response(
                {'detail': f'Lampiran ini sudah digantikan oleh #{lama.digantikan_oleh_id}. Ganti yang itu.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        s = GantiLampiranSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                baru = Lampiran.objects.create(
                    jenis=s.validated_data.get('jenis', lama.jenis),
                    berkas=s.validated_data['berkas'],
                    keterangan=s.validated_data.get('keterangan', ''),
                    content_type=lama.content_type,
                    object_id=lama.object_id,
                    dibuat_oleh=request.user
                )
                # Tandai dokumen lama bahwa sudah digantikan
                lama.digantikan_oleh = baru
                lama.save(update_fields=['digantikan_oleh'])
        except DjangoValidationError as e:
            return _galat(e)
            
        return Response(
            LampiranSerializer(baru, context={'request': request}).data, 
            status=status.HTTP_201_CREATED
        )