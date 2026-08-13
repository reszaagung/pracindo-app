"""
Hak akses produksi — produksi/permissions.py

Tiga tingkat, dari longgar ke ketat:

    ModulProduksi   membaca sesi, resep, kapasitas
    OperatorSesi    menjalankan sesi (bahan benar-benar keluar dari pool)
    HanyaSupervisor menyetujui susut di luar batas resep

RIWAYAT BUG
    Versi sebelumnya menaruh `modul = 'produksi'` di permission class,
    sementara AksesModul membacanya dari VIEW lewat getattr(view, 'modul').
    Hasilnya `modul` selalu None -> `return False` -> setiap endpoint
    produksi menolak semua orang, termasuk superuser. Modul mati total,
    dan docstring lama justru mengklaim bug itu sudah diperbaiki.

    Memindahkan atribut ke tiap ViewSet tidak cukup: kalkulasi_kapasitas()
    dan alokasi_bahan() memakai @api_view, yang menghasilkan WrappedAPIView
    dan tidak bisa diberi atribut kelas. Jadi permission-nya yang dibuat
    mandiri.
"""
from staff_user.models import Role
from staff_user.permissions import (
    AksesModul, AtauPermission, HanyaSupervisor, PunyaRole,
)


class ModulProduksi(AksesModul):
    """
    Membaca `modul` dari PERMISSION, bukan dari view.

    Berlaku sama untuk ViewSet maupun @api_view. Jangan menghapus
    has_permission() di bawah dengan alasan "sudah ada di induk" -- induknya
    membaca atribut dari tempat yang berbeda.
    """
    modul = 'produksi'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        cek = getattr(user, 'bisa_akses_modul', None)
        return bool(callable(cek) and cek(self.modul))


OperatorProduksi = PunyaRole.dengan(Role.PRODUKSI, Role.GUDANG)
OperatorSesi = AtauPermission.dari(OperatorProduksi, HanyaSupervisor)

ModulProduksiPermission = ModulProduksi