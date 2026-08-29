"""
Endpoint master data — master/views.py
"""
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from staff_user.permissions import HanyaAdmin, SudahLogin, AdminAtauAkunting
from rest_framework.permissions import AllowAny
from .models import Pelanggan, Produk, Satuan, Suplier ,MasterProduk
from .serializers import (
    PelangganSerializer, ProdukRingkasSerializer,
    ProdukSerializer, SatuanSerializer, SuplierRingkasSerializer,
    SuplierSerializer,MasterProdukSerializer,
)

class BasisMaster(viewsets.ModelViewSet):
    modul = 'master'

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [SudahLogin()]
        return [HanyaAdmin()]

    def perform_destroy(self, instance):
        raise DRFValidationError(
            'Master data tidak dihapus -- transaksi lama merujuk ke sini. '
            'Set aktif=False.'
        )

class SatuanViewSet(BasisMaster):
    queryset = Satuan.objects.all()
    serializer_class = SatuanSerializer
    search_fields = ['kode', 'nama']

class ProdukViewSet(BasisMaster):
    queryset = Produk.objects.select_related('satuan').prefetch_related('suplier').order_by('kode')
    
    # Filter 'suplier' ditambahkan untuk fitur Katalog Suplier
    filterset_fields = ['jenis', 'aktif', 'suplier']
    search_fields = ['kode', 'nama']

    def get_serializer_class(self):
        if self.request.query_params.get('ringkas'):
            return ProdukRingkasSerializer
        return ProdukSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [SudahLogin()]
        return [AdminAtauAkunting()]

class SuplierViewSet(BasisMaster):
    queryset = Suplier.objects.order_by('nama')
    filterset_fields = ['aktif']
    search_fields = ['kode', 'nama', 'npwp', 'kontak_nama']

    def get_serializer_class(self):
        if self.request.query_params.get('ringkas'):
            return SuplierRingkasSerializer
        return SuplierSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [SudahLogin()]
        return [AdminAtauAkunting()]

class PelangganViewSet(BasisMaster):
    queryset = Pelanggan.objects.order_by('nama')
    filterset_fields = ['aktif']
    search_fields = ['kode', 'nama', 'npwp']
    serializer_class = PelangganSerializer

class PelangganViewSet(BasisMaster):
    """
    Master pelanggan. Dipakai selector di form Sales Order.

    `aktif` disaring lewat query param, bukan otomatis -- daftar master
    tetap harus bisa menampilkan yang nonaktif untuk diaktifkan kembali.
    Yang menyaring adalah pemanggil: form SO mengirim ?aktif=true.
    """
    queryset = Pelanggan.objects.all().order_by('nama')
    serializer_class = PelangganSerializer
    filterset_fields = ['aktif']
    search_fields = ['kode', 'nama', 'kontak_nama']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('aktif') in ('true', '1', 'True'):
            qs = qs.filter(aktif=True)
        return qs


class MasterProdukViewSet(viewsets.ModelViewSet):
    queryset = MasterProduk.objects.all()
    serializer_class = MasterProdukSerializer
    permission_classes = [AllowAny]
    search_fields = ['id', 'nama_item']
    ordering_fields = ['nama_item', 'id']
