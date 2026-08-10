from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IsiPoolView, KlaimHasilView, MutasiStokViewSet, NilaiEkuivalenViewSet,
    OpnameView, PosisiKlaimViewSet, SetorKePoolView, StokViewSet,
    TangkiViewSet, VerifikasiView,
)

app_name = 'inventory'

router = DefaultRouter()
router.register('stok', StokViewSet, basename='stok')
router.register('tangki', TangkiViewSet, basename='tangki')
router.register('mutasi', MutasiStokViewSet, basename='mutasi')
router.register('posisi-klaim', PosisiKlaimViewSet, basename='posisi-klaim')
router.register('nilai-ekuivalen', NilaiEkuivalenViewSet,
                basename='nilai-ekuivalen')

urlpatterns = [
    path('isi-pool/', IsiPoolView.as_view(), name='isi-pool'),
    path('setor-ke-pool/', SetorKePoolView.as_view(), name='setor-ke-pool'),
    path('klaim-hasil/', KlaimHasilView.as_view(), name='klaim-hasil'),
    path('opname/', OpnameView.as_view(), name='opname'),
    path('verifikasi/', VerifikasiView.as_view(), name='verifikasi'),
    path('', include(router.urls)),
]
