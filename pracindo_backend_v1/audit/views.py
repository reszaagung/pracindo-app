"""
Endpoint jejak aktivitas — audit/views.py

READ-ONLY sepenuhnya. Jejak hanya lahir dari services.catat() yang
dipanggil app lain; tidak ada jalur API untuk membuat, mengubah, atau
menghapusnya.

Supervisor saja. Riwayat siapa membatalkan apa adalah informasi yang
bisa disalahgunakan -- baik untuk mengintai rekan kerja maupun untuk
mengetahui kapan pengawasan sedang longgar.
"""
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from staff_user.permissions import HanyaSupervisor

from .models import JejakAktivitas
from .serializers import JejakAktivitasSerializer


class JejakAktivitasViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'staff_user'
    permission_classes = [HanyaSupervisor]
    serializer_class = JejakAktivitasSerializer
    queryset = (JejakAktivitas.objects
                .select_related('oleh', 'entitas', 'content_type')
                .order_by('-waktu', '-id'))
    filterset_fields = ['aksi', 'entitas', 'oleh', 'content_type']
    search_fields = ['label_objek', 'alasan']

    @action(detail=False, methods=['get'])
    def objek(self, request):
        """
        Riwayat satu objek: ?model=purchaseorder&id=12

        Dipakai layar detail dokumen untuk menampilkan lini masa
        perubahan statusnya.
        """
        model = request.query_params.get('model')
        obj_id = request.query_params.get('id')
        if not model or not obj_id:
            return Response({'detail': 'Parameter model dan id wajib.'},
                            status=400)

        ct = ContentType.objects.filter(model=model.lower()).first()
        if not ct:
            return Response({'detail': f'Model {model} tidak dikenali.'},
                            status=400)

        qs = self.get_queryset().filter(content_type=ct, object_id=obj_id)
        return Response(JejakAktivitasSerializer(qs, many=True).data)
