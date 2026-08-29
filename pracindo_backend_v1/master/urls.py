from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PelangganViewSet, ProdukViewSet, SatuanViewSet, SuplierViewSet,MasterProdukViewSet
)

app_name = 'master'

router = DefaultRouter()
router.register('master-produk', MasterProdukViewSet, basename='master-produk')
router.register('produk', ProdukViewSet, basename='produk')
router.register('suplier', SuplierViewSet, basename='suplier')
router.register('satuan', SatuanViewSet, basename='satuan')
router.register('pelanggan', PelangganViewSet, basename='pelanggan')
urlpatterns = [
    path('', include(router.urls)),
]