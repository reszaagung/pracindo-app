from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    LaporanSelisihViewSet, 
    PenerimaanViewSet,
    POSiapTerimaViewSet,
)

app_name = 'warehouse'

router = DefaultRouter()
router.register('po-siap-terima', POSiapTerimaViewSet, basename='po-siap-terima')
router.register('penerimaan', PenerimaanViewSet, basename='penerimaan')
router.register('laporan-selisih', LaporanSelisihViewSet, basename='laporan-selisih')

urlpatterns = [
    path('', include(router.urls)),
]