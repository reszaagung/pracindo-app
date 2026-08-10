"""
Sambungan ke warehouse — logistik/integrasi_warehouse.py

SATU-SATUNYA tempat logistik berbicara dengan warehouse. Tidak ada berkas
lain di app ini yang boleh mengimpor apa pun dari warehouse.

Alasannya bukan kerapian: kalau sambungannya tersebar, mengganti bentuk
Distribusi berarti berburu ke seluruh app. Terkumpul di sini, kontraknya
bisa dibaca sekali dan diubah sekali.

============================================================
KONTRAK YANG HARUS DISEDIAKAN warehouse/services.py
============================================================

    distribusi_siap_kirim(entitas_id=None) -> list[dict]
        Distribusi yang stoknya sudah dikurangi tapi belum masuk pengiriman.
        Tiap dict: {id, nomor, pelanggan_nama, alamat, lat, lng, berat_kg}

    rincian_distribusi(distribusi_id) -> dict
        Sama seperti di atas untuk satu id, ditambah `baris`:
        [{produk_kode, produk_nama, stiker, qty, unit}]

    tandai_terkirim(distribusi_id, waktu, oleh) -> None
        Dipanggil saat bukti terima masuk.

    kembalikan_stok(distribusi_id, alasan, oleh) -> None
        Dipanggil setelah retur DISETUJUI Supervisor. warehouse yang
        menentukan barang kembali ke stok badan hukum mana berdasarkan
        stikernya, dan apakah masuk stok siap jual atau tidak.

Selama warehouse belum ada, keempatnya melempar SambunganBelumSiap dengan
pesan yang menyebut fungsi mana yang kurang. GAGAL KERAS DISENGAJA --
mengembalikan daftar kosong akan membuat layar perakitan pengiriman terlihat
"tidak ada yang perlu dikirim", padahal sebenarnya belum tersambung.
"""
import logging

logger = logging.getLogger(__name__)


class SambunganBelumSiap(Exception):
    """warehouse belum menyediakan fungsi yang dibutuhkan."""


def _service(nama):
    try:
        from warehouse import services as ws
    except ImportError as exc:
        raise SambunganBelumSiap(
            'Modul warehouse belum tersedia. Lihat kontrak di '
            'logistik/integrasi_warehouse.py.'
        ) from exc

    fn = getattr(ws, nama, None)
    if fn is None:
        raise SambunganBelumSiap(
            f'warehouse.services.{nama}() belum ada. '
            f'Lihat kontrak di logistik/integrasi_warehouse.py.'
        )
    return fn


def distribusi_siap_kirim(entitas_id=None):
    return _service('distribusi_siap_kirim')(entitas_id=entitas_id)


def rincian_distribusi(distribusi_id):
    return _service('rincian_distribusi')(distribusi_id)


def tandai_terkirim(distribusi_id, waktu, oleh):
    return _service('tandai_terkirim')(distribusi_id, waktu=waktu, oleh=oleh)


def kembalikan_stok(distribusi_id, alasan, oleh):
    return _service('kembalikan_stok')(distribusi_id, alasan=alasan, oleh=oleh)


def tersedia():
    """Cek cepat untuk endpoint kesehatan dan pesan galat yang ramah."""
    try:
        _service('distribusi_siap_kirim')
        return True
    except SambunganBelumSiap:
        return False
