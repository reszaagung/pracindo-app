import uuid
import os
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

import django_filters
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from docxtpl import DocxTemplate

from staff_user.models import Role
from staff_user.permissions import AksesModul, PunyaRole

from . import services
from .models import (
    Akun, FakturPembelian, FakturPenjualan, JurnalUmum, PurchaseOrder,
    PurchaseOrderItem, UangMukaSuplier, PembelianKemasan
)
from .models.pengeluaran import PengeluaranKas
from .serializers import (
    AkunSerializer, BatalPOSerializer, BayarSerializer,
    FakturListSerializer, FakturPembelianSerializer, FakturPenjualanSerializer,
    JurnalBalikSerializer, JurnalUmumSerializer,
    PurchaseOrderListSerializer, PurchaseOrderSerializer,
    TerbitkanFakturJualSerializer, TerbitkanFakturSerializer,
    TerimaPiutangSerializer, UangMukaSerializer, UbahItemPOSerializer,
    BuatPOSerializer, PurchaseOrderKemasanSerializer, PengeluaranKasSerializer
)


_NAMA_BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def _format_tanggal_id(tgl):
    if not tgl:
        return "-"
    return f"{tgl.day:02d} {_NAMA_BULAN_ID[tgl.month]} {tgl.year}"


def batasi_entitas(qs, request, field="entitas"):
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
        # User tidak punya entitas yang diizinkan -> jangan tampilkan apa pun.
        # (Sebelumnya `return qs` di sini, artinya staff yang belum di-assign
        # entitas apa pun malah melihat SEMUA entitas. Konfirmasi ulang ya.)
        return qs.none()
    return qs.filter(**{f"{field}_id__in": ids})


def _galat(e):
    isi = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(isi, status=status.HTTP_400_BAD_REQUEST)


def _idem(request, prefix):
    return f'{prefix}:{request.headers.get("Idempotency-Key") or uuid.uuid4()}'


class BasisAkunting(viewsets.ModelViewSet):
    modul = 'akunting'
    permission_classes = [AksesModul]

    def filter_entitas(self, qs):
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

    @action(detail=True, methods=['post'], permission_classes=[PunyaRole.dengan(Role.SUPERVISOR)])
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
        return Response(JurnalUmumSerializer(balik).data, status=status.HTTP_201_CREATED)


class PurchaseOrderFilter(django_filters.FilterSet):
    class Meta:
        model = PurchaseOrder
        fields = ['entitas', 'suplier', 'status', 'tanggal']


