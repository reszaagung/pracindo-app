"""
Peta akses modul — staff_user/permissions.py

ROLE ADALAH KUNCI PORTAL. Modul mana yang terbuka ditentukan sepenuhnya
oleh role, dan petanya di bawah ini adalah DATA, bukan percabangan if
yang tersebar di tiap views.py.

Menambah modul baru = menambah entri dict. Mengubah siapa yang boleh
masuk = mengubah satu baris, bukan berburu ke belasan file.

PEMISAHAN TUGAS
    AKUNTING dan KEUANGAN sengaja TIDAK saling tumpang tindih. Orang yang
    menyetujui pembayaran tidak boleh orang yang memposting jurnal --
    kalau satu orang bisa keduanya, dia bisa mengarang faktur fiktif,
    membayarnya, lalu memposting jurnal yang merapikan jejaknya.

    Kalau di lapangan satu orang memang merangkap, berikan dia peran
    SUPERVISOR secara sadar -- jangan gabungkan dua role.

BUG YANG DIPERBAIKI DI VERSI INI

    Berkas ini sebelumnya mendefinisikan AksesModul, PunyaRole, dan
    HanyaSupervisor DUA KALI. Python memakai definisi terakhir, jadi:

    - AksesModul kehilangan pemeriksaan `bisa_login`.
    - PunyaRole versi kedua membaca `allowed_roles`, sementara HanyaAdmin
      dan AdminAtauAkunting di atasnya menulis `roles`. Keduanya jadi
      punya daftar role KOSONG -- menolak semua orang, selamanya, tanpa
      satu baris pun di log.

    Itu bug yang sama persis dengan yang diperingatkan docstring
    produksi/permissions.py: atribut dibaca dari tempat yang berbeda dari
    tempat ia ditulis. Sekarang tiap kelas hanya ada satu.
"""
from rest_framework import permissions

from .models import Role





# =========================================================
# SAKLAR PENGEMBANGAN
# =========================================================

# Membuka seluruh akses modul selama pengembangan.
#
# Autentikasi TETAP diwajibkan. Membuka permission modul berbeda dari
# membuka pintu: setiap dokumen transaksional punya `dibuat_oleh` yang
# non-nullable, jadi request anonim akan tetap gagal -- hanya dengan
# galat yang jauh lebih membingungkan.
#
# CABUT SEBELUM MENYENTUH DATA NYATA. Buku klaim yang bisa ditulis siapa
# saja bukan buku klaim.
BUKA_MODUL = False


AKSES_MODUL = {
    'dashboard':   [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES, Role.STAFF, Role.KURIR, Role.SUPERVISOR], 
    'akunting':    [Role.AKUNTING, Role.SUPERVISOR],
    'keuangan':    [Role.KEUANGAN, Role.SUPERVISOR],
    'pajak':       [Role.AKUNTING, Role.SUPERVISOR],
    'warehouse':   [Role.GUDANG, Role.SUPERVISOR],
    'warehouse_distribusi': [Role.GUDANG, Role.SUPERVISOR], 
    'inventory':   [Role.GUDANG, Role.PRODUKSI, Role.AKUNTING, Role.SUPERVISOR],
    'produksi':    [Role.PRODUKSI, Role.SUPERVISOR],
    'retail':      [Role.ADMIN, Role.SALES, Role.STAFF, Role.SUPERVISOR], 
    
    'sales_order': [Role.SALES, Role.SUPERVISOR],
    'logistik':    [Role.GUDANG, Role.SALES, Role.KURIR, Role.SUPERVISOR], 
    'work_order':  [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES, Role.STAFF, Role.SUPERVISOR],
    'master':      [Role.ADMIN, Role.SUPERVISOR],
    'dokumen':     [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES, Role.SUPERVISOR],
    'staff_user':  [Role.ADMIN, Role.SUPERVISOR],
}
META_MODUL = {
    'dashboard':   {'label': 'Dashboard',      'ikon': 'pi-home',          'rute': '/'},
    'akunting':    {'label': 'Akunting',       'ikon': 'pi-book',          'rute': '/akunting'},
    'keuangan':    {'label': 'Keuangan',       'ikon': 'pi-wallet',        'rute': '/keuangan'},
    'pajak':       {'label': 'Pajak',          'ikon': 'pi-percentage',    'rute': '/pajak'},
    'warehouse':   {'label': 'Gudang',         'ikon': 'pi-box',           'rute': '/warehouse'},
    'warehouse_distribusi': {'label': 'Distribusi', 'ikon': 'pi-truck',    'rute': '/distribusi'},
    'inventory':   {'label': 'Persediaan',     'ikon': 'pi-database',      'rute': '/inventory'},
    'produksi':    {'label': 'Produksi',       'ikon': 'pi-cog',           'rute': '/produksi'},
    'retail':      {'label': 'Retail & POS',   'ikon': 'pi-shop',          'rute': '/retail/pos'},
    
    'sales_order': {'label': 'Sales Order',    'ikon': 'pi-shopping-cart', 'rute': '/sales-order'},
    'logistik':    {'label': 'Logistik',       'ikon': 'pi-map',           'rute': '/kurir'}, 
    'work_order':  {'label': 'Papan Tugas',    'ikon': 'pi-list-check',    'rute': '/work-order'},
    'master':      {'label': 'Master Data',    'ikon': 'pi-server',        'rute': '/master'},
    'dokumen':     {'label': 'Dokumen',        'ikon': 'pi-file',          'rute': '/dokumen'},
    'staff_user':  {'label': 'Pengguna',       'ikon': 'pi-users',         'rute': '/pengguna'},
}


