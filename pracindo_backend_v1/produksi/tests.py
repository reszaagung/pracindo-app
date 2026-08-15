"""
Uji produksi — produksi/tests.py

Yang diuji di sini bukan "apakah fungsinya jalan", melainkan "apakah
invariant tetap lurus setelah fungsinya jalan". Modul ini seluruh
nilainya bergantung pada satu persamaan:

    SUM(PosisiKlaim.nilai_bersih) == SUM(Stok.nilai) lapis POOL

Kalau itu melenceng, tidak ada error yang muncul. Laporan tetap terbit,
angkanya saja yang salah. Karena itu setiap uji di bawah diakhiri
pemeriksaan invariant, bukan hanya pemeriksaan hasil.

Skenario utama memakai angka dari kesepakatan:
    A 10 kg @ Rp1.000 = Rp10.000
    B 20 kg @ Rp1.500 = Rp30.000
    C  5 kg @ Rp2.000 = Rp10.000
    ------------------------------
       35 kg             Rp50.000
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.test import TestCase

from inventory.models import Lapis, PosisiKlaim, Stok
from inventory.services import (
    klaim_hasil, setor_ke_pool, terima_raw, verifikasi_pool_bersih,
)

from .models import JenisSesi, Resep, ResepItem, SesiProduksi, StatusSesi
from . import services

D = Decimal


class DasarProduksiTest(TestCase):
    """
    Kerangka bersama. `_siapkan()` diisi sesuai model core/master di
    proyek ini -- kolom Entitas, GrupBahan, Produk, dan Satuan berbeda
    antar cabang, jadi sengaja tidak ditebak di sini.
    """

    def _siapkan(self):
        """
        Isi dengan pabrik objek proyek ini, lalu hapus skipTest.

            self.pt, self.cv, self.ud       core.Entitas
            self.grup                       core.GrupBahan berisi ketiganya
            self.bahan_a/_b/_c              master.Produk
            self.produk_jadi                master.Produk
            self.tangki_1/_2/_hasil         inventory.Tangki milik self.grup
            self.resep + ResepItem A/B/C    hasil_per_batch = 35
            self.operator                   user
            self.tanggal                    dalam periode TERBUKA

        CATATAN untuk test_rendemen_dihitung_atas_target_bukan_kilogram:
        butuh resep yang MEMEKATKAN -- hasil_per_batch berbeda dari total
        kg bahan, mis. 35 kg bahan -> 30 unit. Selama resep uji memakai
        35 kg -> 35 unit, bug pembagi rendemen tidak akan pernah terlihat.

        CATATAN setelah patch inventory: NilaiEkuivalen tidak lagi dipakai
        setor_ke_pool() selama RAW punya dasar biaya. Nilai pool sekarang
        SAMA dengan harga perolehan, jadi test_nilai_bahan_terkumpul_persis
        benar tanpa perlu menyamakan tarif ekuivalen secara manual.
        """
        self.skipTest(
            'Isi DasarProduksiTest._siapkan() dengan fixture proyek ini. '
            'Selama belum diisi, seluruh berkas uji ini tidak berjalan.'
        )

    def setUp(self):
        self._siapkan()

    # -----------------------------------------------------
    def _isi_pool(self, entitas, bahan, qty, harga, tangki=None):
        """Terima RAW lalu setor ke pool, supaya klaim ikut terbentuk."""
        nilai = D(qty) * D(harga)
        terima_raw(
            produk_id=bahan.id, grup_bahan_id=self.grup.id,
            entitas_id=entitas.id, qty=qty, nilai=nilai,
            tanggal=self.tanggal, referensi='PO-UJI',
            idem_key=f'uji:terima:{entitas.id}:{bahan.id}',
        )
        setor_ke_pool(
            produk_id=bahan.id, grup_bahan_id=self.grup.id,
            entitas_id=entitas.id, qty=qty, tanggal=self.tanggal,
            referensi='SETOR-UJI', tangki_pool_id=tangki.id if tangki else None,
            idem_key=f'uji:setor:{entitas.id}:{bahan.id}',
        )

    def _nilai_pool(self):
        return (Stok.objects
                .filter(grup_bahan=self.grup, lapis=Lapis.POOL)
                .aggregate(t=Sum('nilai'))['t'] or D('0'))

    def _cek_invariant(self, pesan=''):
        hasil = verifikasi_pool_bersih(self.grup.id)
        self.assertTrue(
            hasil['cocok'],
            f'Invariant (2) melenceng {hasil["selisih"]}. {pesan}\n{hasil}'
        )


class AliranNilaiTest(DasarProduksiTest):

    def test_nilai_bahan_terkumpul_persis(self):
        """35 kg dari tiga bahan harus bernilai Rp50.000, tidak lebih."""
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        self.assertEqual(self._nilai_pool(), D('50000.00'))
        self._cek_invariant('setelah setoran')

    def test_susut_menghapus_nilai_harga_tetap(self):
        """
        35 kg / Rp50.000 masuk. Hasil 33 kg -> Rp47.142,86.
        Susut 2 kg -> Rp2.857,14 dibebankan ke pemegang hak.
        Harga per kg TETAP Rp1.428,57, tidak terkerek naik.
        """
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
            tangki_hasil_id=self.tangki_hasil.id,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        sesi.refresh_from_db()
        self.assertEqual(sesi.nilai_input, D('50000.00'))

        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=33,
                                 abaikan_susut=True)
        sesi.refresh_from_db()

        self.assertEqual(sesi.nilai_hasil, D('47142.86'))
        self.assertEqual(sesi.nilai_kerugian, D('2857.14'))
        # Harga tidak berubah: 47.142,86 / 33 = 1.428,57
        self.assertEqual(sesi.harga_hasil_per_satuan, D('1428.5715'))
        self.assertEqual(self._nilai_pool(), D('47142.86'))
        # Hasil + susut harus sama persis dengan yang keluar.
        self.assertEqual(sesi.nilai_hasil + sesi.nilai_kerugian,
                         sesi.nilai_input)
        self._cek_invariant('setelah produksi bersusut')

    def test_klaim_memakai_porsi_tangki_saat_itu(self):
        """
        Tangki berisi 33 kg senilai Rp47.142,86. Mengambil 10 kg
        mengurangi hak 47.142,86 x 10/33 = 14.285,7151... -> Rp14.285,72
        (ROUND_HALF_UP).

        Bukan 10 x tarif bulat: 10.000 x 1,5 = 15.000 akan menciptakan
        Rp714 dari udara.
        """
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
            tangki_hasil_id=self.tangki_hasil.id,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=33,
                                 abaikan_susut=True)

        _, _, klaim, posisi = klaim_hasil(
            produk_id=self.produk_jadi.id, grup_bahan_id=self.grup.id,
            entitas_id=self.pt.id, qty=10, tanggal=self.tanggal,
            referensi='AMBIL-UJI', idem_key='uji:ambil:1',
            tangki_pool_id=self.tangki_hasil.id,
        )
        self.assertEqual(klaim.nilai, D('-14285.72'))
        self._cek_invariant('setelah pengambilan')

    def test_susut_dan_hasil_selalu_berjumlah_nilai_input(self):
        """
        Rendemen yang tidak habis dibagi (33/35) selalu menyisakan
        pecahan. Kalau hasil dan susut dibulatkan sendiri-sendiri,
        jumlahnya meleset dari nilai_input dan invariant melenceng.
        Susut harus dihitung sebagai SELISIH, bukan dibulatkan terpisah.
        """
        for qty, harga in ((7, 1234.56), (11, 987.65), (3, 1111.11)):
            self._isi_pool(self.pt, self.bahan_a, qty, harga)

        sesi = services.buat_sesi_rnd(
            grup_bahan_id=self.grup.id, produk_jadi_id=self.produk_jadi.id,
            qty_target=21, tanggal=self.tanggal, user=self.operator,
            baris=[{'bahan_id': self.bahan_a.id, 'qty_rencana': 21}],
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=19)
        sesi.refresh_from_db()

        self.assertEqual(sesi.nilai_hasil + sesi.nilai_kerugian,
                         sesi.nilai_input)
        self._cek_invariant('setelah rendemen berpecahan')

    def test_menguras_habis_tidak_menyisakan_receh(self):
        """
        Pembulatan proporsional biasanya meninggalkan Rp0,01 di baris
        kosong. Kalau itu terjadi, invariant melenceng sedikit demi
        sedikit dan tidak ada yang sadar sampai berbulan-bulan.
        """
        self._isi_pool(self.pt, self.bahan_a, 3, 333.33)

        klaim_hasil(
            produk_id=self.bahan_a.id, grup_bahan_id=self.grup.id,
            entitas_id=self.pt.id, qty=3, tanggal=self.tanggal,
            referensi='KURAS', idem_key='uji:kuras',
        )
        stok = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.POOL,
                                produk=self.bahan_a)
        self.assertEqual(stok.qty, D('0.000'))
        self.assertEqual(stok.nilai, D('0.00'))
        self._cek_invariant('setelah pool terkuras habis')


class KerugianTest(DasarProduksiTest):

    def test_sesi_gagal_membebankan_kerugian_nyata(self):
        """
        Sebelumnya nilai_kerugian selalu nol karena tarifnya di-hardcode,
        dan tidak ada baris klaim yang terbit sama sekali.
        """
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.gagalkan_sesi(sesi_id=sesi.id, alasan='Karamelisasi',
                               kategori='PROSES')
        sesi.refresh_from_db()

        self.assertEqual(sesi.status, StatusSesi.GAGAL)
        self.assertEqual(sesi.nilai_kerugian, D('50000.00'))
        self._cek_invariant('setelah sesi gagal')

    def test_kerugian_dibagi_sebanding_hak(self):
        """PT menyetor 3/4, CV 1/4 -> beban kerugian 3:1."""
        self._isi_pool(self.pt, self.bahan_a, 30, 1000)
        self._isi_pool(self.cv, self.bahan_a, 10, 1000)

        sesi = services.buat_sesi_rnd(
            grup_bahan_id=self.grup.id, produk_jadi_id=self.produk_jadi.id,
            qty_target=40, tanggal=self.tanggal, user=self.operator,
            hasil_masuk_pool=False,
            baris=[{'bahan_id': self.bahan_a.id, 'qty_rencana': 40}],
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=38)

        pt = PosisiKlaim.objects.get(entitas=self.pt, grup_bahan=self.grup)
        cv = PosisiKlaim.objects.get(entitas=self.cv, grup_bahan=self.grup)
        self.assertEqual(pt.total_rugi, D('30000.00'))
        self.assertEqual(cv.total_rugi, D('10000.00'))
        self._cek_invariant('setelah R&D di luar pool')

    def test_pembulatan_kerugian_tidak_menguap(self):
        """Rp10.000,01 dibagi tiga harus tetap berjumlah Rp10.000,01."""
        for ent, qty in ((self.pt, 10), (self.cv, 10), (self.ud, 10)):
            self._isi_pool(ent, self.bahan_a, qty, 333.3337)

        awal = verifikasi_pool_bersih(self.grup.id)['total_posisi']
        sesi = services.buat_sesi_rnd(
            grup_bahan_id=self.grup.id, produk_jadi_id=self.produk_jadi.id,
            qty_target=30, tanggal=self.tanggal, user=self.operator,
            hasil_masuk_pool=False,
            baris=[{'bahan_id': self.bahan_a.id, 'qty_rencana': 30}],
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=28)

        akhir = verifikasi_pool_bersih(self.grup.id)['total_posisi']
        self.assertEqual(akhir, awal - sesi.nilai_input)
        self._cek_invariant('setelah pembagian kerugian berpembulatan')


class PenjagaTest(DasarProduksiTest):

    def test_bahan_lintas_dua_tangki_terhitung_penuh(self):
        """
        Bug lama: dict comprehension membuat tangki kedua tertimpa, jadi
        kapasitas hanya menghitung satu tangki.
        """
        self._isi_pool(self.pt, self.bahan_a, 6, 1000, tangki=self.tangki_1)
        self._isi_pool(self.cv, self.bahan_a, 4, 1000, tangki=self.tangki_2)

        potongan = services.alokasi_tangki(self.grup.id, self.bahan_a.id, 10)
        self.assertEqual(len(potongan), 2)
        self.assertEqual(sum(q for _, q in potongan), D('10.000'))

    def test_bahan_nol_dilewati_bukan_menggagalkan_sesi(self):
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
        )
        services.mulai_sesi(sesi_id=sesi.id,
                            qty_aktual={self.bahan_c.id: 0})
        sesi.refresh_from_db()

        self.assertEqual(sesi.status, StatusSesi.BERJALAN)
        self.assertEqual(sesi.nilai_input, D('40000.00'))
        self._cek_invariant('setelah satu bahan dilewati')

    def test_mulai_dua_kali_tidak_menarik_dua_kali(self):
        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        sesi = services.buat_sesi_rnd(
            grup_bahan_id=self.grup.id, produk_jadi_id=self.produk_jadi.id,
            qty_target=10, tanggal=self.tanggal, user=self.operator,
            baris=[{'bahan_id': self.bahan_a.id, 'qty_rencana': 5}],
        )
        services.mulai_sesi(sesi_id=sesi.id)
        with self.assertRaises(ValidationError):
            services.mulai_sesi(sesi_id=sesi.id)

        stok = Stok.objects.get(grup_bahan=self.grup, lapis=Lapis.POOL,
                                produk=self.bahan_a)
        self.assertEqual(stok.qty, D('5.000'))
        self._cek_invariant('setelah percobaan mulai ganda')

    def test_susut_di_luar_batas_resep_ditolak(self):
        """susut_wajar 5% -> hasil di bawah 33,25 harus ditolak."""
        self.resep.susut_wajar = D('0.0500')
        self.resep.save(update_fields=['susut_wajar'])

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        with self.assertRaises(ValidationError):
            services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=25)

        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=34)
        self._cek_invariant('setelah susut dalam batas')

    def test_pool_tidak_cukup_ditolak_dengan_pesan_jelas(self):
        self._isi_pool(self.pt, self.bahan_a, 2, 1000)
        with self.assertRaises(ValidationError) as ctx:
            services.alokasi_tangki(self.grup.id, self.bahan_a.id, 10)
        self.assertIn('hanya berisi', str(ctx.exception))


# =========================================================
# REGRESI HAK AKSES
# =========================================================
# Bug "modul produksi mati total" tidak menghasilkan error apa pun di
# log, hanya 403. Jenis bug yang kembali diam-diam setiap kali ada yang
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
        harus membacanya dari dirinya sendiri, supaya @api_view -- yang
        tidak bisa diberi atribut kelas -- ikut lolos.
        """
        from produksi.permissions import ModulProduksi
        req = self._request(self._UserPalsu())
        self.assertTrue(ModulProduksi().has_permission(req, object()))

    def test_modul_lain_tetap_ditolak(self):
        from produksi.permissions import ModulProduksi
        req = self._request(self._UserPalsu(modul=('inventory',)))
        self.assertFalse(ModulProduksi().has_permission(req, object()))

    def test_anonim_ditolak(self):
        from produksi.permissions import ModulProduksi

        class Anon:
            is_authenticated = False

        self.assertFalse(
            ModulProduksi().has_permission(self._request(Anon()), object()))


