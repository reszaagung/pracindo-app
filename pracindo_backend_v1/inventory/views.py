"""
Endpoint persediaan — inventory/views.py

Semua logika bisnis ada di services.py. View di sini hanya
memvalidasi payload dan meneruskannya -- tidak ada perhitungan qty/nilai
di file ini.

Stok punya DUA tampilan dari objek yang sama, dipilih lewat ?sisi=:
    default          -> StokGudangSerializer, tanpa nilai rupiah
    ?sisi=akunting   -> StokAkuntingSerializer, hanya untuk modul akunting

MutasiStok, MutasiKlaim, PosisiKlaim append-only: semua lewat
ReadOnlyModelViewSet, tidak ada rute update/partial_update sama sekali
(bukan di-override jadi 405 -- routernya memang tidak membuat rutenya).
"""
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from staff_user.models import Role
from staff_user.permissions import AksesModul, HanyaSupervisor, PunyaRole

from . import services
from .models import MutasiStok, NilaiEkuivalen, PosisiKlaim, Stok, Tangki
from .serializers import (
    KlaimHasilSerializer, MutasiKlaimSerializer, MutasiStokSerializer,
    NilaiEkuivalenSerializer, OpnameSerializer, PosisiKlaimSerializer,
    SetorKePoolSerializer, StokAkuntingDetailSerializer,
    StokAkuntingSerializer, StokGudangDetailSerializer, StokGudangSerializer,
    TangkiSerializer,
)

GudangProduksi = PunyaRole.dengan(Role.GUDANG, Role.PRODUKSI)


def _galat(e):
    isi = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# STOK
# =========================================================

class StokViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'inventory'
    permission_classes = [AksesModul]

    def get_queryset(self):
        qs = (Stok.objects.select_related('produk', 'grup_bahan', 'tangki')
              .order_by('lapis', 'produk__kode'))
        p = self.request.query_params
        if p.get('lapis'):
            qs = qs.filter(lapis=p['lapis'])
        if p.get('grup'):
            qs = qs.filter(grup_bahan_id=p['grup'])
        if p.get('produk'):
            qs = qs.filter(produk_id=p['produk'])
        if self.action == 'retrieve':
            qs = qs.prefetch_related('kepemilikan__entitas')
        return qs

    def _sisi_akunting(self):
        return (self.request.query_params.get('sisi') == 'akunting'
                and self.request.user.bisa_akses_modul('akunting'))

    def get_serializer_class(self):
        akunting = self._sisi_akunting()
        if self.action == 'retrieve':
            return (StokAkuntingDetailSerializer if akunting
                    else StokGudangDetailSerializer)
        return StokAkuntingSerializer if akunting else StokGudangSerializer


# =========================================================
# TANGKI
# =========================================================

class TangkiViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'inventory'
    permission_classes = [AksesModul]
    queryset = (Tangki.objects.select_related('grup_bahan', 'produk_terisi')
                .order_by('kode'))
    serializer_class = TangkiSerializer
    filterset_fields = ['grup_bahan', 'aktif']


# =========================================================
# MUTASI STOK -- append-only
# =========================================================

class MutasiStokViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'inventory'
    permission_classes = [AksesModul]
    queryset = (MutasiStok.objects.select_related('stok__produk')
                .order_by('-tanggal', '-id'))
    serializer_class = MutasiStokSerializer
    filterset_fields = ['stok', 'jenis']


# =========================================================
# POSISI KLAIM -- append-only, list via services.posisi_grup()
# =========================================================

class PosisiKlaimViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'inventory'
    permission_classes = [AksesModul]
    queryset = (PosisiKlaim.objects.select_related('entitas', 'grup_bahan')
                .order_by('grup_bahan', 'entitas__kode'))
    serializer_class = PosisiKlaimSerializer
    filterset_fields = ['grup_bahan', 'entitas']

    def list(self, request, *args, **kwargs):
        grup_id = request.query_params.get('grup')
        if not grup_id:
            return Response({'detail': 'Parameter grup wajib diisi.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(services.posisi_grup(grup_id))


# =========================================================
# NILAI EKUIVALEN
# =========================================================

class NilaiEkuivalenViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'inventory'
    permission_classes = [AksesModul]
    queryset = (NilaiEkuivalen.objects.select_related('produk')
                .order_by('produk__kode', '-berlaku_sejak'))
    serializer_class = NilaiEkuivalenSerializer
    filterset_fields = ['produk']


# =========================================================
# ISI POOL
# =========================================================

class IsiPoolView(APIView):
    modul = 'inventory'
    permission_classes = [AksesModul]

    def get(self, request):
        grup_id = request.query_params.get('grup')
        if not grup_id:
            return Response({'detail': 'Parameter grup wajib diisi.'},
                            status=status.HTTP_400_BAD_REQUEST)
        hasil, total = services.isi_pool(
            grup_id, tanggal=request.query_params.get('tanggal'),
        )
        return Response({'produk': hasil, 'total_nilai': total})


# =========================================================
# SETOR KE POOL / KLAIM HASIL -- GUDANG dan PRODUKSI
# =========================================================

class SetorKePoolView(APIView):
    permission_classes = [GudangProduksi]

    def post(self, request):
        s = SetorKePoolSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'setor:{uuid.uuid4()}'
        try:
            m_out, m_in, klaim, posisi = services.setor_ke_pool(
                idem_key=idem_key, **d,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response({
            'mutasi_keluar': MutasiStokSerializer(m_out).data if m_out else None,
            'mutasi_masuk': MutasiStokSerializer(m_in).data if m_in else None,
            'klaim': MutasiKlaimSerializer(klaim).data if klaim else None,
            'posisi': PosisiKlaimSerializer(posisi).data if posisi else None,
        }, status=status.HTTP_201_CREATED)


class KlaimHasilView(APIView):
    permission_classes = [GudangProduksi]

    def post(self, request):
        s = KlaimHasilSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'klaim:{uuid.uuid4()}'
        try:
            m_out, m_in, klaim, posisi = services.klaim_hasil(
                idem_key=idem_key, **d,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response({
            'mutasi_keluar': MutasiStokSerializer(m_out).data if m_out else None,
            'mutasi_masuk': MutasiStokSerializer(m_in).data if m_in else None,
            'klaim': MutasiKlaimSerializer(klaim).data if klaim else None,
            'posisi': PosisiKlaimSerializer(posisi).data if posisi else None,
        }, status=status.HTTP_201_CREATED)


# =========================================================
# OPNAME -- Supervisor saja
# =========================================================

class OpnameView(APIView):
    """
    Menyesuaikan catatan ke fisik. Hanya Supervisor -- penyalahgunaannya
    sulit dideteksi karena tidak ada dokumen pembanding independen seperti
    PO atau resep produksi.
    """

    permission_classes = [HanyaSupervisor]

    def post(self, request):
        s = OpnameSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'opname:{uuid.uuid4()}'
        try:
            mutasi = services.sesuaikan_stok(idem_key=idem_key, **d)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(MutasiStokSerializer(mutasi).data,
                        status=status.HTTP_201_CREATED)


# =========================================================
# VERIFIKASI -- Supervisor saja
# =========================================================

class VerifikasiView(APIView):
    """
    Dipakai kalau angka di layar terlihat aneh. ?grup= opsional -- kalau
    diisi, invariant (2) (pool bersih) untuk grup itu ikut diperiksa.
    """

    permission_classes = [HanyaSupervisor]

    def get(self, request):
        grup_id = request.query_params.get('grup')
        hasil = {
            'kepemilikan': services.verifikasi_kepemilikan(grup_bahan_id=grup_id),
            'posisi_cache': services.verifikasi_posisi_cache(grup_bahan_id=grup_id),
        }
        if grup_id:
            hasil['pool_bersih'] = services.verifikasi_pool_bersih(
                grup_bahan_id=grup_id,
            )
        return Response(hasil)
