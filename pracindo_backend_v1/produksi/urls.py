from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BatchViewSet

app_name = 'produksi'

router = DefaultRouter()
router.register('batch', BatchViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
]