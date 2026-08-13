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
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import Role

AKSES_MODUL = {
    'dashboard':   [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES, Role.STAFF],
    'akunting':    [Role.AKUNTING],
    'keuangan':    [Role.KEUANGAN],
    'pajak':       [Role.AKUNTING],
    'warehouse':   [Role.GUDANG],
    'inventory':   [Role.GUDANG, Role.PRODUKSI, Role.AKUNTING],
    'produksi':    [Role.PRODUKSI],
    'sales_order': [Role.SALES],
    'logistik':    [Role.GUDANG, Role.SALES],
    'work_order':  [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES, Role.STAFF],
    'master':      [Role.ADMIN],
    'dokumen':     [Role.ADMIN, Role.AKUNTING, Role.KEUANGAN, Role.GUDANG,
                    Role.PRODUKSI, Role.SALES],
    'staff_user':  [Role.ADMIN],
}
META_MODUL = {
    'dashboard':   {'label': 'Dashboard',      'ikon': 'pi-home',      'rute': '/'},
    'akunting':    {'label': 'Akunting',       'ikon': 'pi-book',      'rute': '/akunting'},
    'keuangan':    {'label': 'Keuangan',       'ikon': 'pi-wallet',    'rute': '/keuangan'},
    'pajak':       {'label': 'Pajak',          'ikon': 'pi-percentage','rute': '/pajak'},
    'warehouse':   {'label': 'Gudang',         'ikon': 'pi-box',       'rute': '/warehouse'},
    'inventory':   {'label': 'Persediaan',     'ikon': 'pi-database',  'rute': '/inventory'},
    'produksi':    {'label': 'Produksi',       'ikon': 'pi-cog',       'rute': '/produksi'},
    'sales_order': {'label': 'Sales Order',    'ikon': 'pi-shopping-cart', 'rute': '/sales-order'},
    'logistik':    {'label': 'Logistik',       'ikon': 'pi-truck',     'rute': '/logistik'},
    'work_order':  {'label': 'Papan Tugas',    'ikon': 'pi-list-check','rute': '/work-order'},
    'master':      {'label': 'Master Data',    'ikon': 'pi-server',    'rute': '/master'},
    'dokumen':     {'label': 'Dokumen',        'ikon': 'pi-file',      'rute': '/dokumen'},
    'staff_user':  {'label': 'Pengguna',       'ikon': 'pi-users',     'rute': '/pengguna'},
}


def role_boleh_modul(role, modul, superuser=False):
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
            meta = META_MODUL.get(kode, {})
            hasil.append({'kode': kode, **meta})
    return hasil


class SudahLogin(permissions.BasePermission):
    """Lebih ketat dari IsAuthenticated: status kerja ikut diperiksa."""

    message = 'Akun tidak aktif atau sudah keluar.'

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.bisa_login)


class AksesModul(permissions.BasePermission):
    """
    Dipasang di view lewat atribut `modul`:

        class PurchaseOrderViewSet(ModelViewSet):
            modul = 'akunting'
            permission_classes = [AksesModul]

    View tanpa atribut `modul` DITOLAK -- gagal tertutup, bukan terbuka.
    Kalau seseorang lupa menetapkan modulnya, endpoint tidak jalan sama
    sekali dan itu ketahuan langsung, bukan diam-diam terbuka untuk semua.
    """

    message = 'Peran Anda tidak punya akses ke modul ini.'

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and u.bisa_login):
            return False
        modul = getattr(view, 'modul', None)
        if not modul:
            return False
        return u.bisa_akses_modul(modul)


class PunyaRole(permissions.BasePermission):
    """
    Untuk endpoint yang lebih sempit dari modulnya.

        class TutupPeriodeView(APIView):
            permission_classes = [PunyaRole.dengan(Role.SUPERVISOR)]
    """

    roles = ()
    message = 'Peran Anda tidak diizinkan untuk aksi ini.'

    @classmethod
    def dengan(cls, *roles):
        return type('PunyaRoleKhusus', (cls,), {'roles': roles})

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and u.bisa_login):
            return False
        return u.punya_role(*self.roles)


class HanyaSupervisor(PunyaRole):
    roles = (Role.SUPERVISOR,)
    message = 'Hanya Supervisor yang boleh melakukan ini.'


class HanyaAdmin(PunyaRole):
    roles = (Role.SUPERVISOR, Role.ADMIN)
    message = 'Hanya Admin atau Supervisor yang boleh melakukan ini.'


class AdminAtauAkunting(PunyaRole):
    roles = (Role.SUPERVISOR, Role.ADMIN, Role.AKUNTING)
    message = 'Hanya Admin, Supervisor, atau staf Akunting yang boleh melakukan ini.'


class DiriSendiriAtauSupervisor(permissions.BasePermission):
    """
    Untuk data pribadi: pemilik boleh, Supervisor boleh, orang lain tidak.
    """

    message = 'Anda hanya boleh mengakses data Anda sendiri.'

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.supervisor:
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
        entitas_id = getattr(obj, 'entitas_id', None)
        if entitas_id is None:
            return True
        return request.user.bisa_akses_entitas(entitas_id)


class BacaSaja(permissions.BasePermission):
    """Gabungkan dengan AksesModul untuk memberi akses baca lebih luas."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS



class AksesModul(BasePermission):
    """
    Memastikan user memiliki hak akses ke modul yang di-request.
    View DRF harus menetapkan atribut `modul` (contoh: modul = 'inventory').
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        
        # Mengambil nama modul yang dideklarasikan di ViewSet / APIView
        modul = getattr(view, 'modul', None)
        
        # Tolak akses secara default jika view lupa mendefinisikan atribut modul
        if not modul:
            return False 
            
        # Memanggil metode bantuan pada model User untuk mengecek akses
        return getattr(request.user, 'bisa_akses_modul', lambda m: False)(modul)


class HanyaSupervisor(BasePermission):
    """
    Hanya mengizinkan akses jika pengguna memiliki atribut/hak akses Supervisor[cite: 25].
    Digunakan untuk menjaga endpoint sensitif seperti Verifikasi dan Opname yang tidak punya dokumen pembanding.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'supervisor', False)
        )


class PunyaRole(BasePermission):
    """
    Memeriksa apakah user memiliki role spesifik[cite: 25].
    Penggunaan: permission_classes = [PunyaRole.dengan(Role.GUDANG, Role.PRODUKSI)][cite: 25].
    """
    allowed_roles = []

    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
            
        user_role = getattr(request.user, 'role', None)
        return user_role in self.allowed_roles

    @classmethod
    def dengan(cls, *roles):
        """
        Factory method untuk membuat subclass permission dinamis secara on-the-fly[cite: 25].
        """
        return type(
            'PunyaRoleDinamis',
            (cls,),
            {'allowed_roles': roles}
        )


class AtauPermission(BasePermission):
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
 