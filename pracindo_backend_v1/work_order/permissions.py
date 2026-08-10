"""
Izin Papan Tugas — work_order/permissions.py

Modul ini terbuka untuk SEMUA peran lewat AKSES_MODUL['work_order'], jadi
`AksesModul` hanya menjawab "sudah login dan masih aktif?". Yang menentukan
baris mana yang terlihat adalah services.wo_terlihat(), dipanggil dari
get_queryset().

Kelas di bawah menjaga penyuntingan: melihat dan mengubah bukan hal yang
sama. Orang yang ditandai boleh membaca dan menyetujui, tapi tidak boleh
mengubah susunan tugas yang bukan dia buat.
"""
from rest_framework import permissions

from . import services


class BolehUbahWorkOrder(permissions.BasePermission):
    """
    Baca: siapa pun yang lolos penyaringan queryset.
    Ubah: hanya pembuat, Supervisor, atau superuser.

    Aksi lapangan (setujui, kirim pesan) TIDAK lewat sini -- keduanya punya
    aturannya sendiri di services, dan orang yang ditandai memang berhak
    melakukannya walau bukan pembuat.
    """

    message = 'Hanya pembuat tugas atau Supervisor yang boleh mengubahnya.'

    AKSI_BEBAS = {'setujui', 'kirim_pesan', 'pesan', 'mading', 'staff',
                  'list', 'retrieve'}

    def has_object_permission(self, request, view, obj):
        if getattr(view, 'action', None) in self.AKSI_BEBAS:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return services.boleh_ubah(obj, request.user)
