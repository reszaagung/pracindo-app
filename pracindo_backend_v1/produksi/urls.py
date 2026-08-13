"""
Rute produksi — produksi/urls.py

Dipasang di pracindo_erp/urls.py sebagai:

    path('api/v1/produksi/', include('produksi.urls')),

PETA RUTE

    resep/                              GET     daftar resep aktif
    jenis-pengukuran/                   GET     master jenis pengukuran
    kapasitas/                          GET     ?grup=&produk=&tanggal=
    alokasi/                            GET     ?grup=&bahan=&qty=

    sesi/                               GET     daftar sesi
                                        POST    buat sesi rutin (berbasis resep)
    sesi/rnd/                           POST    buat sesi eksperimen
    sesi/banding/                       GET     ?ids=1,2,3  (maks 8)
    sesi/{id}/                          GET     ringkasan sesi
    sesi/{id}/rencana/                  GET     baris rencana per tangki
    sesi/{id}/mulai/                    POST    DRAFT    -> BERJALAN
    sesi/{id}/selesaikan/               POST    BERJALAN -> SELESAI
    sesi/{id}/gagalkan/                 POST    BERJALAN -> GAGAL
    sesi/{id}/batalkan/                 POST    DRAFT    -> BATAL
    sesi/{id}/pengukuran/               GET/POST
    sesi/{id}/catatan/                  GET/POST
    sesi/{id}/pratinjau-kerugian/       GET     akunting atau supervisor

PUT, PATCH, dan DELETE pada sesi/{id}/ sengaja dibalas 405 di ViewSet.
Sesi tidak diubah, sesi ditransisikan lewat aksi di atas.

URUTAN RUTE
    `sesi/rnd/` dan `sesi/banding/` adalah @action(detail=False). DRF
    SimpleRouter menempatkan dynamic list route SEBELUM detail route, jadi
    keduanya tidak tertelan oleh `sesi/{pk}/`. Jangan mengganti urutan
    router.routes.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    JenisPengukuranViewSet, ResepViewSet, SesiViewSet, alokasi_bahan,
    kalkulasi_kapasitas,
)

app_name = 'produksi'

router = DefaultRouter()
router.register('sesi', SesiViewSet, basename='sesi')
router.register('resep', ResepViewSet, basename='resep')
router.register('jenis-pengukuran', JenisPengukuranViewSet,
                basename='jenis-pengukuran')

urlpatterns = [
    path('kapasitas/', kalkulasi_kapasitas, name='kapasitas'),
    path('alokasi/', alokasi_bahan, name='alokasi'),
    path('', include(router.urls)),
]