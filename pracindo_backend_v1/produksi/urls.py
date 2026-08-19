from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BatchViewSet, TangkiViewSet, pratinjau_batch

app_name = 'produksi'

router = DefaultRouter()
router.register('batch', BatchViewSet, basename='batch')
router.register('tangki', TangkiViewSet, basename='tangki')

urlpatterns = [
    path('', include(router.urls)),
    path('pratinjau/', pratinjau_batch, name='pratinjau_batch'),
]