# =========================================================
# REGRESI PARKIRAN NILAI (WIP)
# =========================================================

class ParkiranNilaiTest(DasarProduksiTest):

    def test_invariant_utuh_saat_sesi_masih_berjalan(self):
        """
        Sebelum ada NilaiDitahan, invariant (2) SALAH sepanjang sesi
        berjalan -- verifikator nightly berteriak palsu setiap ada batch
        yang belum ditutup, lalu orang berhenti mempercayainya.
        """
        from inventory.services import sisa_ditahan

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
            tangki_hasil_id=self.tangki_hasil.id,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        sesi.refresh_from_db()

        self.assertEqual(sisa_ditahan(self.grup.id, sesi.nomor),
                         sesi.nilai_input)
        self._cek_invariant('saat sesi masih BERJALAN')

    def test_parkiran_kosong_setelah_sesi_selesai(self):
        from inventory.services import sisa_ditahan

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
            tangki_hasil_id=self.tangki_hasil.id,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=33,
                                 abaikan_susut=True)

        self.assertEqual(sisa_ditahan(self.grup.id, sesi.nomor), D('0'))
        self._cek_invariant('setelah sesi ditutup')

    def test_parkiran_kosong_setelah_sesi_gagal(self):
        from inventory.services import sisa_ditahan

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=35, tanggal=self.tanggal, user=self.operator,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.gagalkan_sesi(sesi_id=sesi.id, alasan='Karamelisasi',
                               kategori='PROSES')

        self.assertEqual(sisa_ditahan(self.grup.id, sesi.nomor), D('0'))
        self._cek_invariant('setelah sesi gagal')

    def test_rendemen_dihitung_atas_target_bukan_kilogram(self):
        """
        Resep yang memekatkan: 35 kg bahan -> 30 unit target.
        Hasil 29 unit adalah susut 3,3%, bukan 17,1%.

        Butuh resep dengan hasil_per_batch yang membuat total kg bahan
        BERBEDA dari qty_target -- lihat catatan di _siapkan().
        """
        if self.resep.hasil_per_batch == sum(
                i.qty for i in self.resep.item.all()):
            self.skipTest(
                'Resep uji masih 35 kg -> 35 unit. Bug pembagi rendemen '
                'tidak akan terlihat sampai resepnya memekatkan.')

        self._isi_pool(self.pt, self.bahan_a, 10, 1000)
        self._isi_pool(self.pt, self.bahan_b, 20, 1500)
        self._isi_pool(self.pt, self.bahan_c, 5, 2000)

        sesi = services.buat_sesi_produksi(
            grup_bahan_id=self.grup.id, resep_id=self.resep.id,
            qty_target=30, tanggal=self.tanggal, user=self.operator,
            tangki_hasil_id=self.tangki_hasil.id,
        )
        services.mulai_sesi(sesi_id=sesi.id)
        services.selesaikan_sesi(sesi_id=sesi.id, qty_hasil=29)
        sesi.refresh_from_db()

        # 29/30 -> nilai terbawa 96,67% dari Rp50.000
        self.assertEqual(sesi.nilai_hasil, D('48333.33'))
        self.assertEqual(sesi.nilai_kerugian, D('1666.67'))
        self._cek_invariant('setelah rendemen atas target')