class PurchaseOrderViewSet(BasisAkunting):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.none()
    filterset_class = PurchaseOrderFilter
    search_fields = ['no_po', 'suplier__nama']

    def get_queryset(self):
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
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)

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

        entitas_id = request.query_params.get('entitas')
        tanggal = request.query_params.get('tanggal')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.bisa_akses_entitas(entitas_id):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            entitas = Entitas.objects.get(pk=entitas_id)
        except Entitas.DoesNotExist:
            return Response({'detail': 'Entitas tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)

        tgl = (timezone.datetime.fromisoformat(tanggal).date() if tanggal else timezone.localdate())
        return Response({'nomor': services.preview_nomor_po(entitas, tgl),
                         'catatan': 'Preview. Nomor final ditetapkan saat simpan.'})

    @action(detail=False, methods=['get'])
    def outstanding(self, request):
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
    def ajukan(self, request, pk=None):
        try:
            po = services.ajukan_po(po_id=pk, user=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'])
    def setujui(self, request, pk=None):
        try:
            po = services.setujui_po(po_id=pk, user=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'])
    def tolak(self, request, pk=None):
        s = BatalPOSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            po = services.tolak_po(
                po_id=pk,
                user=request.user,
                alasan=s.validated_data['alasan']
            )
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
            po = services.batalkan_po(
                po_id=pk,
                user=request.user,
                alasan=s.validated_data['alasan']
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'], url_path='tutup-sesi')
    def tutup_sesi(self, request, pk=None):
        try:
            po = services.tutup_paksa_po(po_id=pk, user=request.user)
            return Response(PurchaseOrderSerializer(po).data)
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=True, methods=['get'])
    def ringkasan(self, request, pk=None):
        return Response(services.ringkasan_po(pk))

    @action(detail=True, methods=["get"], url_path="cetak")
    def cetak(self, request, pk=None):
        po = self.get_object()  # 404/403 ditangani otomatis oleh DRF

        try:
            items_data = []
            total_subtotal = Decimal("0")

            for barang in po.item.all():
                is_produk = bool(getattr(barang, "produk", None))
                is_kemasan = bool(getattr(barang, "kemasan", None))

                if is_produk:
                    nama_produk = barang.produk.nama
                elif is_kemasan:
                    nama_produk = barang.kemasan.nama
                else:
                    nama_produk = "-"

                qty = Decimal(str(barang.qty_pesan or 0))

                if is_produk:
                    harga = Decimal(str(barang.harga_per_kg or 0))
                else:
                    harga = Decimal(str(getattr(barang, "harga_per_pcs", 0) or 0))

                subtotal = qty * harga
                total_subtotal += subtotal

                items_data.append({
                    "nama_item": nama_produk,
                    "kuantitas": f"{qty:g}",
                    "total_harga": f"Rp {subtotal:,.0f}".replace(",", "."),
                })

            persen = Decimal(str(po.ppn_persen or 0))
            ppn_nominal = total_subtotal * persen / Decimal("100")
            grand_total = total_subtotal + ppn_nominal

            context = {
                "NAMA_PIC": po.entitas.nama if po.entitas else "Pracindo Staff",
                "NAMA_SUPPLIER": po.suplier.nama if po.suplier else "-",
                "NO_PO": po.no_po,
                "TANGGAL_BUAT": _format_tanggal_id(po.tanggal),
                "TOTAL_SUBTOTAL": f"Rp {total_subtotal:,.0f}".replace(",", "."),
                "TOTAL_PPN": f"Rp {ppn_nominal:,.0f}".replace(",", "."),
                "TOTAL_FINAL": f"Rp {grand_total:,.0f}".replace(",", "."),
                "items": items_data,
            }

            template_path = os.path.join(
                settings.BASE_DIR, "akunting", "templates_dokumen", "master_doc_po.docx",
            )
            if not os.path.exists(template_path):
                return Response(
                    {"detail": f"File template tidak ditemukan di {template_path}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            doc = DocxTemplate(template_path)
            doc.render(context)

            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            safe_filename = po.no_po.replace("/", "_").replace(" ", "_")
            response["Content-Disposition"] = f'attachment; filename="PO_{safe_filename}.docx"'
            doc.save(response)
            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": f"Gagal mencetak dokumen: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FakturPembelianViewSet(BasisAkunting):
    queryset = FakturPembelian.objects.none()
    serializer_class = FakturPembelianSerializer
    filterset_fields = ['entitas', 'suplier', 'status', 'jenis', 'tanggal_jatuh_tempo']
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
            {'detail': 'Faktur barang diterbitkan lewat POST faktur/dari-penerimaan/{id}/'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Faktur hanya berubah lewat terbitkan_faktur() dan pembayaran, tidak lewat PUT/PATCH langsung.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Faktur tidak bisa dihapus.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'], url_path=r'draft-dari-penerimaan/(?P<penerimaan_id>\d+)')
    def draft_dari_penerimaan(self, request, penerimaan_id=None):
        try:
            return Response(services.draft_faktur(penerimaan_id))
        except DjangoValidationError as e:
            return _galat(e)

    @action(detail=False, methods=['post'], url_path=r'dari-penerimaan/(?P<penerimaan_id>\d+)')
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
            {'faktur': FakturPembelianSerializer(faktur).data, 'rincian': rincian},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], url_path='jatuh-tempo')
    def jatuh_tempo(self, request):
        entitas_id = request.query_params.get('entitas')
        sampai = request.query_params.get('sampai')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.bisa_akses_entitas(entitas_id):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)
        tgl = (timezone.datetime.fromisoformat(sampai).date() if sampai else timezone.localdate())
        qs = services.faktur_jatuh_tempo(entitas_id, tgl)
        return Response(FakturListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def aging(self, request):
        entitas_id = request.query_params.get('entitas')
        if not entitas_id:
            return Response({'detail': 'Parameter entitas wajib.'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.bisa_akses_entitas(entitas_id):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'},
                            status=status.HTTP_403_FORBIDDEN)
        return Response(services.aging_hutang(entitas_id))


class PembayaranView(viewsets.ViewSet):
    modul = 'keuangan'
    permission_classes = [AksesModul]

    def create(self, request):
        s = BayarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if not request.user.bisa_akses_entitas(d['entitas_id']):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            alokasi, uang_muka = services.alokasi_pembayaran(
                user=request.user, idem_key=_idem(request, 'bayar'), **d,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(
            {
                'alokasi': alokasi,
                'uang_muka': UangMukaSerializer(uang_muka).data if uang_muka else None
            },
            status=status.HTTP_201_CREATED,
        )


class UangMukaViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'keuangan'
    permission_classes = [AksesModul]
    queryset = (UangMukaSuplier.objects.select_related('entitas', 'suplier').order_by('-tanggal'))
    serializer_class = UangMukaSerializer
    filterset_fields = ['entitas', 'suplier']

    def get_queryset(self):
        return batasi_entitas(super().get_queryset(), self.request)


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
        return Response({'detail': 'Faktur penjualan tidak bisa dihapus.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

        return Response(FakturPenjualanSerializer(faktur).data, status=status.HTTP_201_CREATED)


class PenerimaanPiutangView(viewsets.ViewSet):
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
            return Response({'detail': 'Faktur penjualan tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)
        if not request.user.bisa_akses_entitas(entitas_id):
            return Response({'detail': 'Anda tidak punya akses ke entitas ini.'}, status=status.HTTP_403_FORBIDDEN)

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


class PengeluaranKasViewSet(BasisAkunting):
    modul = 'keuangan'
    queryset = PengeluaranKas.objects.select_related('entitas', 'kategori_beban', 'sumber_dana').order_by('-tanggal', '-id')
    serializer_class = PengeluaranKasSerializer
    filterset_fields = ['entitas', 'status']

    def perform_create(self, serializer):
        serializer.save(dibuat_oleh=self.request.user)

    @action(detail=True, methods=['post'])
    def posting(self, request, pk=None):
        pengeluaran = self.get_object()
        try:
            pengeluaran.posting(user=request.user)
            return Response({'status': 'Pengeluaran berhasil diposting dan jurnal tercetak.'})
        except DjangoValidationError as e:
            return Response({'detail': e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderKemasanViewSet(BasisAkunting):
    # Asumsi: PembelianKemasan punya field `entitas` seperti model lain di modul ini.
    # Kalau nama field-nya beda/gak ada, sesuaikan `field=` di batasi_entitas
    # atau override get_queryset() di sini secara manual.
    queryset = PembelianKemasan.objects.all().order_by('-tanggal', '-id')
    serializer_class = PurchaseOrderKemasanSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Purchase Order Kemasan berhasil dibuat.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(dibuat_oleh=self.request.user)