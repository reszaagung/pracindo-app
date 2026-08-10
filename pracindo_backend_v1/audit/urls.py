from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JejakAktivitasViewSet

app_name = 'audit'

router = DefaultRouter()
router.register('jejak', JejakAktivitasViewSet, basename='jejak')

urlpatterns = [path('', include(router.urls))]
