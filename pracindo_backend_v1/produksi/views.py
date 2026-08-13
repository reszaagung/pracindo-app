"""
Endpoint produksi — produksi/views.py

Semua logika ada di services.py. View memvalidasi payload, memeriksa hak,
dan meneruskan.

HAK AKSES PER AKSI
    baca            ModulProduksi
    buat / batal    OperatorSesi
    mulai           OperatorSesi   (bahan benar-benar keluar dari pool)
    selesaikan      OperatorSesi, tapi abaikan_susut butuh supervisor
    gagalkan        OperatorSesi   (menerbitkan pembebanan kerugian)

RUPIAH
    Operator lantai melihat qty, tangki, dan rendemen -- tidak melihat
    rupiah. Penyaringan itu harus konsisten di SETIAP endpoint, bukan
    hanya di retrieve() dan kapasitas. Aksi `banding` dulu mengembalikan
    nilai_input, nilai_hasil, dan harga_per_satuan tanpa saringan apa pun.
"""
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ObjectDoesNotExist
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from staff_user.permissions import HanyaSupervisor

from .models import (
    JenisPengukuran, Resep, SesiCatatan, SesiInput, SesiPengukuran,
    SesiProduksi,
)
from .permissions import ModulProduksi, OperatorSesi
from . import serializers, services

# Kolom rupiah yang harus hilang untuk yang tidak punya akses akunting.
KOLOM_RUPIAH_SESI = ('nilai_input', 'nilai_hasil', 'nilai_kerugian',
                     'harga_hasil_per_satuan')

# =========================================================
# SAKLAR PENGEMBANGAN — JANGAN AKTIF DI PRODUKSI
# =========================================================
# BUKA_API=1 mengosongkan permission_classes di seluruh modul ini.
# List kosong berarti loop di check_permissions() tidak pernah berjalan.
#
# JANGAN mendeklarasikan permission_classes lagi di kelas anak. Atribut
# kelas anak MENIMPA milik induk, jadi melonggarkan induk tidak ada
# efeknya -- persis yang terjadi di StokViewSet inventory dan membuat
# endpoint tetap 403 walau induknya sudah dibuka.
#
# Autentikasi tidak ikut dimatikan: request.user tetap AnonymousUser,
# jadi _boleh_akunting() dan _supervisor() tetap False. Layar akan
# menampilkan versi operator tanpa rupiah, dan abaikan_susut tetap
# ditolak. Itu disengaja.
BUKA = getattr(settings, 'BUKA_API', False)

IZIN_BACA = [] if BUKA else [ModulProduksi]


def _galat(e):
    """
    Menyamakan bentuk galat dengan inventory. Dulu memakai str(e),
    sehingga frontend menerima "['Stok tidak cukup.']" lengkap dengan
    kurung siku dan tanda kutip.
    """
    if hasattr(e, 'message_dict'):
        isi = e.message_dict
    elif hasattr(e, 'messages'):
        isi = {'detail': ' '.join(e.messages)}
    else:
        isi = {'detail': str(e)}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


def _boleh_akunting(request):
    cek = getattr(request.user, 'bisa_akses_modul', None)
    return bool(callable(cek) and cek('akunting'))


def _supervisor(request):
    """
    Memakai kelas permission yang sama dengan endpoint supervisor lain.

    Dulu ditulis ulang di sini sebagai getattr(request.user, 'supervisor',
    False). Kalau atribut itu berganti nama di staff_user, salinan yang
    duplikat gagal DIAM-DIAM: supervisor tidak pernah bisa menyetujui
    apa pun dan tidak ada pesan galat yang menjelaskan kenapa.
    """
    return HanyaSupervisor().has_permission(request, None)


class JenisPengukuranViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = IZIN_BACA
    queryset = JenisPengukuran.objects.filter(aktif=True).order_by('nama')
    serializer_class = serializers.JenisPengukuranSerializer


class ResepViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = IZIN_BACA
    queryset = (Resep.objects.filter(aktif=True)
                .select_related('produk_jadi')
                .prefetch_related('item__bahan')
                .order_by('produk_jadi__kode', '-versi'))
    serializer_class = serializers.ResepSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        produk = self.request.query_params.get('produk')
        if produk:
            qs = qs.filter(produk_jadi_id=produk)
        return qs


