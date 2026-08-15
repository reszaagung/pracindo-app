"""
Uji regresi persediaan — inventory/tests.py

Berkas ini menggantikan patch `PATCH-tests` yang lama. Yang lama tidak
bisa di-collect sama sekali: ada `def` menggantung di level modul, dan
setengah namanya tidak diimpor. Berkas uji yang tidak pernah berjalan
lebih berbahaya daripada tidak ada berkas uji, karena dia terlihat
seperti jaring pengaman.

DUA KELOMPOK
    UjiAritmetika  murni fungsi, JALAN TANPA FIXTURE apa pun.
    UjiInvariant   butuh data master. Isi _siapkan() dengan pabrik objek
                   proyek Anda; selama belum diisi, seluruh kelas ini
                   di-skip dengan pesan yang jelas, BUKAN lolos diam-diam.
"""
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from inventory.services import _porsi_nilai, alokasi_prorata


class _StokPalsu:
    def __init__(self, qty, nilai):
        self.qty = D(qty)
        self.nilai = D(nilai)


# =========================================================
# 1. ARITMETIKA — tidak butuh database
# =========================================================

class UjiAritmetika(SimpleTestCase):

    def test_porsi_menguras_habis_membawa_seluruh_sisa(self):
        """
        Kalau qty menghabiskan stok, seluruh nilai ikut -- tidak dihitung
        proporsional. Tanpa aturan ini receh tertinggal di baris kosong
        dan invariant (2) melenceng pelan-pelan.
        """
        s = _StokPalsu('33', '47142.86')
        self.assertEqual(_porsi_nilai(s, D('33')), D('47142.86'))
        self.assertEqual(_porsi_nilai(s, D('99')), D('47142.86'))

    def test_porsi_sebagian_dibulatkan_half_up(self):
        # 47.142,86 x 10 / 33 = 14.285,7151515... -> 14.285,72
        s = _StokPalsu('33', '47142.86')
        self.assertEqual(_porsi_nilai(s, D('10')), D('14285.72'))

    def test_porsi_stok_kosong_nol(self):
        self.assertEqual(_porsi_nilai(_StokPalsu('0', '0'), D('5')), D('0'))

    def test_alokasi_jumlahnya_persis_total(self):
        """Rp10.000 dibagi tiga tidak boleh jadi Rp9.999,99."""
        bagian = alokasi_prorata({1: D('1'), 2: D('1'), 3: D('1')}, D('10000.00'))
        self.assertEqual(sum(bagian.values()), D('10000.00'))

    def test_alokasi_deterministik_saat_bobot_kembar(self):
        bobot = {7: D('5'), 3: D('5'), 9: D('5')}
        a = alokasi_prorata(dict(bobot), D('100.00'))
        b = alokasi_prorata(dict(reversed(list(bobot.items()))), D('100.00'))
        self.assertEqual(a, b)

    def test_alokasi_residual_ke_bobot_terbesar(self):
        bagian = alokasi_prorata({1: D('100'), 2: D('1')}, D('10.00'))
        self.assertEqual(sum(bagian.values()), D('10.00'))
        self.assertGreater(bagian[1], bagian[2])

    def test_alokasi_bobot_kosong_aman(self):
        self.assertEqual(alokasi_prorata({}, D('100.00')), {})
        self.assertEqual(alokasi_prorata({1: D('0')}, D('100.00')), {})


# =========================================================
# 2. INVARIANT — butuh data master
# =========================================================

class DasarInventoryTest(TestCase):
    """
    Isi _siapkan() dengan objek berikut, lalu hapus baris skipTest:

        self.pt, self.cv, self.ud     core.Entitas
        self.grup                     core.GrupBahan berisi ketiganya
        self.bahan_a, self.produk_jadi master.Produk
        self.tangki_pool              inventory.Tangki milik self.grup
        self.kemasan                  inventory.Kemasan (isi = 1.000)
        self.tanggal                  tanggal dalam periode TERBUKA

    Periode harus terbuka untuk KETIGA entitas, karena _periode_grup()
    memeriksa seluruh anggota grup.
    """

    def _siapkan(self):
        self.skipTest(
            'Isi DasarInventoryTest._siapkan() dengan fixture proyek ini. '
            'Selama belum diisi, uji invariant tidak berjalan.')

    def setUp(self):
        self._siapkan()

    # ---------- pembantu ----------

    def _isi_pool(self, entitas, produk, qty, harga):
        from inventory.services import setor_ke_pool, terima_raw
        nilai = D(qty) * D(harga)
        terima_raw(produk_id=produk.id, grup_bahan_id=self.grup.id,
                   entitas_id=entitas.id, qty=D(qty), nilai=nilai,
                   tanggal=self.tanggal, referensi='UJI',
                   idem_key=f'uji.terima.{entitas.id}.{produk.id}.{qty}')
        setor_ke_pool(produk_id=produk.id, grup_bahan_id=self.grup.id,
                      entitas_id=entitas.id, qty=D(qty),
                      tanggal=self.tanggal, referensi='UJI',
                      idem_key=f'uji.setor.{entitas.id}.{produk.id}.{qty}',
                      tangki_pool_id=self.tangki_pool.id)

    def _cek_invariant(self):
        from inventory.services import verifikasi_pool_bersih
        h = verifikasi_pool_bersih(self.grup.id)
        self.assertTrue(
            h['cocok'],
            f"invariant (2) melenceng {h['selisih']}: pool={h['nilai_pool']} "
            f"ditahan={h['nilai_ditahan']} posisi={h['total_posisi']}")


