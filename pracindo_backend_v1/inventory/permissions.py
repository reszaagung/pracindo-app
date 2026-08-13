from rest_framework.permissions import BasePermission

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