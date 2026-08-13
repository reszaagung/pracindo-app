"""
PERUBAHAN UNTUK produksi/tests.py
=================================

Tiga suntingan kecil di kelas yang sudah ada, plus satu kelas baru.
Berkas ini bukan pengganti utuh -- sisa produksi/tests.py tidak berubah.

Tambahkan impor di bagian atas produksi/tests.py:

    from django.db.models import Sum
"""


# =========================================================
# 1. GANTI DasarProduksiTest._nilai_pool()
# =========================================================
# Sisa eksperimen `... if False else ...` masih menempel di sana.

    def _nilai_pool(self):
        return (Stok.objects
                .filter(grup_bahan=self.grup, lapis=Lapis.POOL)
                .aggregate(t=Sum('nilai'))['t'] or D('0'))


# =========================================================
# 2. GANTI satu baris di test_klaim_memakai_porsi_tangki_saat_itu
# =========================================================
#
#   47.142,86 x 10 / 33 = 14.285,7151515...
#   quantize(0,01, ROUND_HALF_UP) -> 14.285,72
#
# Kodenya benar; ekspektasi ujinya yang meleset satu sen. Perbarui juga
# docstring-nya supaya angka di komentar tidak lagi bertentangan.

        self.assertEqual(klaim.nilai, D('-14285.72'))


# =========================================================
# 3. ISI DasarProduksiTest._siapkan()
# =========================================================
# Selama ini `raise NotImplementedError`, jadi SELURUH berkas uji tidak
# pernah berjalan sama sekali. Yang wajib dibuat:
#
#   - Entitas: self.pt, self.cv, self.ud
#   - GrupBahan: self.grup (berisi ketiga entitas)
#   - Produk: self.bahan_a, self.bahan_b, self.bahan_c, self.produk_jadi
#   - Tangki: self.tangki_1, self.tangki_2, self.tangki_hasil
#   - Resep: self.resep (+ ResepItem untuk A/B/C)
#   - User: self.operator
#   - self.tanggal
#
# CATATAN PENTING setelah patch P8 (Opsi A):
#   NilaiEkuivalen tidak lagi dipakai setor_ke_pool() selama RAW punya
#   dasar biaya. Nilai pool sekarang SAMA dengan harga perolehan, jadi
#   test_nilai_bahan_terkumpul_persis benar tanpa perlu menyamakan tarif
#   secara manual. Sebelum patch, uji itu hanya lulus kalau tarif
#   ekuivalen kebetulan dibuat 1000/1500/2000.


# =========================================================
# 4. KELAS BARU — uji regresi hak akses
# =========================================================
# Bug "modul produksi mati total" tidak menghasilkan error apa pun di
# log, hanya 403. Jenis bug yang kembali diam-diam saat ada yang
# merapikan permissions.

class HakAksesTest(TestCase):

    class _UserPalsu:
        is_authenticated = True

        def __init__(self, modul=('produksi',)):
            self._modul = set(modul)

        def bisa_akses_modul(self, m):
            return m in self._modul

    def _request(self, user):
        from rest_framework.test import APIRequestFactory
        req = APIRequestFactory().get('/')
        req.user = user
        return req

    def test_modul_produksi_lolos_tanpa_atribut_di_view(self):
        """
        AksesModul induk membaca getattr(view, 'modul'). ModulProduksi
        harus membacanya dari dirinya sendiri, supaya @api_view --
        yang tidak bisa diberi atribut kelas -- ikut lolos.
        """
        from produksi.permissions import ModulProduksi

        req = self._request(self._UserPalsu())
        # `object()` mewakili view tanpa atribut `modul` sama sekali.
        self.assertTrue(ModulProduksi().has_permission(req, object()))

    def test_modul_lain_tetap_ditolak(self):
        from produksi.permissions import ModulProduksi

        req = self._request(self._UserPalsu(modul=('inventory',)))
        self.assertFalse(ModulProduksi().has_permission(req, object()))

    def test_anonim_ditolak(self):
        from produksi.permissions import ModulProduksi

        class Anon:
            is_authenticated = False

        req = self._request(Anon())
        self.assertFalse(ModulProduksi().has_permission(req, object()))


# =========================================================
# 5. KELAS BARU — uji regresi untuk P3, P4, P5
# =========================================================

class InvariantPenjagaTest(DasarProduksiTest):

    def test_stok_habis_tidak_boleh_menyisakan_nilai(self):
        """
        _catat() dulu memaksa nilai jadi nol saat qty habis, dan
        verifikasi_rantai_saldo() justru mengecualikan baris ber-qty nol.
        Sekarang kondisi itu HARUS meledak, bukan dibungkam.
        """
        from inventory.services import _catat, _stok
        from inventory.models import JenisMutasiStok

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        stok = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.POOL,
                                produk=self.bahan_a)

        # Keluarkan seluruh qty tapi hanya sebagian nilainya.
        with self.assertRaises(ValidationError) as ctx:
            _catat(stok, JenisMutasiStok.PAKAI, D('0'), stok.qty,
                   self.tanggal, 'UJI-RECEH', 'uji:receh',
                   nilai_keluar=stok.nilai - D('0.01'))
        self.assertIn('masih menyisakan', str(ctx.exception))

    def test_bebankan_rugi_dua_kali_tidak_membebankan_dua_kali(self):
        """
        Penjaga lama memeriksa kunci ':0', yang bisa tidak pernah ditulis
        kalau bagian pertama membulat ke nol -- pemanggilan kedua lolos.
        """
        from inventory.services import bebankan_rugi

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.cv, self.bahan_a, 10, 1000)

        awal = verifikasi_pool_bersih(self.grup.id)['total_posisi']
        bebankan_rugi(grup_bahan_id=self.grup.id, nilai=D('1000.00'),
                      tanggal=self.tanggal, referensi='UJI',
                      idem_key='uji:rugi-ganda')
        bebankan_rugi(grup_bahan_id=self.grup.id, nilai=D('1000.00'),
                      tanggal=self.tanggal, referensi='UJI',
                      idem_key='uji:rugi-ganda')
        akhir = verifikasi_pool_bersih(self.grup.id)['total_posisi']

        self.assertEqual(akhir, awal - D('1000.00'))

    def test_rendemen_dihitung_atas_target_bukan_kilogram(self):
        """
        Resep yang memekatkan: 35 kg bahan -> 30 unit target.
        Hasil 29 unit adalah susut 3,3%, bukan 17,1%.

        Butuh resep dengan hasil_per_batch yang membuat total kg bahan
        berbeda dari qty_target -- isi di _siapkan() proyek ini.
        """
        self.skipTest('Isi dengan resep 35 kg -> 30 unit di _siapkan().')