from django.urls import path
from .views import (
    KatalogPOSAPIView, CheckoutPOSAPIView, RiwayatTransaksiAPIView,
    SesiKasirAPIView, AkunBukuBesarAPIView, JurnalUmumAPIView,
    PelangganRetailAPIView, SalesRetailAPIView
)

urlpatterns = [
    # POS Kasir
    path('pos/katalog/', KatalogPOSAPIView.as_view(), name='pos-katalog'),
    path('pos/checkout/', CheckoutPOSAPIView.as_view(), name='pos-checkout'),
    path('riwayat/', RiwayatTransaksiAPIView.as_view(), name='pos-riwayat'),
    path('sesi/', SesiKasirAPIView.as_view(), name='pos-sesi'),
    
    # Master Data Retail
    path('pelanggan/', PelangganRetailAPIView.as_view(), name='retail-pelanggan'),
    path('sales/', SalesRetailAPIView.as_view(), name='retail-sales'),

    # Akuntansi
    path('akuntansi/akun/', AkunBukuBesarAPIView.as_view(), name='akuntansi-akun'),
    path('akuntansi/jurnal/', JurnalUmumAPIView.as_view(), name='akuntansi-jurnal'),
]