"""
API logistik — logistik/views.py

Views tipis: menerjemahkan HTTP ke pemanggilan service dan sebaliknya.
Seluruh logika bisnis di services.py.

PENYARINGAN KURIR ADA DI get_queryset(), BUKAN DI has_object_permission.
Izin objek di DRF tidak berlaku untuk endpoint list -- kalau hanya
mengandalkannya, GET daftar pengiriman akan mengembalikan perjalanan seluruh
kurir beserta alamat semua pelanggan.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status as http, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from staff_user.permissions import AksesModul, HanyaSupervisor

from . import serializers as s
from . import services
from .integrasi_warehouse import SambunganBelumSiap
from .models import Kendaraan, Pengiriman, Retur, StatusPengiriman
from .permissions import (
    HanyaKurirPengiriman, KurirTidakMengubahRute, batasi_ke_kurir,
)


def _galat(e):
    pesan = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
    return Response({'detail': pesan}, status=http.HTTP_400_BAD_REQUEST)


def _belum_siap(e):
    # 503, bukan 400: ini bukan kesalahan pengguna, ini modul hulu yang
    # belum terpasang. Membalasnya 400 membuat orang mengira datanya salah.
    return Response({'detail': str(e)}, status=http.HTTP_503_SERVICE_UNAVAILABLE)


class PengirimanViewSet(viewsets.ModelViewSet):
    permission_classes = [AksesModul, KurirTidakMengubahRute, HanyaKurirPengiriman]
    modul = 'logistik'
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    queryset = (
        Pengiriman.objects
        .select_related('kurir', 'kendaraan', 'entitas')
        .all()
    )

    def get_queryset(self):
        qs = super().get_queryset()
        qs = batasi_ke_kurir(qs, self.request.user, 'kurir_id')
        if self.action in ('retrieve', 'tugas_saya'):
            qs = qs.prefetch_related('perhentian__bukti', 'perhentian__retur')
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return s.PengirimanSerializer
        return s.PengirimanDetailSerializer

    def _balas(self, pk, kode=http.HTTP_200_OK):
        obj = self.get_queryset().prefetch_related(
            'perhentian__bukti', 'perhentian__retur').get(pk=pk)
        return Response(s.PengirimanDetailSerializer(obj).data, status=kode)

    # ---------- metode yang ditutup ----------

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            'PUT/PATCH',
            detail='Pengiriman tidak diubah lewat PUT atau PATCH. Gunakan '
                   'aksi urutkan, berangkatkan, atau batalkan.',
        )

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            'DELETE',
            detail='Pengiriman tidak dihapus. Gunakan aksi batalkan.',
        )

    # ---------- perakitan ----------

    def create(self, request, *args, **kwargs):
        ser = s.RakitPengirimanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            kirim = services.rakit_pengiriman(user=request.user, **ser.validated_data)
        except SambunganBelumSiap as e:
            return _belum_siap(e)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id, http.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def urutkan(self, request, pk=None):
        """Urutan dari orang menimpa usulan sistem. Itu memang niatnya."""
        ser = s.UrutRuteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        kirim = self.get_object()

        diminta = ser.validated_data['urutan']
        milik = list(kirim.perhentian.values_list('id', flat=True))
        if sorted(diminta) != sorted(milik):
            return Response(
                {'detail': 'Daftar urutan harus memuat tepat semua perhentian '
                           'pengiriman ini, tanpa kurang dan tanpa lebih.'},
                status=http.HTTP_400_BAD_REQUEST,
            )

        for posisi, hid in enumerate(diminta, start=1):
            kirim.perhentian.filter(pk=hid).update(urutan=posisi)

        try:
            services.hitung_rute(kirim.id)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    @action(detail=True, methods=['post'], url_path='hitung-rute')
    def hitung_rute(self, request, pk=None):
        ser = s.PakaiUsulanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        kirim = self.get_object()
        try:
            services.hitung_rute(
                kirim.id, pakai_usulan=ser.validated_data['pakai_usulan'])
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    # ---------- alur perjalanan ----------

    @action(detail=True, methods=['post'])
    def berangkatkan(self, request, pk=None):
        kirim = self.get_object()
        try:
            services.berangkatkan(pengiriman_id=kirim.id, oleh=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    @action(detail=True, methods=['post'])
    def batalkan(self, request, pk=None):
        ser = s.BatalPengirimanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        kirim = self.get_object()
        try:
            services.batalkan_pengiriman(
                pengiriman_id=kirim.id, alasan=ser.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    @action(detail=False, methods=['get'], url_path='tugas-saya')
    def tugas_saya(self, request):
        """Layar utama kurir: perjalanan yang belum tuntas, array polos."""
        qs = self.get_queryset().filter(
            kurir=request.user,
            status__in=[StatusPengiriman.DISIAPKAN, StatusPengiriman.BERANGKAT],
        ).order_by('tanggal', 'id')
        return Response(s.PengirimanDetailSerializer(qs, many=True).data)

    # ---------- pelacakan ----------

    @action(detail=True, methods=['post'])
    def posisi(self, request, pk=None):
        kirim = self.get_object()
        ser = s.PosisiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            services.catat_posisi(
                pengiriman_id=kirim.id, oleh=request.user, **ser.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(status=http.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def jejak(self, request, pk=None):
        kirim = self.get_object()
        return Response(
            s.JejakPosisiSerializer(kirim.jejak.all(), many=True).data)

    # ---------- aksi per perhentian ----------

    @action(detail=True, methods=['post'],
            url_path=r'perhentian/(?P<hid>\d+)/sampai')
    def sampai(self, request, pk=None, hid=None):
        kirim = self.get_object()
        try:
            services.tandai_sampai(perhentian_id=int(hid), oleh=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    @action(detail=True, methods=['post'],
            url_path=r'perhentian/(?P<hid>\d+)/bukti')
    def bukti(self, request, pk=None, hid=None):
        """
        Unggah foto bukti terima. Bisa datang dari antrean offline berjam-jam
        setelah kejadian, jadi header Idempotency-Key dipakai supaya
        pengiriman ulang tidak menghasilkan dua foto untuk satu peristiwa.
        """
        kirim = self.get_object()
        ser = s.BuktiTerimaUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            services.unggah_bukti(
                perhentian_id=int(hid), oleh=request.user,
                idem_key=request.headers.get('Idempotency-Key', ''),
                **ser.validated_data,
            )
        except SambunganBelumSiap as e:
            return _belum_siap(e)
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)

    @action(detail=True, methods=['post'],
            url_path=r'perhentian/(?P<hid>\d+)/retur')
    def retur(self, request, pk=None, hid=None):
        kirim = self.get_object()
        ser = s.CatatReturSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            services.catat_retur(
                perhentian_id=int(hid), oleh=request.user,
                idem_key=request.headers.get('Idempotency-Key', ''),
                **ser.validated_data,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return self._balas(kirim.id)


class ReturViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AksesModul]
    modul = 'logistik'
    serializer_class = s.ReturSerializer

    queryset = (
        Retur.objects
        .select_related('perhentian', 'perhentian__pengiriman',
                        'dicatat_oleh', 'disetujui_oleh')
        .all()
    )

    def get_queryset(self):
        return batasi_ke_kurir(
            super().get_queryset(), self.request.user,
            'perhentian__pengiriman__kurir_id')

    @action(detail=True, methods=['post'],
            permission_classes=[HanyaSupervisor])
    def setujui(self, request, pk=None):
        """
        Persetujuan Supervisor memicu warehouse mengembalikan stok.
        Logistik tidak pernah menulis stok sendiri.
        """
        retur = self.get_object()
        try:
            services.setujui_retur(retur_id=retur.id, oleh=request.user)
        except SambunganBelumSiap as e:
            return _belum_siap(e)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(s.ReturSerializer(self.get_object()).data)


class KendaraanViewSet(viewsets.ModelViewSet):
    permission_classes = [AksesModul]
    modul = 'logistik'
    queryset = Kendaraan.objects.all()
    serializer_class = s.KendaraanSerializer


class DistribusiTersediaView(APIView):
    """
    Distribusi yang siap dirakit jadi pengiriman. Sumbernya warehouse.
    Array polos.
    """
    permission_classes = [AksesModul]
    modul = 'logistik'

    def get(self, request):
        entitas_id = request.query_params.get('entitas')
        try:
            data = services.distribusi_tersedia(
                entitas_id=int(entitas_id) if entitas_id else None)
        except SambunganBelumSiap as e:
            return _belum_siap(e)
        return Response(data)
