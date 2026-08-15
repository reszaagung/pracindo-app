"""
Hak akses persediaan — inventory/permissions.py

KENAPA ADA BERKAS INI

`staff_user.permissions` dipakai bersama seluruh modul. Dua kelemahannya
tidak bisa diperbaiki dari sana tanpa mengubah perilaku modul lain yang
mungkin sudah bergantung padanya, jadi pengerasannya dilakukan di sini,
lokal untuk inventory saja.

    HanyaSupervisor membaca `getattr(user, 'supervisor', False)`.
    Kalau `supervisor` ternyata METHOD dan bukan property, getattr
    mengembalikan bound method -- dan bound method selalu truthy. Setiap
    user terautentikasi jadi supervisor: opname, pelunasan, dan
    verifikasi terbuka untuk semua orang, tanpa satu baris pun di log.

    AksesModul membaca `getattr(view, 'modul')` dan menolak kalau kosong.
    Aman selama view berupa kelas. `@api_view` tidak bisa diberi atribut
    kelas, jadi endpoint fungsi akan 403 diam-diam.

Keduanya ditangani di bawah. Kalau nanti staff_user diperbaiki di
sumbernya, berkas ini bisa dihapus dan views.py kembali mengimpor
langsung dari sana.
"""
from rest_framework.permissions import BasePermission

from staff_user.permissions import AksesModul

MODUL = 'inventory'


def _nilai_atribut(obj, nama, default=False):
    """
    Ambil atribut, panggil kalau dia callable.

    Ini yang membedakan property `supervisor` dari method `supervisor()`.
    Tanpa pemanggilan, yang kedua selalu bernilai benar.
    """
    nilai = getattr(obj, nama, default)
    if callable(nilai):
        try:
            return nilai()
        except TypeError:
            # Butuh argumen -- bukan penanda boolean. Anggap tidak punya.
            return default
    return nilai


class AksesInventory(AksesModul):
    """
    Sama seperti AksesModul, tapi nama modulnya tidak diambil dari view.

    Dengan begini endpoint fungsi (`@api_view`) ikut lolos, dan view yang
    lupa memasang atribut `modul` tidak diam-diam jadi 403.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        cek = getattr(request.user, 'bisa_akses_modul', None)
        if not callable(cek):
            # Model user tidak punya metode ini sama sekali. Menolak
            # adalah pilihan yang benar, tapi diam-diam menolak seluruh
            # modul adalah cara termahal untuk mengetahuinya.
            raise RuntimeError(
                'Model user tidak punya metode bisa_akses_modul(). '
                'AksesInventory tidak bisa memutuskan apa pun.'
            )
        return bool(cek(MODUL))


class SupervisorInventory(BasePermission):
    """
    Supervisor DAN punya akses modul inventory.

    Versi lama hanya memeriksa flag supervisor, jadi supervisor modul
    lain -- keuangan, HR -- tetap bisa menekan /opname/ dan /lunas/.
    """

    def has_permission(self, request, view):
        if not AksesInventory().has_permission(request, view):
            return False
        return bool(_nilai_atribut(request.user, 'supervisor', False))


class Akunting(BasePermission):
    """Boleh melihat kolom rupiah."""

    def has_permission(self, request, view):
        cek = getattr(request.user, 'bisa_akses_modul', None)
        return bool(callable(cek) and cek('akunting'))


def boleh_akunting(request):
    """Versi fungsi, dipakai view untuk memilih serializer."""
    return Akunting().has_permission(request, None)


def grup_yang_boleh(user):
    """
    Daftar id grup bahan yang boleh dilihat user ini, atau None kalau
    tidak ada pembatasan.

    None berarti "semua" -- perilaku lama. Begitu model user Anda punya
    `grup_bahan_ids` (property, method, atau queryset), pembatasannya
    langsung berlaku di SELURUH queryset inventory tanpa menyentuh satu
    view pun.
    """
    nilai = _nilai_atribut(user, 'grup_bahan_ids', None)
    if nilai is None:
        return None
    return {int(x) for x in nilai}