"""
Rute logistik — logistik/urls.py

Endpoint level-app didaftarkan SEBELUM router. Kalau di belakang,
DefaultRouter menangkapnya sebagai rute detail dengan pk berupa teks, lalu
filter(pk='...') melempar ValueError dan menghasilkan 500, bukan 404.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DistribusiTersediaView, KendaraanViewSet, PengirimanViewSet, ReturViewSet,
)

app_name = 'logistik'

router = DefaultRouter()
router.register(r'pengiriman', PengirimanViewSet, basename='pengiriman')
router.register(r'retur', ReturViewSet, basename='retur')
router.register(r'kendaraan', KendaraanViewSet, basename='kendaraan')

urlpatterns = [
    path('distribusi-tersedia/', DistribusiTersediaView.as_view(),
         name='distribusi-tersedia'),
    path('', include(router.urls)),
]
