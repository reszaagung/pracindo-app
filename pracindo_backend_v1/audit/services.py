"""
Pencatat jejak — audit/services.py

catat() dipanggil dari service app lain SETELAH perubahan status
berhasil, di dalam transaksi yang sama. Kalau transaksi di-rollback,
jejaknya ikut hilang -- dan itu benar, karena perubahannya juga tidak
pernah terjadi.

TIDAK PERNAH memblokir operasi utama. Kegagalan pencatatan jejak tidak
boleh membatalkan pembatalan PO. Semua galat ditelan dan dicatat ke log.
"""
import logging

from django.contrib.contenttypes.models import ContentType

from .models import JejakAktivitas

log = logging.getLogger(__name__)


def catat(*, objek, aksi, oleh=None, status_lama='', status_baru='',
          alasan='', entitas=None, rincian=None, request=None):
    """
    Mencatat satu perubahan status.

        catat(objek=po, aksi=JenisAksi.BATAL, oleh=user,
              status_lama='TERKIRIM', status_baru='BATAL',
              alasan='Suplier tidak sanggup')

    entitas diturunkan otomatis dari objek kalau punya field entitas.
    """
    try:
        if entitas is None:
            entitas = getattr(objek, 'entitas', None)
            # property entitas di PenerimaanBarang mengembalikan objek,
            # tapi di model lain bisa berupa FK biasa. Keduanya aman.

        JejakAktivitas.objects.create(
            oleh=oleh,
            aksi=aksi,
            content_type=ContentType.objects.get_for_model(objek),
            object_id=objek.pk,
            label_objek=str(objek)[:120],
            entitas=entitas,
            status_lama=str(status_lama or '')[:32],
            status_baru=str(status_baru or '')[:32],
            alasan=alasan or '',
            rincian=rincian,
            ip=_ip(request),
        )
    except Exception:
        # Jejak gagal tidak boleh membatalkan operasi bisnis.
        log.exception('Gagal mencatat jejak aktivitas untuk %r', objek)


def catat_perubahan_status(*, objek, aksi, oleh, sebelum, sesudah,
                           alasan='', request=None):
    """
    Pembungkus untuk kasus paling umum: satu field status berubah.
    Tidak mencatat apa pun kalau nilainya tidak benar-benar berubah.
    """
    if sebelum == sesudah:
        return
    catat(objek=objek, aksi=aksi, oleh=oleh,
          status_lama=sebelum, status_baru=sesudah,
          alasan=alasan, request=request)


def riwayat_objek(objek):
    """Seluruh jejak untuk satu objek, terbaru dulu."""
    return (JejakAktivitas.objects
            .filter(content_type=ContentType.objects.get_for_model(objek),
                    object_id=objek.pk)
            .select_related('oleh', 'entitas'))


def _ip(request):
    if request is None:
        return None
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
