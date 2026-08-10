from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DaftarView, DataKepegawaianViewSet, GantiPasswordView, JabatanViewSet,
    LoginView, LogoutView, PortalView, ProfilViewSet, RiwayatAksesViewSet,
)

app_name = 'staff_user'

router = DefaultRouter()
router.register('profil', ProfilViewSet, basename='profil')
router.register('jabatan', JabatanViewSet, basename='jabatan')
router.register('kepegawaian', DataKepegawaianViewSet, basename='kepegawaian')
router.register('riwayat-akses', RiwayatAksesViewSet, basename='riwayat-akses')

urlpatterns = [
    path('daftar/', DaftarView.as_view(), name='daftar'),
    # Alias untuk frontend yang memanggil auth/register/
    path('register/', DaftarView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('portal/', PortalView.as_view(), name='portal'),
    path('ganti-password/', GantiPasswordView.as_view(), name='ganti-password'),
    path('', include(router.urls)),
]
