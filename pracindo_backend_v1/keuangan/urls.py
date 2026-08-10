from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PengeluaranViewSet

app_name = 'keuangan'

router = DefaultRouter()
router.register(r'pengeluaran', PengeluaranViewSet, basename='pengeluaran')

urlpatterns = [
    path('', include(router.urls)),
]