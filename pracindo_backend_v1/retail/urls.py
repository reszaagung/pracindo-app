from django.urls import path
from .views import (
    KatalogPOSAPIView, CheckoutPOSAPIView, 
    RiwayatTransaksiAPIView, SesiKasirAPIView,
    AkunBukuBesarAPIView, JurnalUmumAPIView
)

app_name = 'retail'

urlpatterns = [
    path('pos/katalog/', KatalogPOSAPIView.as_view(), name='pos-katalog'),
    path('pos/checkout/', CheckoutPOSAPIView.as_view(), name='pos-checkout'),
    path('riwayat/', RiwayatTransaksiAPIView.as_view(), name='riwayat'),
    path('sesi/', SesiKasirAPIView.as_view(), name='sesi'),
    
    path('akuntansi/akun/', AkunBukuBesarAPIView.as_view(), name='akun-buku-besar'),
    path('akuntansi/jurnal/', JurnalUmumAPIView.as_view(), name='jurnal-umum'),
]