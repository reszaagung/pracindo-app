"""
Rute Papan Tugas — work_order/urls.py

Router didaftarkan dengan prefiks kosong: app ini dipasang di `work-order/`
dan satu-satunya resource-nya adalah Work Order itu sendiri.

DefaultRouter menempatkan rute list dan aksi-list (mading/, staff/) SEBELUM
rute detail, jadi keduanya tidak tertangkap sebagai pk berupa teks. Kalau
nanti ada resource kedua di app ini, prefiks kosong harus diganti lebih dulu.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'work_order'

router = DefaultRouter()
router.register('', views.WorkOrderViewSet, basename='workorder')

urlpatterns = [
    path('', include(router.urls)),
]
