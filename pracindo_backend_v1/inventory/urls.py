from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IsiPoolView, IsiTangkiView, KemasanViewSet, KlaimHasilView,
    KlaimKemasanView, LunasView, LuruskanView, MutasiStokViewSet,
    NilaiEkuivalenViewSet, OpnameView, PosisiKlaimViewSet,
    RencanaKemasanView, SetorKePoolView, StokViewSet, TangkiViewSet,
    VerifikasiView,
)

app_name = 'inventory'

router = DefaultRouter()
router.register('stok', StokViewSet, basename='stok')
router.register('tangki', TangkiViewSet, basename='tangki')
router.register('kemasan', KemasanViewSet, basename='kemasan')
router.register('mutasi', MutasiStokViewSet, basename='mutasi')
router.register('posisi-klaim', PosisiKlaimViewSet, basename='posisi-klaim')
router.register('nilai-ekuivalen', NilaiEkuivalenViewSet,
                basename='nilai-ekuivalen')

urlpatterns = [
    path('isi-pool/', IsiPoolView.as_view(), name='isi-pool'),
    path('tangki/<int:pk>/isi/', IsiTangkiView.as_view(), name='isi-tangki'),
    path('rencana-kemasan/', RencanaKemasanView.as_view(),
         name='rencana-kemasan'),
    path('setor-ke-pool/', SetorKePoolView.as_view(), name='setor-ke-pool'),
    path('klaim-hasil/', KlaimHasilView.as_view(), name='klaim-hasil'),
    path('klaim-kemasan/', KlaimKemasanView.as_view(), name='klaim-kemasan'),
    path('opname/', OpnameView.as_view(), name='opname'),
    path('lunas/', LunasView.as_view(), name='lunas'),
    path('luruskan/', LuruskanView.as_view(), name='luruskan'),
    path('verifikasi/', VerifikasiView.as_view(), name='verifikasi'),
    path('', include(router.urls)),
]
