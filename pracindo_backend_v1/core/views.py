"""
Endpoint core — core/views.py

Entitas dan grup bahan READ-ONLY di sini. Daftar entitas yang dipakai 
dropdown tetap diambil dari auth/portal/ yang sudah tersaring sesuai 
izin pengguna. Endpoint ini ditujukan untuk halaman pengaturan Supervisor.
"""
from datetime import date
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from staff_user.permissions import HanyaSupervisor, SudahLogin
from . import services
from .models import Entitas, GrupBahan, PeriodeAkuntansi
from .serializers import (
    BukaPeriodeSerializer, EntitasSerializer, GrupBahanSerializer,
    PeriodeAkuntansiSerializer, TutupPeriodeSerializer
)


def _galat(e):
    pesan = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(pesan, status=status.HTTP_400_BAD_REQUEST)


class EntitasViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'master'
    queryset = Entitas.objects.select_related('grup_bahan').order_by('kode')
    serializer_class = EntitasSerializer
    permission_classes = [HanyaSupervisor]
    filterset_fields = ['jenis', 'aktif']
    search_fields = ['kode', 'nama', 'npwp']


class GrupBahanViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'master'
    queryset = GrupBahan.objects.all().order_by('kode')
    serializer_class = GrupBahanSerializer
    permission_classes = [HanyaSupervisor]
    search_fields = ['kode', 'nama']


class PeriodeAkuntansiViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'akunting'
    queryset = PeriodeAkuntansi.objects.select_related('entitas', 'ditutup_oleh').order_by('-tahun', '-bulan')
    serializer_class = PeriodeAkuntansiSerializer
    filterset_fields = ['entitas', 'tahun', 'bulan', 'ditutup']

    def get_permissions(self):
        # Aksi tutup dan buka periode hanya untuk Supervisor. 
        # Cek status periode boleh oleh siapa saja yang login (seperti Akunting).
        if self.action in ('tutup', 'buka'):
            return [HanyaSupervisor()]
        return [SudahLogin()]

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Apakah tanggal tertentu masih boleh diposting?
        Contoh: ?entitas=1&tanggal=2026-08-02
        Dipakai oleh frontend sebelum submit form PO/Jurnal.
        """
        entitas_id = request.query_params.get('entitas')
        tgl_str = request.query_params.get('tanggal')
        
        if not entitas_id or not entitas_id.isdigit():
            return Response({'detail': 'Parameter entitas wajib berupa angka.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tgl = date.fromisoformat(tgl_str)
        except (ValueError, TypeError):
            return Response({'detail': 'Format tanggal harus YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            services.pastikan_periode_terbuka(entitas_id=int(entitas_id), tanggal=tgl)
            return Response({
                'terbuka': True, 
                'periode': f"{tgl.month:02d}/{tgl.year}",
                'pesan': None
            })
        except services.PeriodeTertutup as e:
            return Response({
                'terbuka': False,
                'periode': f"{tgl.month:02d}/{tgl.year}",
                'pesan': str(e)
            })

    @action(detail=False, methods=['post'])
    def tutup(self, request):
        s = TutupPeriodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            periode = services.tutup_periode(
                entitas_id=d['entitas_id'],
                tahun=d['tahun'],
                bulan=d['bulan'],
                user=request.user
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PeriodeAkuntansiSerializer(periode).data)

    @action(detail=False, methods=['post'])
    def buka(self, request):
        s = BukaPeriodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            periode = services.buka_periode(
                entitas_id=d['entitas_id'],
                tahun=d['tahun'],
                bulan=d['bulan'],
                user=request.user,
                alasan=d['alasan']
            )
        except DjangoValidationError as e:
            return _galat(e)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PeriodeAkuntansiSerializer(periode).data)