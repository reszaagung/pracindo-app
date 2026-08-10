from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import LampiranViewSet

app_name = 'dokumen'

router = DefaultRouter()
# Mendaftarkan basename 'lampiran' agar sesuai dengan 'dokumen:lampiran-list' di tests.py
router.register('lampiran', LampiranViewSet, basename='lampiran')

urlpatterns = [
    path('', include(router.urls)),
]