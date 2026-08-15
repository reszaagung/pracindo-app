"""
Rute Inventory — inventory/urls.py

ENTITAS DAN PRODUK HANYA DIBACA DI SINI

    CRUD-nya milik app core dan master. Endpoint di bawah cuma memberi
    daftar untuk selector -- dua pintu tulis untuk satu master berarti
    dua tempat yang bisa lupa aturan yang dipegang yang lain.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "inventory"

router = DefaultRouter()
router.register("kemasan", views.KemasanViewSet, basename="kemasan")
router.register("pembelian", views.PembelianViewSet, basename="pembelian")
router.register("packing", views.PackingViewSet, basename="packing")

urlpatterns = [
    # Rute spesifik SEBELUM router. DefaultRouter memasang pola
    # tangkap-semua untuk detail; 'mutasi/rekap/' bisa tertelan sebagai
    # 'mutasi/{pk}/' kalau urutannya terbalik.
    path("entitas/", views.entitas_list, name="entitas"),
    path("produk/", views.produk_list, name="produk"),
    path("stok/", views.stok_list, name="stok"),
    path("pool/", views.pool_list, name="pool"),
    path("pool/<int:produk_id>/kartu/", views.pool_kartu_stok, name="pool-kartu"),
    path("mutasi/", views.mutasi_list, name="mutasi"),
    path("mutasi/rekap/", views.mutasi_rekap, name="mutasi-rekap"),
    path("pemeriksaan/", views.pemeriksaan_invarian, name="pemeriksaan"),
    path("barang-jadi/", views.barang_jadi, name="barang-jadi"),
    path("", include(router.urls)),
]