def role_boleh_modul(role, modul, superuser=False):
    if BUKA_MODUL:
        return True
    if superuser:
        return True
    if role == Role.SUPERVISOR:
        return True
    return role in AKSES_MODUL.get(modul, [])


def modul_untuk_role(role, superuser=False):
    """
    Daftar modul beserta metanya. Dipakai endpoint /auth/portal/ supaya
    frontend tidak perlu menyimpan salinan aturan akses.
    """
    hasil = []
    for kode in AKSES_MODUL:
        if role_boleh_modul(role, kode, superuser):
            hasil.append({'kode': kode, **META_MODUL.get(kode, {})})
    return hasil


def _login_sah(user):
    """
    Autentikasi + status kerja. Diperiksa SEBELUM BUKA_MODUL, jadi
    saklar pengembangan tidak pernah meloloskan anonim.
    """
    return bool(user and user.is_authenticated
                and getattr(user, 'bisa_login', True))


class SudahLogin(permissions.BasePermission):
    """Lebih ketat dari IsAuthenticated: status kerja ikut diperiksa."""

    message = 'Akun tidak aktif atau sudah keluar.'

    def has_permission(self, request, view):
        return _login_sah(request.user)


class AksesModul(permissions.BasePermission):
    """
    Dipasang di view lewat atribut `modul`:

        class PurchaseOrderViewSet(ModelViewSet):
            modul = 'akunting'
            permission_classes = [AksesModul]

    View tanpa atribut `modul` DITOLAK -- gagal tertutup, bukan terbuka.
    Kalau seseorang lupa menetapkan modulnya, endpoint tidak jalan sama
    sekali dan itu ketahuan langsung.

    Selama BUKA_MODUL menyala, pemeriksaan modul dilewati -- TAPI aturan
    "view wajib punya atribut modul" tetap berlaku. Melonggarkannya juga
    akan menyembunyikan view yang lupa dikonfigurasi sampai saklarnya
    dicabut, dan saat itu terjadi seluruh modul mati sekaligus tanpa
    petunjuk mana yang salah.
    """

    message = 'Peran Anda tidak punya akses ke modul ini.'

    def has_permission(self, request, view):
        if not _login_sah(request.user):
            return False
        modul = getattr(view, 'modul', None)
        if not modul:
            return False
        return request.user.bisa_akses_modul(modul)


class PunyaRole(permissions.BasePermission):
    """
    Untuk endpoint yang lebih sempit dari modulnya.

        class TutupPeriodeView(APIView):
            permission_classes = [PunyaRole.dengan(Role.SUPERVISOR)]

    Atribut yang dibaca dan yang ditulis .dengan() HARUS sama namanya.
    Versi lama punya dua definisi kelas ini dengan nama atribut berbeda
    (`roles` vs `allowed_roles`), dan turunan yang menulis salah satu
    diam-diam berakhir dengan daftar kosong.
    """

    roles = ()
    message = 'Peran Anda tidak diizinkan untuk aksi ini.'

    @classmethod
    def dengan(cls, *roles):
        return type('PunyaRoleKhusus', (cls,), {'roles': roles})

    def has_permission(self, request, view):
        if not _login_sah(request.user):
            return False
        if BUKA_MODUL:
            return True
        cek = getattr(request.user, 'punya_role', None)
        if callable(cek):
            return cek(*self.roles)
        return getattr(request.user, 'role', None) in self.roles


class HanyaSupervisor(PunyaRole):
    roles = (Role.SUPERVISOR,)
    message = 'Hanya Supervisor yang boleh melakukan ini.'


class HanyaAdmin(PunyaRole):
    roles = (Role.SUPERVISOR, Role.ADMIN)
    message = 'Hanya Admin atau Supervisor yang boleh melakukan ini.'


class AdminAtauAkunting(PunyaRole):
    roles = (Role.SUPERVISOR, Role.ADMIN, Role.AKUNTING)
    message = ('Hanya Admin, Supervisor, atau staf Akunting yang boleh '
               'melakukan ini.')


class DiriSendiriAtauSupervisor(permissions.BasePermission):
    """Data pribadi: pemilik boleh, Supervisor boleh, orang lain tidak."""

    message = 'Anda hanya boleh mengakses data Anda sendiri.'

    def has_object_permission(self, request, view, obj):
        u = request.user
        sup = getattr(u, 'supervisor', False)
        if callable(sup):
            try:
                sup = sup()
            except TypeError:
                sup = False
        if sup:
            return True
        target = getattr(obj, 'profil_id', None) or getattr(obj, 'id', None)
        return target == u.id


class AksesEntitas(permissions.BasePermission):
    """
    Objek yang punya field `entitas` hanya boleh diakses kalau entitas itu
    ada dalam daftar izin pengguna. Daftar kosong = boleh semua.
    """

    message = 'Anda tidak punya akses ke entitas ini.'

    def has_object_permission(self, request, view, obj):
        if BUKA_MODUL:
            return True
        entitas_id = getattr(obj, 'entitas_id', None)
        if entitas_id is None:
            return True
        return request.user.bisa_akses_entitas(entitas_id)


class BacaSaja(permissions.BasePermission):
    """Gabungkan dengan AksesModul untuk memberi akses baca lebih luas."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class AtauPermission(permissions.BasePermission):
    """
    Lolos kalau SALAH SATU permission terpenuhi.

    Dipakai untuk aksi yang boleh dijalankan operator produksi ATAU
    supervisor, tanpa harus menulis kelas gabungan satu per satu.
    """

    kelas = ()

    def has_permission(self, request, view):
        return any(k().has_permission(request, view) for k in self.kelas)

    @classmethod
    def dari(cls, *kelas):
        return type('AtauDinamis', (cls,), {'kelas': kelas})