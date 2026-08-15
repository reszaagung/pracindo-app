"""
Endpoint gudang — warehouse/views.py

Serializer di modul ini TIDAK PERNAH memuat harga. Payload dari gudang
juga tidak pernah membawa angka rupiah -- nilai dihitung di server dari
harga yang tersimpan di PO, sehingga tidak ada yang bisa dimanipulasi
dari klien.

LaporanSelisihViewSet punya DUA tampilan dari objek yang sama:
    modul warehouse  -> tanpa nilai rupiah, gudang melaporkan fakta fisik
    modul akunting   -> dengan nilai dan resolusi, akunting yang menilai
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from akunting.models import PurchaseOrder, PurchaseOrderItem

from . import services
from .models import LaporanSelisih, Packaging, PenerimaanBarang
from .serializers import (
    LaporanManualSerializer, LaporanSelisihAkuntingSerializer,
    LaporanSelisihGudangSerializer, PackagingSerializer,
    PenerimaanBarangSerializer, PenerimaanListSerializer, POGudangSerializer,
    SelesaikanSelisihSerializer, TerimaBarangSerializer,
    TutupSelisihSerializer,
)
from staff_user.permissions import AksesModul


def _galat(e):
    isi = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# PO SIAP TERIMA
# =========================================================

class POSiapTerimaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Daftar PO yang menunggu barang, untuk layar Received.

    Serializer-nya POGudangSerializer -- tanpa harga_per_kg, tanpa amount,
    tanpa total_nilai.
    """

    modul = 'warehouse'
    permission_classes = [AksesModul]
    serializer_class = POGudangSerializer
    filterset_fields = ['suplier', 'entitas']
    search_fields = ['no_po', 'suplier__nama']

    def get_queryset(self):
        return (PurchaseOrder.objects.terbuka()
                .select_related('suplier', 'entitas')
                .prefetch_related(
                    Prefetch('item',
                             queryset=PurchaseOrderItem.objects.select_related('produk')))
                .order_by('tanggal'))


# =========================================================
# PENERIMAAN
# =========================================================

