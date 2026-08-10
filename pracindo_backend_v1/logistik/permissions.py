"""
Aturan akses logistik — logistik/permissions.py

Peran KURIR adalah peran paling sempit di sistem ini. Dia butuh melihat
alamat pelanggan dan mengunggah foto, dan tidak butuh apa pun selain itu:
bukan nilai transaksi, bukan daftar pelanggan, bukan pengiriman rekannya.

Karena itu akses modul saja tidak cukup. AksesModul menjawab "boleh masuk
modul logistik?", sedangkan penyaringan di bawah menjawab "baris yang mana".
"""
from rest_framework import permissions

from staff_user.models import Role


def adalah_kurir(user):
    return getattr(user, 'role', None) == Role.KURIR and not user.is_superuser


def batasi_ke_kurir(qs, user, lewat='kurir_id'):
    """
    Saring queryset supaya kurir hanya melihat pengirimannya sendiri.

    `lewat` menyesuaikan jalur relasi, mis. 'pengiriman__kurir_id' untuk
    queryset perhentian.
    """
    if not adalah_kurir(user):
        return qs
    return qs.filter(**{lewat: user.id})


class KurirTidakMengubahRute(permissions.BasePermission):
    """
    Kurir boleh menandai sampai, mengunggah bukti, dan mencatat retur.
    Kurir TIDAK boleh merakit pengiriman, mengubah muatan, atau menugaskan
    dirinya ke perjalanan lain.
    """

    message = 'Kurir tidak berwenang mengubah susunan pengiriman.'

    AKSI_KURIR = {
        'list', 'retrieve', 'sampai', 'bukti', 'retur', 'posisi', 'tugas_saya',
    }

    def has_permission(self, request, view):
        if not adalah_kurir(request.user):
            return True
        return getattr(view, 'action', None) in self.AKSI_KURIR


class HanyaKurirPengiriman(permissions.BasePermission):
    """Aksi lapangan hanya boleh oleh kurir yang membawa pengiriman itu."""

    message = 'Anda bukan kurir pengiriman ini.'

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or getattr(request.user, 'supervisor', False):
            return True
        kurir_id = getattr(obj, 'kurir_id', None)
        if kurir_id is None:
            kurir_id = getattr(getattr(obj, 'pengiriman', None), 'kurir_id', None)
        if kurir_id is None:
            return True
        if adalah_kurir(request.user):
            return kurir_id == request.user.id
        return True