class UjiInvariantProduksi(DasarInventoryTest):

    def test_invariant_utuh_di_tengah_produksi(self):
        """
        REGRESI: dulu pakai_dari_pool() mengeluarkan nilai dari POOL tanpa
        ada yang mencatat, jadi invariant (2) SALAH sepanjang sesi
        berjalan. Sekarang nilainya parkir di NilaiDitahan dan verifikator
        ikut menghitungnya.
        """
        from inventory.services import pakai_dari_pool, sisa_ditahan

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._cek_invariant()

        _, nilai = pakai_dari_pool(
            produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
            qty=D('10'), tanggal=self.tanggal, referensi='BATCH-1',
            idem_key='uji.pakai.1', tangki_id=self.tangki_pool.id,
            sesi_ref='BATCH-1')

        self.assertEqual(sisa_ditahan(self.grup.id, 'BATCH-1'), nilai)
        self._cek_invariant()          # <-- inilah yang dulu gagal

    def test_hasil_tidak_boleh_melebihi_yang_diambil(self):
        """Mengembalikan lebih banyak dari yang diambil = menciptakan rupiah."""
        from inventory.services import hasil_ke_pool, pakai_dari_pool

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        pakai_dari_pool(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                        qty=D('10'), tanggal=self.tanggal, referensi='B2',
                        idem_key='uji.pakai.2',
                        tangki_id=self.tangki_pool.id, sesi_ref='B2')

        with self.assertRaises(ValidationError):
            hasil_ke_pool(produk_id=self.produk_jadi.id,
                          grup_bahan_id=self.grup.id, qty=D('9'),
                          nilai_masuk=D('99999.00'), tanggal=self.tanggal,
                          referensi='B2', idem_key='uji.hasil.2',
                          tangki_id=self.tangki_pool.id, sesi_ref='B2')

    def test_tutup_sesi_mengosongkan_parkiran(self):
        from inventory.services import (pakai_dari_pool, sisa_ditahan,
                                        tutup_sesi)

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        pakai_dari_pool(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                        qty=D('10'), tanggal=self.tanggal, referensi='B3',
                        idem_key='uji.pakai.3',
                        tangki_id=self.tangki_pool.id, sesi_ref='B3')
        tutup_sesi(grup_bahan_id=self.grup.id, sesi_ref='B3',
                   tanggal=self.tanggal, referensi='B3 gagal',
                   idem_key='uji.tutup.3')

        self.assertEqual(sisa_ditahan(self.grup.id, 'B3'), D('0'))
        self._cek_invariant()


class UjiInvariantOpname(DasarInventoryTest):

    def test_opname_lebih_pool_bernilai_menerbitkan_untung(self):
        """
        REGRESI: dulu nilai_penyesuaian menaikkan Stok.nilai tanpa baris
        klaim apa pun, jadi invariant (2) pecah persis sebesar angka itu.
        """
        from inventory.models import JenisKlaim, Lapis, MutasiKlaim, Stok
        from inventory.services import sesuaikan_stok

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        stok = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.POOL,
                                produk=self.bahan_a)

        sesuaikan_stok(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                       lapis=Lapis.POOL, qty_fisik=stok.qty + D('2'),
                       tanggal=self.tanggal, referensi='OPN-1',
                       idem_key='uji.opname.1',
                       tangki_id=self.tangki_pool.id,
                       nilai_penyesuaian=D('2000.00'))

        self.assertTrue(MutasiKlaim.objects
                        .filter(grup_bahan=self.grup,
                                jenis=JenisKlaim.UNTUNG).exists())
        self._cek_invariant()

    def test_opname_pool_menolak_entitas(self):
        from inventory.models import Lapis
        from inventory.services import sesuaikan_stok

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        with self.assertRaises(ValidationError):
            sesuaikan_stok(produk_id=self.bahan_a.id,
                           grup_bahan_id=self.grup.id, lapis=Lapis.POOL,
                           qty_fisik=D('5'), tanggal=self.tanggal,
                           referensi='OPN-2', idem_key='uji.opname.2',
                           tangki_id=self.tangki_pool.id,
                           entitas_id=self.pt.id)

    def test_opname_raw_memakai_harga_pemiliknya(self):
        """
        REGRESI: dulu porsi nilai dihitung dari rata-rata baris Stok yang
        ditumpangi beberapa entitas, lalu seluruhnya dibebankan ke satu
        entitas. PT yang beli murah menanggung rata-rata CV yang beli
        mahal.
        """
        from inventory.models import Lapis, SaldoEntitas, Stok
        from inventory.services import sesuaikan_stok, terima_raw

        terima_raw(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                   entitas_id=self.pt.id, qty=D('10'), nilai=D('10000.00'),
                   tanggal=self.tanggal, referensi='PO-1',
                   idem_key='uji.raw.pt')
        terima_raw(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                   entitas_id=self.cv.id, qty=D('10'), nilai=D('30000.00'),
                   tanggal=self.tanggal, referensi='PO-2',
                   idem_key='uji.raw.cv')

        stok = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.RAW,
                                produk=self.bahan_a)
        sesuaikan_stok(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                       lapis=Lapis.RAW, qty_fisik=stok.qty - D('1'),
                       tanggal=self.tanggal, referensi='OPN-3',
                       idem_key='uji.opname.3', entitas_id=self.pt.id)

        pt = SaldoEntitas.objects.get(stok=stok, entitas=self.pt)
        # 1 kg dari 10 kg senilai 10.000 -> 1.000, bukan rata-rata 2.000.
        self.assertEqual(pt.qty, D('9.000'))
        self.assertEqual(pt.nilai, D('9000.00'))