class PenerimaanViewSet(viewsets.ModelViewSet):
    modul = 'warehouse'
    permission_classes = [AksesModul]
    serializer_class = PenerimaanBarangSerializer
    filterset_fields = ['purchase_order', 'ada_selisih', 'tanggal']
    search_fields = ['nomor', 'no_surat_jalan', 'purchase_order__no_po']

    def get_queryset(self):
        return (PenerimaanBarang.objects
                .select_related('purchase_order__suplier', 'dibuat_oleh')
                .prefetch_related('item__po_item', 'laporan_selisih')
                .order_by('-tanggal', '-id'))

    def get_serializer_class(self):
        if self.action == 'list':
            return PenerimaanListSerializer
        return PenerimaanBarangSerializer

    def create(self, request):
        """
        Satu transaksi atomik: catat penerimaan, naikkan stok RAW, posting
        Dr Persediaan / Cr GRNI, terbitkan laporan selisih otomatis.
        Gagal satu, batal semua.

        Unggah surat jalan HARUS dilakukan lebih dulu lewat modul dokumen,
        lalu dokumen_id dikirim di payload ini. Penulisan berkas di dalam
        transaksi meninggalkan berkas yatim kalau terjadi rollback.
        """
        s = TerimaBarangSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            penerimaan, laporan ,setoran = services.terima_barang(
                user=request.user, **d,
            )
        except DjangoValidationError as e:
            return _galat(e)

        return Response(
            {
                'penerimaan': PenerimaanBarangSerializer(penerimaan).data,
                'laporan_selisih': LaporanSelisihGudangSerializer(
                    laporan, many=True).data,
                'pesan': (
                    f'{len(laporan)} laporan selisih terbit otomatis.'
                    if laporan else 'Penerimaan sesuai, tidak ada selisih.'
                ),
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Penerimaan tidak bisa diubah. Jurnalnya sudah '
                       'terposting. Terbitkan laporan selisih manual.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Penerimaan tidak bisa dihapus. Terbitkan retur.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=['get'])
    def ringkasan(self, request, pk=None):
        return Response(services.ringkasan_penerimaan(pk))

class LaporanSelisihViewSet(viewsets.ModelViewSet):
    """
    Dua tampilan dari objek yang sama, dipilih dari query param ?sisi=.

    Default `gudang` -- tanpa nilai rupiah. Sisi `akunting` hanya terbuka
    untuk pengguna yang boleh masuk modul akunting.
    """

    modul = 'warehouse'
    permission_classes = [AksesModul]
    filterset_fields = ['penerimaan', 'jenis', 'status', 'resolusi']
    search_fields = ['nomor', 'uraian', 'penerimaan__nomor']

    def get_queryset(self):
        return (LaporanSelisih.objects
                .select_related('penerimaan__purchase_order__suplier',
                                'penerimaan_item__po_item')
                .order_by('-tanggal', '-id'))

    def _sisi_akunting(self):
        return (self.request.query_params.get('sisi') == 'akunting'
                and self.request.user.bisa_akses_modul('akunting'))

    def get_serializer_class(self):
        if self._sisi_akunting():
            return LaporanSelisihAkuntingSerializer
        return LaporanSelisihGudangSerializer

    def create(self, request):
        """Laporan manual untuk temuan yang muncul setelah barang diterima."""
        s = LaporanManualSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            lap = services.laporan_manual(user=request.user, **s.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(LaporanSelisihGudangSerializer(lap).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Laporan tidak bisa diubah langsung. Gunakan aksi '
                       'selesaikan atau tutup.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Laporan tidak bisa dihapus. Tutup saja.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'])
    def terbuka(self, request):
        """
        Klaim yang belum diselesaikan. Dipakai akunting sebelum menerbitkan
        faktur -- jangan bayar penuh kalau masih ada klaim menggantung.
        """
        qs = services.klaim_belum_diselesaikan(
            suplier_id=request.query_params.get('suplier'),
            entitas_id=request.query_params.get('entitas'),
        )
        kelas = (LaporanSelisihAkuntingSerializer if self._sisi_akunting()
                 else LaporanSelisihGudangSerializer)
        return Response(kelas(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def ajukan(self, request, pk=None):
        try:
            lap = services.ajukan_ke_suplier(laporan_id=pk, user=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(LaporanSelisihGudangSerializer(lap).data)

    @action(detail=True, methods=['post'])
    def selesaikan(self, request, pk=None):
        """
        Menetapkan resolusi. Ini keputusan finansial, jadi hanya untuk
        pengguna yang boleh masuk modul akunting.
        """
        if not request.user.bisa_akses_modul('akunting'):
            return Response(
                {'detail': 'Resolusi selisih ditetapkan modul akunting.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        s = SelesaikanSelisihSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            lap = services.selesaikan_laporan(
                laporan_id=pk, user=request.user, **s.validated_data,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(LaporanSelisihAkuntingSerializer(lap).data)

    @action(detail=True, methods=['post'])
    def tutup(self, request, pk=None):
        if not request.user.bisa_akses_modul('akunting'):
            return Response(
                {'detail': 'Penutupan selisih ditetapkan modul akunting.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        s = TutupSelisihSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            lap = services.tutup_laporan(laporan_id=pk, user=request.user,
                                         alasan=s.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(LaporanSelisihAkuntingSerializer(lap).data)


class PackagingViewSet(viewsets.ModelViewSet):
    modul = 'warehouse'
    permission_classes = [AksesModul]
    queryset = (Packaging.objects
                .select_related('produk', 'grup_bahan')
                .order_by('-tanggal', '-id'))
    serializer_class = PackagingSerializer
    filterset_fields = ['produk', 'grup_bahan', 'tanggal']
