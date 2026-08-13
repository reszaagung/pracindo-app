"""
Endpoint persediaan — inventory/views.py

Semua logika bisnis ada di services.py. View memvalidasi payload,
memeriksa hak, dan meneruskan. Tidak ada perhitungan qty/nilai di sini.

Stok punya DUA tampilan dari objek yang sama, dipilih lewat ?sisi=:
    default          -> tanpa nilai rupiah
    ?sisi=akunting   -> dengan nilai, hanya untuk yang punya akses akunting

FILTER
    filterset_fields sengaja TIDAK dipakai. Kalau DjangoFilterBackend
    belum terpasang di DEFAULT_FILTER_BACKENDS, atribut itu diabaikan
    diam-diam dan endpoint mengembalikan SEMUA baris -- termasuk grup
    milik entitas lain. Filter ditulis eksplisit di get_queryset().

POSISI KLAIM
    Tidak punya versi "gudang". Setiap kolomnya rupiah -- setor, ambil,
    rugi, bersih -- jadi tidak ada yang tersisa untuk ditampilkan setelah
    disaring. Menolak lebih jujur daripada mengembalikan objek kosong.
    Dulu endpoint ini terbuka untuk siapa pun yang punya akses modul
    inventory, termasuk staff gudang.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from staff_user.models import Role
from staff_user.permissions import AksesModul, HanyaSupervisor, PunyaRole

from . import services
from .models import (
    Kemasan, MutasiStok, NilaiEkuivalen, PosisiKlaim, Stok, Tangki,
)
from .serializers import (
    KemasanSerializer, KlaimHasilSerializer, KlaimKemasanSerializer,
    LunasSerializer, LuruskanSerializer, MutasiKlaimSerializer,
    MutasiStokAkuntingSerializer, MutasiStokSerializer,
    NilaiEkuivalenSerializer, OpnameSerializer, PosisiKlaimSerializer,
    SetorKePoolSerializer, StokAkuntingDetailSerializer,
    StokAkuntingSerializer, StokGudangDetailSerializer,
    StokGudangListRinciSerializer, StokGudangSerializer,
    TangkiSerializer,
)

GudangProduksi = PunyaRole.dengan(Role.GUDANG, Role.PRODUKSI)

# =========================================================
# SAKLAR PENGEMBANGAN — JANGAN AKTIF DI PRODUKSI
# =========================================================
# BUKA_API=1 mengosongkan permission_classes di seluruh modul ini.
# List kosong berarti loop pemeriksaan di check_permissions() tidak
# pernah berjalan -- lebih bersih daripada [AllowAny], yang tetap
# memanggil has_permission() satu per satu.
#
# Autentikasi TIDAK ikut dimatikan: request.user tetap AnonymousUser
# kalau tidak login, jadi _akunting() tetap False dan layar tetap
# menampilkan versi tanpa rupiah. Itu disengaja -- penyaringan rupiah
# justru paling perlu diuji dalam kondisi ini.
#
# Yang hilang: atribusi. POST /setor-ke-pool/ menulis ke MutasiKlaim
# yang append-only, jadi setoran anonim tidak bisa ditelusuri dan tidak
# bisa dihapus. Untuk membaca selama pengembangan, aman. Untuk menulis,
# sebaiknya tetap login.
BUKA = getattr(settings, 'BUKA_API', False)

IZIN_BACA = [] if BUKA else [AksesModul]
IZIN_TULIS = [] if BUKA else [GudangProduksi]
IZIN_SUPERVISOR = [] if BUKA else [HanyaSupervisor]


def _galat(e):
    if hasattr(e, 'message_dict'):
        isi = e.message_dict
    elif hasattr(e, 'messages'):
        isi = {'detail': ' '.join(e.messages)}
    else:
        isi = {'detail': str(e)}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


def _akunting(request):
    cek = getattr(request.user, 'bisa_akses_modul', None)
    return bool(callable(cek) and cek('akunting'))


def _tolak_non_akunting():
    return Response(
        {'detail': 'Seluruh kolom di sini bernilai rupiah. Butuh akses '
                   'modul akunting.'},
        status=status.HTTP_403_FORBIDDEN)


class BasisInventory:
    modul = 'inventory'
    permission_classes = IZIN_BACA


# =========================================================
# STOK
# =========================================================

class StokViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):
    # JANGAN deklarasikan permission_classes di sini. Atribut kelas anak
    # MENIMPA milik BasisInventory, jadi melonggarkan induk tidak ada
    # efeknya. Itu yang membuat endpoint ini 403 padahal induknya sudah
    # dibuka -- dan GudangProduksi justru lebih ketat dari AksesModul
    # karena menuntut user.role tepat GUDANG atau PRODUKSI.

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
        if p.get('tangki'):
            qs = qs.filter(tangki_id=p['tangki'])
        if p.get('ada_isi') == '1':
            qs = qs.filter(qty__gt=0)
        # `rinci=1` menyertakan kepemilikan di DAFTAR. Prefetch-nya wajib:
        # tanpa ini satu baris stok = satu query tambahan.
        if self.action == 'retrieve' or p.get('rinci') == '1':
            qs = qs.prefetch_related('kepemilikan__entitas')
        return qs

    def _sisi_akunting(self):
        return (self.request.query_params.get('sisi') == 'akunting'
                and _akunting(self.request))

    def get_serializer_class(self):
        ak = self._sisi_akunting()
        if self.action == 'retrieve':
            return (StokAkuntingDetailSerializer if ak
                    else StokGudangDetailSerializer)
        if self.request.query_params.get('rinci') == '1':
            # Rincian kepemilikan hanya tersedia tanpa rupiah. Yang butuh
            # nilai per entitas memakai endpoint detail.
            return StokGudangListRinciSerializer
        return StokAkuntingSerializer if ak else StokGudangSerializer


class TangkiViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):
    serializer_class = TangkiSerializer

    def get_queryset(self):
        qs = (Tangki.objects.select_related('grup_bahan', 'produk_terisi')
              .order_by('kode'))
        p = self.request.query_params
        if p.get('grup'):
            qs = qs.filter(grup_bahan_id=p['grup'])
        if p.get('aktif') in ('1', 'true', 'True'):
            qs = qs.filter(aktif=True)
        return qs


class KemasanViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):
    """Daftar kemasan yang tersedia untuk satu produk curah."""
    serializer_class = KemasanSerializer

    def get_queryset(self):
        qs = (Kemasan.objects.filter(aktif=True)
              .select_related('produk_curah', 'produk_kemasan')
              .order_by('produk_curah__kode', 'isi'))
        curah = self.request.query_params.get('curah')
        if curah:
            qs = qs.filter(produk_curah_id=curah)
        return qs


class MutasiStokViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        qs = (MutasiStok.objects.select_related('stok__produk')
              .order_by('-tanggal', '-id'))
        p = self.request.query_params
        if p.get('stok'):
            qs = qs.filter(stok_id=p['stok'])
        if p.get('jenis'):
            qs = qs.filter(jenis=p['jenis'])
        if p.get('referensi'):
            qs = qs.filter(referensi=p['referensi'])
        return qs

    def get_serializer_class(self):
        return (MutasiStokAkuntingSerializer if _akunting(self.request)
                else MutasiStokSerializer)


class PosisiKlaimViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):
    serializer_class = PosisiKlaimSerializer

    def get_queryset(self):
        qs = (PosisiKlaim.objects.select_related('entitas', 'grup_bahan')
              .order_by('grup_bahan', 'entitas__kode'))
        p = self.request.query_params
        if p.get('grup'):
            qs = qs.filter(grup_bahan_id=p['grup'])
        if p.get('entitas'):
            qs = qs.filter(entitas_id=p['entitas'])
        return qs

    def list(self, request, *args, **kwargs):
        grup_id = request.query_params.get('grup')
        if not grup_id:
            return Response({'detail': 'Parameter grup wajib diisi.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not _akunting(request):
            return _tolak_non_akunting()
        return Response(services.posisi_grup(grup_id))

    def retrieve(self, request, *args, **kwargs):
        if not _akunting(request):
            return _tolak_non_akunting()
        return super().retrieve(request, *args, **kwargs)


class NilaiEkuivalenViewSet(BasisInventory, viewsets.ReadOnlyModelViewSet):
    serializer_class = NilaiEkuivalenSerializer

    def get_queryset(self):
        qs = (NilaiEkuivalen.objects.select_related('produk')
              .order_by('produk__kode', '-berlaku_sejak'))
        produk = self.request.query_params.get('produk')
        if produk:
            qs = qs.filter(produk_id=produk)
        return qs


# =========================================================
# PEMBACAAN POOL & TANGKI
# =========================================================

class IsiPoolView(BasisInventory, APIView):
    def get(self, request):
        grup_id = request.query_params.get('grup')
        if not grup_id:
            return Response({'detail': 'Parameter grup wajib diisi.'},
                            status=status.HTTP_400_BAD_REQUEST)
        hasil, total = services.isi_pool(grup_id)
        if not _akunting(request):
            for r in hasil:
                r.pop('nilai', None)
                r.pop('harga_rata', None)
            return Response({'produk': hasil})
        return Response({'produk': hasil, 'total_nilai': total})


class IsiTangkiView(BasisInventory, APIView):
    """Nominal yang tersimpan di satu tangki. Dasar tarif pengepakan."""
    def get(self, request, pk):
        data = services.isi_tangki(pk)
        if not _akunting(request):
            data.pop('nilai', None)
            data.pop('harga_rata', None)
        return Response(data)


class RencanaKemasanView(BasisInventory, APIView):
    """
    Pratinjau pengepakan sebelum tombol ditekan.

    GET ?kemasan=&grup=&jumlah=&tangki=

    Angka di sini dihitung server dengan aritmetika yang sama persis
    seperti saat eksekusi, jadi tidak akan meleset dari hasil akhir.
    Klien TIDAK boleh menghitung sendiri dari harga_rata.
    """
    def get(self, request):
        p = request.query_params
        if not (p.get('kemasan') and p.get('grup') and p.get('jumlah')):
            return Response(
                {'detail': 'Parameter kemasan, grup, dan jumlah wajib.'},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            data = services.rencana_kemasan(
                kemasan_id=int(p['kemasan']),
                grup_bahan_id=int(p['grup']),
                jumlah=p['jumlah'],
                tangki_pool_id=int(p['tangki']) if p.get('tangki') else None,
            )
        except (DjangoValidationError, ObjectDoesNotExist) as e:
            return _galat(e)
        if not _akunting(request):
            data.pop('nilai', None)
            data.pop('tarif_tampilan', None)
        return Response(data)


# =========================================================
# PENULISAN
# =========================================================

class BasisTulis(APIView):
    permission_classes = IZIN_TULIS
    serializer = None
    fungsi = None
    prefix = 'op'

    def post(self, request):
        s = self.serializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'{self.prefix}:{uuid.uuid4()}'
        try:
            hasil = self.fungsi(idem_key=idem_key, **d)
        except (DjangoValidationError, ObjectDoesNotExist) as e:
            return _galat(e)
        return Response(self.bentuk(hasil, request),
                        status=status.HTTP_201_CREATED)

    def bentuk(self, hasil, request):
        m_out, m_in, klaim, posisi = hasil
        ser = (MutasiStokAkuntingSerializer if _akunting(request)
               else MutasiStokSerializer)
        isi = {
            'mutasi_keluar': ser(m_out).data if m_out else None,
            'mutasi_masuk': ser(m_in).data if m_in else None,
        }
        if _akunting(request):
            isi['klaim'] = MutasiKlaimSerializer(klaim).data if klaim else None
            isi['posisi'] = PosisiKlaimSerializer(posisi).data if posisi else None
        return isi


class SetorKePoolView(BasisTulis):
    serializer = SetorKePoolSerializer
    fungsi = staticmethod(services.setor_ke_pool)
    prefix = 'setor'


class KlaimHasilView(BasisTulis):
    serializer = KlaimHasilSerializer
    fungsi = staticmethod(services.klaim_hasil)
    prefix = 'klaim'


class KlaimKemasanView(BasisTulis):
    """
    Pengepakan: curah keluar dalam kg, kemasan masuk dalam pcs.

    Hak berkurang sebesar PORSI nilai tangki, bukan jumlah x tarif bulat.
    Kalau klien menampilkan tarif yang sudah dibulatkan, angkanya akan
    sedikit berbeda dari hasil ini -- yang benar adalah hasil ini.
    """
    serializer = KlaimKemasanSerializer
    fungsi = staticmethod(services.klaim_kemasan)
    prefix = 'kemas'


# =========================================================
# SUPERVISOR
# =========================================================

class OpnameView(APIView):
    """
    Menyesuaikan catatan ke fisik. Supervisor saja -- penyalahgunaannya
    sulit dideteksi karena tidak ada dokumen pembanding independen
    seperti PO atau resep produksi.
    """
    permission_classes = IZIN_SUPERVISOR

    def post(self, request):
        s = OpnameSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'opname:{uuid.uuid4()}'
        try:
            mutasi = services.sesuaikan_stok(idem_key=idem_key, **d)
        except DjangoValidationError as e:
            return _galat(e)
        ser = (MutasiStokAkuntingSerializer if _akunting(request)
               else MutasiStokSerializer)
        return Response(ser(mutasi).data, status=status.HTTP_201_CREATED)


class LunasView(APIView):
    """
    Pelunasan antar entitas. WAJIB dua sisi: yang membayar naik, yang
    menerima turun, jumlahnya nol. Pelunasan satu sisi menggeser total
    klaim tanpa menyentuh pool.
    """
    permission_classes = IZIN_SUPERVISOR

    def post(self, request):
        s = LunasSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'lunas:{uuid.uuid4()}'
        try:
            b1, b2 = services.lunasi_antar_entitas(idem_key=idem_key, **d)
        except DjangoValidationError as e:
            return _galat(e)
        return Response({
            'bayar': MutasiKlaimSerializer(b1).data if b1 else None,
            'terima': MutasiKlaimSerializer(b2).data if b2 else None,
        }, status=status.HTTP_201_CREATED)


class LuruskanView(APIView):
    """
    Menutup selisih pembulatan dengan baris KOREKSI bertanggal.

    Selisih di atas `batas` ditolak: itu bukan pembulatan, dan menutupnya
    menghapus jejak yang dibutuhkan untuk menemukan penyebabnya.
    """
    permission_classes = IZIN_SUPERVISOR

    def post(self, request):
        s = LuruskanSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        idem_key = d.pop('idem_key') or f'luruskan:{uuid.uuid4()}'
        try:
            baris = services.luruskan_pembulatan(idem_key=idem_key, **d)
        except DjangoValidationError as e:
            return _galat(e)
        if baris is None:
            return Response({'detail': 'Tidak ada selisih.'},
                            status=status.HTTP_200_OK)
        return Response(MutasiKlaimSerializer(baris).data,
                        status=status.HTTP_201_CREATED)


class VerifikasiView(APIView):
    """
    Dipakai kalau angka di layar terlihat aneh, dan dijalankan nightly.

    ?grup= wajib untuk pemeriksaan pool bersih.
    ?toleransi= menandai selisih kecil sebagai 'dalam_toleransi' --
    menandai, bukan menyembunyikan. Selisihnya tetap ditampilkan apa
    adanya.
    """
    permission_classes = IZIN_SUPERVISOR

    def get(self, request):
        from decimal import Decimal

        grup_id = request.query_params.get('grup')
        toleransi = Decimal(request.query_params.get('toleransi') or '0')
        hasil = {
            'kepemilikan': services.verifikasi_kepemilikan(grup_bahan_id=grup_id),
            'posisi_cache': services.verifikasi_posisi_cache(grup_bahan_id=grup_id),
        }
        if grup_id:
            hasil['pool_bersih'] = services.verifikasi_pool_bersih(
                grup_bahan_id=grup_id, toleransi=toleransi)
        return Response(hasil)