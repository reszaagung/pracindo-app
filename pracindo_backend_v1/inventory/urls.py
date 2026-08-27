from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "inventory"

router = DefaultRouter()
router.register("kemasan", views.KemasanViewSet, basename="kemasan")
router.register("pembelian", views.PembelianViewSet, basename="pembelian")
router.register("packing", views.PackingViewSet, basename="packing")

urlpatterns = [
    path("entitas/", views.entitas_list, name="entitas"),
    path("produk/", views.produk_list, name="produk"),
    path("stok/", views.stok_list, name="stok"),
    
    # Path pool_list disesuaikan dari views.py terbaru
    path("pool/", views.pool_list, name="pool"),
    path("pool/kemasan/", views.pool_kemasan_list, name="pool-kemasan"),
    path("pool/<int:produk_id>/kartu/", views.pool_kartu_stok, name="pool-kartu"),
    
    path("mutasi/", views.mutasi_list, name="mutasi"),
    path("mutasi/rekap/", views.mutasi_rekap, name="mutasi-rekap"),
    path("pemeriksaan/", views.pemeriksaan_invarian, name="pemeriksaan"),
    path("barang-jadi/", views.barang_jadi, name="barang-jadi"),
    path("", include(router.urls)),
]