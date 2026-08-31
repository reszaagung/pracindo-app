from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AkunViewSet, 
    FakturPembelianViewSet, 
    JurnalUmumViewSet,
    PembayaranView, 
    PurchaseOrderViewSet, 
    UangMukaViewSet,
    FakturPenjualanViewSet, 
    PenerimaanPiutangView,
    PengeluaranKasViewSet,
    PurchaseOrderKemasanViewSet
)

app_name = 'akunting'

router = DefaultRouter()

router.register('akun', AkunViewSet, basename='akun')
router.register('jurnal', JurnalUmumViewSet, basename='jurnal')
router.register('purchase-order', PurchaseOrderViewSet, basename='purchase-order')
router.register('po-kemasan', PurchaseOrderKemasanViewSet, basename='po-kemasan')
router.register('faktur', FakturPembelianViewSet, basename='faktur')
router.register('pembayaran', PembayaranView, basename='pembayaran')
router.register('uang-muka', UangMukaViewSet, basename='uang-muka')
router.register('faktur-jual', FakturPenjualanViewSet, basename='faktur-jual')
router.register('terima-piutang', PenerimaanPiutangView, basename='terima-piutang')
router.register('pengeluaran-kas', PengeluaranKasViewSet, basename='pengeluaran-kas')

urlpatterns = [
    path('', include(router.urls)),
]