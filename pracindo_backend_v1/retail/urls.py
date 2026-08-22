from django.urls import path
from .views import (
    KatalogPOSAPIView, CheckoutPOSAPIView, RiwayatTransaksiAPIView, SesiKasirAPIView,
    PelangganRetailAPIView, SalesRetailAPIView,
    AkunBukuBesarAPIView, JurnalUmumAPIView, BukuBesarMutasiAPIView,
    DaftarSuratJalanAPIView, ProsesPenerimaanAPIView,
    DaftarPiutangAPIView, BayarPiutangAPIView
)

urlpatterns = [
    path('pos/katalog/', KatalogPOSAPIView.as_view(), name='pos-katalog'),
    path('pos/checkout/', CheckoutPOSAPIView.as_view(), name='pos-checkout'),
    path('riwayat/', RiwayatTransaksiAPIView.as_view(), name='pos-riwayat'),
    path('sesi/', SesiKasirAPIView.as_view(), name='pos-sesi'),
    path('pelanggan/', PelangganRetailAPIView.as_view(), name='retail-pelanggan'),
    path('sales/', SalesRetailAPIView.as_view(), name='retail-sales'),
    path('penerimaan/', DaftarSuratJalanAPIView.as_view(), name='retail-penerimaan-list'),
    path('penerimaan/<int:pk>/proses/', ProsesPenerimaanAPIView.as_view(), name='retail-penerimaan-proses'),
    path('akuntansi/akun/', AkunBukuBesarAPIView.as_view(), name='akuntansi-akun'),
    path('akuntansi/akun/<int:pk>/mutasi/', BukuBesarMutasiAPIView.as_view(), name='akuntansi-akun-mutasi'),
    path('akuntansi/jurnal/', JurnalUmumAPIView.as_view(), name='akuntansi-jurnal'),
    path('piutang/', DaftarPiutangAPIView.as_view(), name='retail-piutang'),
    path('piutang/<int:pk>/bayar/', BayarPiutangAPIView.as_view(), name='retail-bayar-piutang'),
]