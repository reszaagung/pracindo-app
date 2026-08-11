"""
API Papan Tugas — work_order/views.py

View tipis. Seluruh logika bisnis di services.py, seluruh bentuk di
serializers.py.

PENYARINGAN VISIBILITAS ADA DI get_queryset(), BUKAN DI PERMISSION.
Izin objek DRF tidak berlaku untuk endpoint list. Versi sebelumnya hanya
punya has_object_permission, sehingga GET daftar mengembalikan SELURUH Work
Order termasuk yang berkategori PRIVATE milik orang lain.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Prefetch
from rest_framework import status as http, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from staff_user.models import Profil
from staff_user.permissions import AksesModul, HanyaSupervisor

from . import serializers as s
from . import services
from .models import WorkOrder, WorkOrderPesan
from .permissions import BolehUbahWorkOrder


def _galat(e):
    pesan = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
    return Response({'detail': pesan}, status=http.HTTP_400_BAD_REQUEST)


class WorkOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [AksesModul, BolehUbahWorkOrder]
    modul = 'work_order'

    queryset = (
        WorkOrder.objects
        .select_related('dibuat_oleh', 'diselesaikan_oleh', 'detail_produksi')
        .prefetch_related('penugasan__staff')
        .annotate(total_pesan=Count('pesan_chat', distinct=True))
    )
    def get_queryset(self):
        qs = services.wo_terlihat(super().get_queryset(), self.request.user)

        if self.action in ('retrieve', 'setujui', 'kirim_pesan', 'pesan',
                           'buka_kembali', 'partial_update', 'update'):
            qs = qs.prefetch_related(
                Prefetch('pesan_chat',
                         queryset=WorkOrderPesan.objects.select_related('pengirim')))

        p = self.request.query_params
        if p.get('selesai') in ('true', 'false'):
            qs = qs.filter(selesai=p['selesai'] == 'true')
        if p.get('kategori'):
            qs = qs.filter(kategori=p['kategori'])
        if p.get('ditugaskan_ke_saya') == 'true':
            qs = qs.filter(penugasan__staff=self.request.user)
        if p.get('cari'):
            from django.db.models import Q
            kata = p['cari']
            qs = qs.filter(Q(nomor__icontains=kata) | Q(judul__icontains=kata))
        return qs.distinct()

    def get_serializer_class(self):
        if self.action in ('list', 'mading'):
            return s.WorkOrderRingkasSerializer
        return s.WorkOrderSerializer

    def _balas(self, wo_id, kode=http.HTTP_200_OK):
        wo = self.get_queryset().get(pk=wo_id)
        return Response(
            s.WorkOrderSerializer(wo, context=self.get_serializer_context()).data,
            status=kode)

    # ---------- CRUD ----------

    def create(self, request, *args, **kwargs):
        ser = s.BuatWorkOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            wo = services.buat_wo(user=request.user, **ser.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(wo.id, http.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        wo = self.get_object()
        ser = s.UbahWorkOrderSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            services.ubah_wo(wo_id=wo.id, user=request.user, **ser.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(wo.id)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Work Order tidak dihapus. Diskusi di dalamnya adalah jejak kesepakatan,
        dan menghapusnya menghapus alasan sebuah keputusan diambil.
        """
        return Response(
            {'detail': 'Work Order tidak dihapus. Selesaikan tugasnya, '
                       'atau minta Supervisor menutupnya.'},
            status=http.HTTP_400_BAD_REQUEST,
        )

    # ---------- papan ----------

    @action(detail=False, methods=['get'])
    def mading(self, request):
        """Papan tugas aktif. Array polos, tenggat terdekat di atas."""
        qs = services.mading(self.get_queryset(), request.user)
        return Response(
            s.WorkOrderRingkasSerializer(
                qs, many=True, context=self.get_serializer_context()).data)

    @action(detail=False, methods=['get'])
    def staff(self, request):
        """Daftar staf aktif untuk form penandaan. Array polos."""
        qs = Profil.objects.aktif().exclude(id=request.user.id)
        
        return Response(
            s.ProfilStaffRingkasSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Nama `approve` dipertahankan karena frontend sudah memanggilnya.
        `setujui` tersedia sebagai nama yang sejalan dengan repo.
        """
        return self.setujui(request, pk)

    @action(detail=True, methods=['post'])
    def setujui(self, request, pk=None):
        ser = s.SetujuiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        wo = self.get_object()
        try:
            _, pesan, tuntas = services.setujui(
                wo_id=wo.id, user=request.user,
                catatan=ser.validated_data['catatan'])
        except DjangoValidationError as e:
            return _galat(e)

        data = s.WorkOrderSerializer(
            self.get_queryset().get(pk=wo.id),
            context=self.get_serializer_context()).data
        # `detail` dipertahankan karena frontend menampilkannya apa adanya.
        return Response({'detail': pesan, 'tuntas': tuntas, 'work_order': data})

    @action(detail=True, methods=['post'], url_path='buka-kembali',
            permission_classes=[AksesModul, HanyaSupervisor])
    def buka_kembali(self, request, pk=None):
        ser = s.BukaKembaliSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        wo = self.get_object()
        try:
            services.buka_kembali(wo_id=wo.id, user=request.user,
                                  alasan=ser.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(wo.id)

    # ---------- diskusi ----------

    @action(detail=True, methods=['post'])
    def kirim_pesan(self, request, pk=None):
        """Nama aksi dipertahankan: frontend memanggil work-order/{id}/kirim_pesan/."""
        ser = s.KirimPesanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        wo = self.get_object()
        try:
            pesan = services.kirim_pesan(
                wo_id=wo.id, user=request.user, teks=ser.validated_data['teks'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(s.PesanChatSerializer(pesan).data,
                        status=http.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def pesan(self, request, pk=None):
        """Muat ulang diskusi tanpa menarik seluruh WO. Array polos."""
        wo = self.get_object()
        antrian = wo.pesan_chat.select_related('pengirim').all()
        return Response(s.PesanChatSerializer(antrian, many=True).data)
