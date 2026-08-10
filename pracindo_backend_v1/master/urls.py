from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProdukViewSet, SuplierViewSet, SatuanViewSet

app_name = 'master'

router = DefaultRouter()

router.register('produk', ProdukViewSet, basename='produk')
router.register('suplier', SuplierViewSet, basename='suplier')
router.register('satuan', SatuanViewSet, basename='satuan')

urlpatterns = [
    path('', include(router.urls)),
]