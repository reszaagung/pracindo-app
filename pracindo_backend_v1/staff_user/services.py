"""
Logika bisnis pengguna — staff_user/services.py

Semua perubahan status akun lewat sini, bukan lewat serializer langsung,
supaya pemeriksaan wewenang dan pencatatan jejak konsisten di semua jalur.
"""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import Profil, RiwayatAkses, Role, StatusKerja

@transaction.atomic
def daftar(*, username, password, first_name, last_name='', email='',
           nomor_hp=''):
    """
    Pendaftaran mandiri. role dan is_active DIPAKSA di sini -- nilai dari
    payload tidak pernah dipakai. Tanpa ini, orang bisa mendaftar sebagai
    SUPERVISOR dengan mengirim field tambahan.
    """
    if Profil.objects.filter(username__iexact=username).exists():
        raise ValidationError({'username': 'Username sudah dipakai.'})

    validate_password(password)

    profil = Profil(
        username=username, first_name=first_name, last_name=last_name,
        email=email, nomor_hp=nomor_hp,
        role=Role.STAFF,      
        is_active=False,       
    )
    profil.set_password(password)
    profil.save()
    return profil


@transaction.atomic
def aktifkan(*, profil_id, oleh, role, jabatan_id=None, nip=None,
             entitas_default_id=None, entitas_diizinkan_ids=None,
             atasan_id=None, tanggal_masuk=None):
    """
    Supervisor menyetujui pendaftaran DAN menetapkan peran sekaligus.

    Digabung sengaja: kalau persetujuan dan penetapan peran terpisah,
    ada jendela waktu akun aktif dengan peran STAFF yang belum diniatkan.
    """
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh menyetujui akun.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    if profil.is_active:
        raise ValidationError('Akun ini sudah aktif.')
    if role == Role.SUPERVISOR and not oleh.is_superuser:
        raise ValidationError(
            'Peran Supervisor hanya bisa diberikan oleh superuser.'
        )
    if nip and Profil.objects.filter(nip=nip).exclude(pk=profil.pk).exists():
        raise ValidationError({'nip': f'NIP {nip} sudah dipakai.'})

    profil.role = role
    profil.is_active = True
    profil.jabatan_id = jabatan_id
    profil.nip = nip or profil.nip
    profil.entitas_default_id = entitas_default_id
    profil.atasan_id = atasan_id
    profil.tanggal_masuk = tanggal_masuk or timezone.localdate()
    profil.status_kerja = StatusKerja.AKTIF
    profil.disetujui_oleh = oleh
    profil.disetujui_pada = timezone.now()
    profil.ditolak_pada = None
    profil.alasan_tolak = ''
    profil.save()

    if entitas_diizinkan_ids:
        profil.entitas_diizinkan.set(entitas_diizinkan_ids)
    return profil


@transaction.atomic
def tolak(*, profil_id, oleh, alasan):
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh menolak akun.')
    if not alasan.strip():
        raise ValidationError('Alasan penolakan wajib diisi.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    if profil.is_active:
        raise ValidationError('Akun sudah aktif, tidak bisa ditolak.')

    profil.ditolak_pada = timezone.now()
    profil.alasan_tolak = alasan
    profil.save(update_fields=['ditolak_pada', 'alasan_tolak'])
    return profil


@transaction.atomic
def ubah_role(*, profil_id, role_baru, oleh, alasan=''):
    """
    Mengubah peran berarti mengubah akses modul. Token lama DIHAPUS supaya
    sesi berjalan tidak lanjut memakai izin lama.
    """
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh mengubah peran.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    if profil.id == oleh.id:
        raise ValidationError('Tidak bisa mengubah peran diri sendiri.')
    if role_baru == Role.SUPERVISOR and not oleh.is_superuser:
        raise ValidationError(
            'Peran Supervisor hanya bisa diberikan oleh superuser.'
        )

    profil.role = role_baru
    profil.save(update_fields=['role'])
    Token.objects.filter(user=profil).delete()
    return profil


@transaction.atomic
def nonaktifkan(*, profil_id, oleh, tanggal_keluar=None, alasan=''):
    """
    Akun tidak pernah dihapus -- jejak audit transaksi merujuk ke sini.
    """
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh menonaktifkan akun.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    if profil.id == oleh.id:
        raise ValidationError('Tidak bisa menonaktifkan diri sendiri.')

    profil.is_active = False
    profil.status_kerja = StatusKerja.KELUAR
    profil.tanggal_keluar = tanggal_keluar or timezone.localdate()
    profil.save(update_fields=['is_active', 'status_kerja', 'tanggal_keluar'])
    Token.objects.filter(user=profil).delete()
    return profil


@transaction.atomic
def aktifkan_kembali(*, profil_id, oleh):
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh mengaktifkan akun.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    profil.is_active = True
    profil.status_kerja = StatusKerja.AKTIF
    profil.tanggal_keluar = None
    profil.save(update_fields=['is_active', 'status_kerja', 'tanggal_keluar'])
    return profil


@transaction.atomic
def ganti_password(*, profil, password_lama, password_baru):
    """
    Password lama WAJIB. Tanpa itu, sesi yang dibajak bisa mengunci
    pemilik akun keluar dari akunnya sendiri.
    """
    if not profil.check_password(password_lama):
        raise ValidationError({'password_lama': 'Password lama salah.'})
    if password_lama == password_baru:
        raise ValidationError({'password_baru': 'Password baru harus berbeda.'})

    validate_password(password_baru, profil)
    profil.set_password(password_baru)
    profil.save(update_fields=['password'])

    Token.objects.filter(user=profil).delete()
    return Token.objects.create(user=profil)


@transaction.atomic
def reset_password(*, profil_id, password_baru, oleh):
    """Supervisor mereset password yang lupa. Semua sesi lama dimatikan."""
    if not oleh.supervisor:
        raise ValidationError('Hanya Supervisor yang boleh mereset password.')

    profil = Profil.objects.select_for_update().get(pk=profil_id)
    validate_password(password_baru, profil)
    profil.set_password(password_baru)
    profil.save(update_fields=['password'])
    Token.objects.filter(user=profil).delete()
    return profil


def catat_akses(*, request, username, profil=None, berhasil, alasan=''):
    RiwayatAkses.objects.create(
        profil=profil,
        username_dicoba=username[:150],
        berhasil=berhasil,
        alasan_gagal=alasan[:80],
        ip=_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )


def _ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@transaction.atomic
def terbitkan_token(profil):
    """Satu token per pengguna. Login baru mematikan sesi lama."""
    Token.objects.filter(user=profil).delete()
    return Token.objects.create(user=profil)