class UjiSusutPengepakan(DasarInventoryTest):

    def test_susut_kemas_tidak_menempel_ke_barang_jadi(self):
        """
        REGRESI: kelebihan curah dulu ikut masuk sebagai nilai barang
        jadi, jadi harga per pcs terkerek naik oleh susut -- bertentangan
        dengan "harga per satuan tetap" di models.py.
        """
        from inventory.models import JenisKlaim, Lapis, MutasiKlaim, Stok
        from inventory.services import klaim_kemasan

        self._isi_pool(self.pt, self.bahan_a, 100, 1000)

        klaim_kemasan(kemasan_id=self.kemasan.id, grup_bahan_id=self.grup.id,
                      entitas_id=self.pt.id, jumlah=D('10'),
                      tanggal=self.tanggal, referensi='KMS-1',
                      idem_key='uji.kemas.1',
                      tangki_pool_id=self.tangki_pool.id,
                      qty_curah_aktual=D('10.5'))

        jadi = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.JADI,
                                produk=self.kemasan.produk_kemasan)
        # 10 pcs @ 1 kg dari pool Rp1.000/kg -> Rp1.000/pcs, bukan Rp1.050.
        self.assertEqual(jadi.harga_rata.quantize(D('0.01')), D('1000.00'))
        self.assertTrue(
            MutasiKlaim.objects.filter(grup_bahan=self.grup,
                                       jenis=JenisKlaim.RUGI,
                                       entitas=self.pt).exists())
        self._cek_invariant()

    def test_jumlah_kemasan_wajib_utuh(self):
        from inventory.services import klaim_kemasan

        self._isi_pool(self.pt, self.bahan_a, 100, 1000)
        with self.assertRaises(ValidationError):
            klaim_kemasan(kemasan_id=self.kemasan.id,
                          grup_bahan_id=self.grup.id, entitas_id=self.pt.id,
                          jumlah=D('0.5'), tanggal=self.tanggal,
                          referensi='KMS-2', idem_key='uji.kemas.2',
                          tangki_pool_id=self.tangki_pool.id)


class UjiPenjagaLain(DasarInventoryTest):

    def test_bebankan_rugi_dua_kali_hanya_sekali(self):
        from inventory.services import bebankan_rugi, verifikasi_pool_bersih

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.cv, self.bahan_a, 10, 1000)

        awal = verifikasi_pool_bersih(self.grup.id)['total_posisi']
        for _ in range(2):
            bebankan_rugi(grup_bahan_id=self.grup.id, nilai=D('1000.00'),
                          tanggal=self.tanggal, referensi='UJI',
                          idem_key='uji.rugi.ganda')
        akhir = verifikasi_pool_bersih(self.grup.id)['total_posisi']
        self.assertEqual(akhir, awal - D('1000.00'))

    def test_entitas_bukan_anggota_ditolak(self):
        from inventory.services import terima_raw

        with self.assertRaises(ValidationError):
            terima_raw(produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
                       entitas_id=self.luar.id, qty=D('1'), nilai=D('100.00'),
                       tanggal=self.tanggal, referensi='PO-X',
                       idem_key='uji.raw.luar')

    def test_idem_key_kotor_ditolak(self):
        """
        idem_key dipakai sebagai prefiks. Karakter bebas membuat satu
        kunci bisa jadi awalan kunci lain, dan penjaga pembebanan ganda
        meloloskan pemanggilan kedua.
        """
        from inventory.services import pastikan_idem_bersih

        for buruk in ('a#b', 'a b', 'a/b', "a'b", 'x' * 65, ''):
            with self.assertRaises(ValidationError):
                pastikan_idem_bersih(buruk)
        # Bentuk yang dipakai produksi harus lolos apa adanya.
        for baik in ('setor.abc-123_x', 'sesi:12:pakai:34:0',
                     'sesi:12:rugi-susut'):
            self.assertEqual(pastikan_idem_bersih(baik), baik)