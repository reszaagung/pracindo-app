from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import EntitasViewSet, GrupBahanViewSet, PeriodeAkuntansiViewSet

app_name = 'core'

router = DefaultRouter()
router.register(r'entitas', EntitasViewSet, basename='entitas')
router.register(r'grup-bahan', GrupBahanViewSet, basename='grup-bahan')

router.register(r'periode', PeriodeAkuntansiViewSet, basename='periode')

urlpatterns = [
    path('', include(router.urls)),
]