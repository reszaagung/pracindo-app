"""
Token dengan masa berlaku — staff_user/authentication.py

DRF Token bawaan tidak pernah kedaluwarsa. Untuk ERP internal itu tidak
memadai: token yang bocor berlaku selamanya sampai seseorang sadar dan
menghapusnya manual.

Umur token diatur lewat settings.TOKEN_EXPIRE_HOURS (default 12 jam).
Token kedaluwarsa DIHAPUS, bukan cuma ditolak -- kalau hanya ditolak,
tabel token menumpuk baris mati yang tidak pernah dibersihkan.

Status kerja ikut diperiksa di sini, bukan hanya di permission class.
Karyawan yang sudah keluar tidak boleh lolos autentikasi sama sekali,
meskipun tokennya belum kedaluwarsa.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):

    keyword = 'Token'

    @staticmethod
    def umur_token():
        return timedelta(hours=getattr(settings, 'TOKEN_EXPIRE_HOURS', 12))

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Token tidak dikenali.')

        if not token.user.is_active:
            raise AuthenticationFailed('Akun sudah dinonaktifkan.')

        if not token.user.bisa_login:
            token.delete()
            raise AuthenticationFailed('Akun sudah tidak berlaku.')

        if timezone.now() - token.created > self.umur_token():
            token.delete()
            raise AuthenticationFailed('Sesi berakhir, silakan login kembali.')

        return token.user, token