class SesiViewSet(viewsets.ModelViewSet):
    permission_classes = IZIN_BACA

    queryset = (SesiProduksi.objects
                .select_related('produk_jadi', 'grup_bahan', 'tangki_hasil',
                                'dibuat_oleh')
                .all())

    AKSI_OPERATOR = {'create', 'buat_rnd', 'mulai', 'selesaikan',
                     'gagalkan', 'batalkan'}

    def get_permissions(self):
        if BUKA:
            return []
        if self.action in self.AKSI_OPERATOR:
            return [ModulProduksi(), OperatorSesi()]
        return [ModulProduksi()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get('grup'):
            qs = qs.filter(grup_bahan_id=p['grup'])
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('jenis'):
            qs = qs.filter(jenis_sesi=p['jenis'])
        return qs.order_by('-tanggal', '-id')

    def get_serializer_class(self):
        if _boleh_akunting(self.request):
            return serializers.SesiListAkuntingSerializer
        return serializers.SesiListSerializer

    def retrieve(self, request, *args, **kwargs):
        sesi = self.get_object()
        data = services.ringkasan_sesi(sesi.id)
        if not _boleh_akunting(request):
            for k in KOLOM_RUPIAH_SESI:
                data.pop(k, None)
            for baris in data['input']:
                baris.pop('nilai', None)
                baris.pop('harga_per_satuan', None)
        return Response(data)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            'PUT/PATCH',
            detail='Sesi tidak diubah lewat PUT. Gunakan aksi mulai, '
                   'selesaikan, gagalkan, atau batalkan.')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            'DELETE',
            detail='Sesi tidak dihapus. Gunakan batalkan (DRAFT) atau '
                   'gagalkan (BERJALAN).')

    def create(self, request, *args, **kwargs):
        """POST /produksi/sesi/ -> sesi rutin berbasis resep."""
        ser = serializers.BuatSesiProduksiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            sesi = services.buat_sesi_produksi(user=request.user,
                                               **ser.validated_data)
        except Resep.DoesNotExist:
            return Response({'detail': 'Resep tidak ditemukan.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as e:
            return _galat(e)
        return Response({'id': sesi.id, 'nomor': sesi.nomor},
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='rnd')
    def buat_rnd(self, request):
        """POST /produksi/sesi/rnd/ -> sesi eksperimen, bahan manual."""
        ser = serializers.BuatSesiRndSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            sesi = services.buat_sesi_rnd(user=request.user,
                                          **ser.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return Response({'id': sesi.id, 'nomor': sesi.nomor},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mulai(self, request, pk=None):
        ser = serializers.MulaiSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()

        override = {}
        for baris in ser.validated_data['baris']:
            tangki_id = baris.get('tangki_id')
            kunci = (baris['bahan_id'], tangki_id) if tangki_id else baris['bahan_id']
            override[kunci] = baris['qty_aktual']

        try:
            services.mulai_sesi(sesi_id=sesi.id, qty_aktual=override)
        except DjangoValidationError as e:
            return _galat(e)
        return self.retrieve(request, pk=pk)

    @action(detail=True, methods=['post'])
    def selesaikan(self, request, pk=None):
        ser = serializers.SelesaikanSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()

        abaikan = ser.validated_data['abaikan_susut']
        if abaikan and not _supervisor(request):
            return Response(
                {'detail': 'Menembus batas susut wajar butuh persetujuan '
                           'supervisor.'},
                status=status.HTTP_403_FORBIDDEN)

        try:
            services.selesaikan_sesi(
                sesi_id=sesi.id,
                qty_hasil=ser.validated_data['qty_hasil'],
                abaikan_susut=abaikan,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return self.retrieve(request, pk=pk)

    @action(detail=True, methods=['post'])
    def gagalkan(self, request, pk=None):
        ser = serializers.GagalkanSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()
        try:
            services.gagalkan_sesi(
                sesi_id=sesi.id,
                alasan=ser.validated_data['alasan'],
                kategori=ser.validated_data['kategori_kegagalan'],
            )
        except DjangoValidationError as e:
            return _galat(e)
        return self.retrieve(request, pk=pk)

    @action(detail=True, methods=['post'])
    def batalkan(self, request, pk=None):
        ser = serializers.BatalSesiSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sesi = self.get_object()
        try:
            services.batalkan_sesi(sesi_id=sesi.id,
                                   alasan=ser.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return self.retrieve(request, pk=pk)

    @action(detail=True, methods=['get'])
    def rencana(self, request, pk=None):
        """Baris rencana per tangki, untuk layar SesiPersiapan."""
        sesi = self.get_object()
        baris = (SesiInput.objects.filter(sesi=sesi)
                 .select_related('bahan', 'tangki').order_by('id'))
        return Response(serializers.SesiInputSerializer(baris, many=True).data)

    @action(detail=True, methods=['get', 'post'])
    def pengukuran(self, request, pk=None):
        sesi = self.get_object()
        if request.method == 'GET':
            data = (SesiPengukuran.objects.filter(sesi=sesi)
                    .select_related('nama', 'dicatat_oleh'))
            return Response(
                serializers.SesiPengukuranSerializer(data, many=True).data)

        ser = serializers.SesiPengukuranSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            ser.save(sesi=sesi, dicatat_oleh=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def catatan(self, request, pk=None):
        sesi = self.get_object()
        if request.method == 'GET':
            data = SesiCatatan.objects.filter(sesi=sesi).select_related('penulis')
            return Response(
                serializers.SesiCatatanSerializer(data, many=True).data)

        ser = serializers.SesiCatatanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(sesi=sesi, penulis=request.user)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='pratinjau-kerugian')
    def pratinjau_kerugian(self, request, pk=None):
        if not _boleh_akunting(request) and not _supervisor(request):
            return Response({'detail': 'Butuh akses akunting atau supervisor.'},
                            status=status.HTTP_403_FORBIDDEN)
        sesi = self.get_object()
        return Response(services.pratinjau_kerugian(sesi.id))

    @action(detail=False, methods=['get'])
    def banding(self, request):
        ids = request.query_params.get('ids', '')
        id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        if not id_list:
            return Response({'detail': 'Parameter ids tidak valid.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(id_list) > 8:
            return Response({'detail': 'Maksimal 8 sesi sekali banding.'},
                            status=status.HTTP_400_BAD_REQUEST)

        data = services.banding_batch(id_list)
        # banding_batch() mengembalikan nilai_input, nilai_hasil, dan
        # harga_per_satuan. Operator lantai membandingkan rendemen dan
        # pengukuran, bukan rupiah.
        if not _boleh_akunting(request):
            for s in data['sesi']:
                for k in ('nilai_input', 'nilai_hasil', 'harga_per_satuan'):
                    s.pop(k, None)
        return Response(data)


@api_view(['GET'])
@permission_classes(IZIN_BACA)
def kalkulasi_kapasitas(request):
    """GET /produksi/kapasitas/?grup=X&produk=Y&tanggal=Z"""
    grup = request.query_params.get('grup')
    produk = request.query_params.get('produk')
    tanggal = request.query_params.get('tanggal')

    if not grup or not produk:
        return Response({'detail': 'Parameter grup dan produk wajib diisi.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        data = services.hitung_kapasitas(
            grup_bahan_id=int(grup), produk_jadi_id=int(produk),
            tanggal=tanggal or None,
        )
    except (DjangoValidationError, ObjectDoesNotExist) as e:
        return _galat(e)

    if not _boleh_akunting(request):
        for r in data['rincian']:
            r.pop('nilai_tersedia', None)
            r.pop('harga_rata', None)
    return Response(data)


@api_view(['GET'])
@permission_classes(IZIN_BACA)
def alokasi_bahan(request):
    """
    GET /produksi/alokasi/?grup=X&bahan=Y&qty=Z

    Memberi tahu dari tangki mana saja bahan akan ditarik, sebelum sesi
    dibuat. Dipakai form produksi supaya operator tidak kaget saat
    ternyata satu bahan diambil dari dua tangki.
    """
    grup = request.query_params.get('grup')
    bahan = request.query_params.get('bahan')
    qty = request.query_params.get('qty')
    if not (grup and bahan and qty):
        return Response({'detail': 'Parameter grup, bahan, dan qty wajib.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        potongan = services.alokasi_tangki(int(grup), int(bahan), qty)
    except DjangoValidationError as e:
        return _galat(e)
    return Response([{'tangki_id': t, 'qty': q} for t, q in potongan])