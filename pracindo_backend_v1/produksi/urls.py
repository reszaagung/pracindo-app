from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SesiViewSet

app_name = 'produksi'

router = DefaultRouter()
router.register(r'sesi', SesiViewSet, basename='sesi')

urlpatterns = [
    path('', include(router.urls)),
]