"""
Endpoint akunting — akunting/views.py

View TIDAK berisi logika bisnis. Semua operasi yang mengubah state
memanggil services.py, supaya row lock, idempotency, dan posting jurnal
konsisten di semua jalur -- API maupun shell.

Setiap viewset menetapkan `modul` dan memakai AksesModul. Permission class
itu MENOLAK view yang tidak punya atribut `modul` -- gagal tertutup.
"""
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Prefetch
import django_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models.pengeluaran import PengeluaranKas

# Tambahkan di deretan import .serializers Anda:
from .serializers import PengeluaranKasSerializer
from staff_user.models import Role
from staff_user.permissions import AksesModul, PunyaRole

from . import services
from .models import (
    Akun, FakturPembelian, FakturPenjualan, JurnalUmum, PurchaseOrder,
    PurchaseOrderItem, UangMukaSuplier,
)
from .serializers import (
    AkunSerializer, BatalPOSerializer, BayarSerializer,
    FakturListSerializer, FakturPembelianSerializer, FakturPenjualanSerializer,
    JurnalBalikSerializer, JurnalUmumSerializer,
    PurchaseOrderListSerializer, PurchaseOrderSerializer,
    TerbitkanFakturJualSerializer, TerbitkanFakturSerializer,
    TerimaPiutangSerializer, UangMukaSerializer, UbahItemPOSerializer,
    BuatPOSerializer,
)

def batasi_entitas(qs, request, field="entitas"):
    """
    Saring queryset menurut entitas yang boleh diakses pengguna.

    GAGAL TERTUTUP, BUKAN MELEDAK

        Versi sebelumnya langsung membaca u.entitas_diizinkan.exists().
        AnonymousUser tidak punya atribut itu, jadi hasilnya AttributeError
        -> 500 -- dan 500 tidak menyaring apa pun. Filter yang gagal
        terbuka lebih berbahaya daripada filter yang menolak, karena
        kegagalannya terlihat seperti kerusakan biasa, bukan kebocoran.

    SATU QUERY, BUKAN DUA

        `.exists()` lalu `.all()` menembak database dua kali untuk satu
        keputusan, dan di antara keduanya daftarnya bisa berubah.
        values_list() sekali sudah cukup untuk keduanya.

    Daftar izin KOSONG berarti boleh semua -- perilaku yang sudah
    berlaku, dan berbeda dari pengguna anonim yang tidak boleh apa pun.
    """
    u = getattr(request, "user", None)
    if not (u and u.is_authenticated):
        return qs.none()
    if u.is_superuser:
        return qs

    rel = getattr(u, "entitas_diizinkan", None)
    if rel is None:
        return qs.none()

    ids = list(rel.values_list("id", flat=True))
    if not ids:
        return qs
    return qs.filter(**{f"{field}_id__in": ids})


def _galat(e):
    isi = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


def _idem(request, prefix):
    """
    Kunci idempotency untuk transaksi uang.

    Kunci HARUS datang dari klien -- kunci yang diacak di server berubah
    tiap request, jadi retry apa pun lolos sebagai pembayaran kedua.
    Header absen tetap dilayani demi klien lama, tapi tanpa perlindungan.
    """
    return f'{prefix}:{request.headers.get("Idempotency-Key") or uuid.uuid4()}'


class BasisAkunting(viewsets.ModelViewSet):
    """
    Induk viewset akunting. Menyaring queryset menurut entitas yang boleh
    diakses pengguna.
    """

    def filter_entitas(self, qs):
        """
        Dipanggil turunan yang membangun querysetnya sendiri.

        Isinya didelegasikan ke batasi_entitas() supaya aturannya hanya
        ada di satu tempat -- dua salinan aturan akses akan berbeda cepat
        atau lambat, dan yang tertinggal biasanya yang lebih longgar.
        """
        return batasi_entitas(qs, self.request)

    def get_queryset(self):
        return self.filter_entitas(super().get_queryset())

class AkunViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'akunting'
    permission_classes = [AksesModul]
    queryset = Akun.objects.select_related('parent').order_by('kode')
    serializer_class = AkunSerializer
    filterset_fields = ['tipe', 'boleh_diposting', 'aktif']
    search_fields = ['kode', 'nama']



class JurnalUmumViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only. Jurnal hanya lahir dari posting(), tidak pernah diketik.
    Koreksi lewat aksi balik.
    """
    queryset = JurnalUmum.objects.none()

    modul = 'akunting'
    permission_classes = [AksesModul]
    serializer_class = JurnalUmumSerializer
    filterset_fields = ['entitas', 'kejadian', 'tanggal']
    search_fields = ['nomor', 'referensi', 'keterangan']

    def get_queryset(self):
        qs = (JurnalUmum.objects
              .select_related('entitas')
              .prefetch_related('baris__akun')
              .order_by('-tanggal', '-id'))
        return batasi_entitas(qs, self.request)

    @action(detail=True, methods=['post'],
            permission_classes=[PunyaRole.dengan(Role.SUPERVISOR)])
    def balik(self, request, pk=None):
        s = JurnalBalikSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            balik = services.jurnal_balik(
                jurnal_id=pk, tanggal=d['tanggal'], alasan=d['alasan'],
                user=request.user,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(JurnalUmumSerializer(balik).data,
                        status=status.HTTP_201_CREATED)



class PurchaseOrderFilter(django_filters.FilterSet):
    """
    FilterSet eksplisit.

    filterset_fields mengandalkan django_filters MENEBAK model dari
    queryset yang dikembalikan get_queryset(). Karena get_queryset() di
    sini menyaring per entitas dan bentuknya bisa berubah, penebakan itu
    gagal -- dan galatnya menyebut field yang sebenarnya ADA di model,
    sehingga menunjuk ke arah yang salah sama sekali.
    """
    class Meta:
        model = PurchaseOrder
        fields = ['entitas', 'suplier', 'status', 'tanggal']


class PurchaseOrderViewSet(BasisAkunting):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.none()
    filterset_class = PurchaseOrderFilter
    search_fields = ['no_po', 'suplier__nama']

    def get_queryset(self):
        # Bug salin-tempel: sebelumnya membangun queryset JurnalUmum di
        # dalam viewset PurchaseOrder. Endpoint tetap merespons dan
        # filter tetap terpasang, jadi galatnya muncul sebagai "field
        # suplier tidak ada" -- menunjuk ke serializer yang sebenarnya
        # sudah benar, dan menyembunyikan penyebab aslinya berjam-jam.
        qs = (PurchaseOrder.objects
              .select_related('entitas', 'suplier')
              .prefetch_related('item')
              .order_by('-tanggal', '-id'))
        return batasi_entitas(qs, self.request)

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer

    def create(self, request):
        s = BuatPOSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        ppn_persen = d.pop('ppn_persen', 0)

        if not request.user.bisa_akses_entitas(d['entitas_id']):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            with transaction.atomic():
                po = services.buat_po(user=request.user, **d)
                if ppn_persen:
                    po.ppn_persen = ppn_persen
                    po.save(update_fields=['ppn_persen'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Gunakan aksi ubah-item, kirim, atau batalkan.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'PO tidak dihapus. Gunakan aksi batalkan.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=['get'], url_path='preview-nomor')
    def preview_nomor(self, request):
        from core.models import Entitas
        from django.utils import timezone

        entitas_id = request.query_params.get('entitas')
        tanggal = request.query_params.get('tanggal')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'},
                            status=status.HTTP_400_BAD_REQUEST)
        entitas = Entitas.objects.get(pk=entitas_id)
        tgl = (timezone.datetime.fromisoformat(tanggal).date()
               if tanggal else timezone.localdate())
        return Response({'nomor': services.preview_nomor_po(entitas, tgl),
                         'catatan': 'Preview. Nomor final ditetapkan saat simpan.'})

    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """PO yang masih menunggu barang. Dasar laporan komitmen."""
        qs = self.filter_entitas(
            PurchaseOrder.objects.terbuka()
            .select_related('entitas', 'suplier').dengan_total()
            .order_by('tanggal')
        )
        return Response(PurchaseOrderListSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='ubah-item')
    def ubah_item(self, request, pk=None):
        s = UbahItemPOSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            po = services.ubah_item_po(po_id=pk, items=s.validated_data['items'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'])
    def kirim(self, request, pk=None):
        try:
            po = services.kirim_po(po_id=pk, user=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'])
    def batalkan(self, request, pk=None):
        s = BatalPOSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            po = services.batalkan_po(po_id=pk, user=request.user,
                                      alasan=s.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)
        
    @action(detail=True, methods=['post'])
    def setujui(self, request, pk=None):
        try:
            po = self.get_object()
            po = po.setujui()
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=True, methods=['post'])
    def tolak(self, request, pk=None):
        s = BatalPOSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            po = self.get_object()
            po = po.tolak(alasan=s.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['get'])
    def ringkasan(self, request, pk=None):
        return Response(services.ringkasan_po(pk))


class FakturPembelianViewSet(BasisAkunting):
    queryset = FakturPembelian.objects.none()
    serializer_class = FakturPembelianSerializer
    filterset_fields = ['entitas', 'suplier', 'status', 'jenis',
                        'tanggal_jatuh_tempo']
    search_fields = ['nomor_faktur', 'no_internal', 'suplier__nama']

    def get_queryset(self):
        qs = (FakturPembelian.objects
              .select_related('entitas', 'suplier', 'penerimaan')
              .prefetch_related('mutasi')
              .order_by('tanggal_jatuh_tempo', 'id'))
        return self.filter_entitas(qs)

    def get_serializer_class(self):
        if self.action == 'list':
            return FakturListSerializer
        return FakturPembelianSerializer

    def create(self, request):
        return Response(
            {'detail': 'Faktur barang diterbitkan lewat '
                       'POST faktur/dari-penerimaan/{id}/'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Faktur hanya berubah lewat terbitkan_faktur() dan '
                       'pembayaran, tidak lewat PUT/PATCH langsung.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Faktur tidak bisa dihapus.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'],
            url_path=r'draft-dari-penerimaan/(?P<penerimaan_id>\d+)')
    def draft_dari_penerimaan(self, request, penerimaan_id=None):
        """
        Angka usulan untuk mengisi form. Read-only, dan sudah basi begitu
        dibaca -- yang mengikat adalah perhitungan ulang saat penerbitan.
        """
        try:
            return Response(services.draft_faktur(penerimaan_id))
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=False, methods=['post'],
            url_path=r'dari-penerimaan/(?P<penerimaan_id>\d+)')
    def dari_penerimaan(self, request, penerimaan_id=None):
        s = TerbitkanFakturSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        if d.get('abaikan_klaim_terbuka') and not request.user.supervisor:
            return Response(
                {'detail': 'Hanya Supervisor yang boleh mengabaikan klaim terbuka.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            faktur, rincian = services.terbitkan_faktur(
                penerimaan_id=penerimaan_id, user=request.user, **d,
            )
        except DjangoValidationError as e:
            return _galat(e)

        return Response(
            {'faktur': FakturPembelianSerializer(faktur).data,
             'rincian': rincian},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], url_path='jatuh-tempo')
    def jatuh_tempo(self, request):
        from django.utils import timezone

        entitas_id = request.query_params.get('entitas')
        sampai = request.query_params.get('sampai')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'},
                            status=status.HTTP_400_BAD_REQUEST)
        tgl = (timezone.datetime.fromisoformat(sampai).date()
               if sampai else timezone.localdate())
        qs = services.faktur_jatuh_tempo(entitas_id, tgl)
        return Response(FakturListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def aging(self, request):
        entitas_id = request.query_params.get('entitas')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(services.aging_hutang(entitas_id))


class PembayaranView(viewsets.ViewSet):
    """
    Alokasi pembayaran ke faktur terbuka, FIFO berdasarkan jatuh tempo.

    Peran KEUANGAN yang boleh, bukan AKUNTING -- pemisahan tugas.
    """

    modul = 'keuangan'
    permission_classes = [AksesModul]

    def create(self, request):
        s = BayarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if not request.user.bisa_akses_entitas(d['entitas_id']):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            alokasi, uang_muka = services.alokasi_pembayaran(
                user=request.user, idem_key=_idem(request, 'bayar'), **d,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(
            {'alokasi': alokasi,
             'uang_muka': UangMukaSerializer(uang_muka).data if uang_muka else None},
            status=status.HTTP_201_CREATED,
        )


class UangMukaViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'keuangan'
    permission_classes = [AksesModul]
    queryset = (UangMukaSuplier.objects
                .select_related('entitas', 'suplier').order_by('-tanggal'))
    serializer_class = UangMukaSerializer
    filterset_fields = ['entitas', 'suplier']


class FakturPenjualanViewSet(BasisAkunting):
    serializer_class = FakturPenjualanSerializer
    queryset = FakturPenjualan.objects.none()
    filterset_fields = ['entitas', 'pelanggan', 'status', 'tanggal_jatuh_tempo']
    search_fields = ['nomor_faktur', 'no_internal', 'pelanggan__nama']

    def get_queryset(self):
        qs = (FakturPenjualan.objects
              .select_related('entitas', 'pelanggan')
              .order_by('tanggal_jatuh_tempo', 'id'))
        return self.filter_entitas(qs)

    def create(self, request):
        return Response(
            {'detail': 'Faktur penjualan diterbitkan lewat POST faktur-jual/dari-do/{id}/'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Faktur hanya berubah lewat terbitkan_faktur_jual() dan penerimaan pembayaran.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Faktur penjualan tidak bisa dihapus.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['post'], url_path=r'dari-do/(?P<delivery_order_id>\d+)')
    def dari_do(self, request, delivery_order_id=None):
        s = TerbitkanFakturJualSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        try:
            faktur = services.terbitkan_faktur_jual(
                delivery_order_id=delivery_order_id,
                user=request.user,
                **d
            )
        except DjangoValidationError as e:
            return _galat(e)

        return Response(
            FakturPenjualanSerializer(faktur).data,
            status=status.HTTP_201_CREATED,
        )



class PenerimaanPiutangView(viewsets.ViewSet):
    """
    Penerimaan pembayaran dari pelanggan untuk memotong sisa piutang.
    Modul KEUANGAN yang memproses ini, mirip dengan alur AP.
    """
    modul = 'keuangan'
    permission_classes = [AksesModul]

    def create(self, request):
        s = TerimaPiutangSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        entitas_id = (FakturPenjualan.objects
                      .filter(pk=d['faktur_id'])
                      .values_list('entitas_id', flat=True)
                      .first())
        if entitas_id is None:
            return Response({'detail': 'Faktur penjualan tidak ditemukan.'},
                            status=status.HTTP_404_NOT_FOUND)
        if not request.user.bisa_akses_entitas(entitas_id):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            mutasi = services.terima_pembayaran_piutang(
                user=request.user,
                idem_key=_idem(request, 'terima_piutang'),
                **d
            )
        except DjangoValidationError as e:
            return _galat(e)

        return Response(
            {
                'detail': 'Pembayaran piutang berhasil dicatat.', 
                'mutasi_id': mutasi.id
            },
            status=status.HTTP_201_CREATED,
        )
class PengeluaranKasViewSet(viewsets.ModelViewSet):
    queryset = PengeluaranKas.objects.select_related(
        'entitas', 'kategori_beban', 'sumber_dana'
    ).order_by('-tanggal', '-id')
    
    serializer_class = PengeluaranKasSerializer
    filterset_fields = ['entitas', 'status']

    def perform_create(self, serializer):
        serializer.save(dibuat_oleh=self.request.user)

    @action(detail=True, methods=['post'])
    def posting(self, request, pk=None):
        """
        Endpoint khusus untuk menyetujui pengeluaran dan otomatis mencetak Jurnal.
        URL: POST /api/v1/akunting/pengeluaran-kas/{id}/posting/
        """
        pengeluaran = self.get_object()
        try:
            pengeluaran.posting(user=request.user)
            return Response({'status': 'Pengeluaran berhasil diposting dan jurnal tercetak.'})
        except DjangoValidationError as e:
            return Response({'detail': e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)