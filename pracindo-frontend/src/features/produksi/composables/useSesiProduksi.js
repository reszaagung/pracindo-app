/**
 * features/produksi/composables/useSesiProduksi.js
 * =================================================
 * Kontrak diikat ke produksi/RANCANGAN-API.md — API (pracindo_backend_v1).
 * Tidak ada endpoint yang dikarang di sini — kalau sebuah path tidak ada
 * di Dokumen API, dia tidak boleh muncul di file ini.
 * PAGINASI (DRF "Aturan rumah"):
 *   router list  -> { count, next, previous, results }  ->  ambil .results
 *   @action      -> array / objek polos                 ->  JANGAN unwrap
 * DECIMAL dari DRF adalah STRING (COERCE_DECIMAL_TO_STRING). Semua
 * aritmetika di layar lewat Number()/parseFloat, tidak pernah langsung.
 */
import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError, errorPerField } from '@/utils/error'

export const STATUS_SESI = ['DRAFT', 'BERJALAN', 'SELESAI', 'GAGAL', 'BATAL']
export const JENIS_SESI = ['PRODUKSI', 'RND']

/** Status yang boleh dibatalkan API: batalkan/ hanya DRAFT. */
export const bolehBatal = (sesi) => sesi?.status === 'DRAFT'
export const bolehMulai = (sesi) => sesi?.status === 'DRAFT'
export const bolehTutup = (sesi) => sesi?.status === 'BERJALAN'

export function useSesiProduksi() {
    const daftarSesi = ref([])
    const sesi = ref(null)
    const daftarResep = ref([])
    const kapasitas = ref(null)
    const pratinjauKerugian = ref(null)
    const banding = ref(null)
    const daftarGrupBahan = ref([])
    const daftarEntitas = ref([])
    const daftarProduk = ref([])

    const sedangProses = ref(false)
    const galat = ref('')
    const galatField = ref({})

    const gagal = (err, pesan) => {
        galat.value = bacaError(err, pesan)
        galatField.value = errorPerField(err)
        return { success: false, message: galat.value, errors: galatField.value }
    }

    // =========================================================
    // SESI — jalur produksi rutin & R&D
    // =========================================================

    /** GET produksi/sesi/ — terpaginasi, unwrap .results */
    const muatSesi = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('produksi/sesi/', { params })
            daftarSesi.value = data.results ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat daftar sesi.')
        } finally {
            sedangProses.value = false
        }
    }

    /** GET produksi/sesi/{id}/ — objek polos */
    const muatDetail = async (id) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`produksi/sesi/${id}/`)
            sesi.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat sesi.')
        } finally {
            sedangProses.value = false
        }
    }

    /**
     * POST produksi/sesi/        (jenis_sesi PRODUKSI)
     * POST produksi/sesi/rnd/    (jenis_sesi RND)
     * Dua endpoint berbeda di API, bukan satu endpoint dengan flag.
     */
    const buatSesi = async (jenis, payload) => {
        sedangProses.value = true
        galat.value = ''
        galatField.value = {}
        const path = jenis === 'RND' ? 'produksi/sesi/rnd/' : 'produksi/sesi/'

        try {
            const { data } = await api.post(path, payload)
            return { success: true, data }
        } catch (err) {
            return gagal(err, 'Gagal membuat sesi.')
        } finally {
            sedangProses.value = false
        }
    }

    /**
     * Transisi status — SELALU lewat @action eksplisit, tidak pernah PATCH.
     *   mulai/       body { baris: [{bahan_id, qty_aktual, tangki_id?}] }
     *   selesaikan/  body { qty_hasil }
     *   gagalkan/    body { alasan, kategori_kegagalan }
     *   batalkan/    body { alasan }
     */
    const jalankanAksi = async (id, aksi, payload = {}) => {
        sedangProses.value = true
        galat.value = ''
        galatField.value = {}
        try {
            const { data } = await api.post(`produksi/sesi/${id}/${aksi}/`, payload)
            sesi.value = data
            return { success: true, data }
        } catch (err) {
            return gagal(err, `Gagal menjalankan aksi ${aksi}.`)
        } finally {
            sedangProses.value = false
        }
    }

    /**
     * GET produksi/sesi/{id}/pratinjau-kerugian/ — objek polos.
     * Nilai rupiah dihitung SERVER (tarif NilaiEkuivalen x qty). Frontend
     * tidak pernah menghitungnya sendiri — dua sumber kebenaran untuk angka
     * uang adalah cara paling halus untuk salah.
     */
    const muatPratinjauKerugian = async (id) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`produksi/sesi/${id}/pratinjau-kerugian/`)
            pratinjauKerugian.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat pratinjau kerugian.')
            pratinjauKerugian.value = null
        } finally {
            sedangProses.value = false
        }
    }

    /** GET produksi/sesi/banding/?ids=1,2,3 — objek polos, JANGAN unwrap */
    const muatBanding = async (ids = []) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('produksi/sesi/banding/', { params: { ids: ids.join(',') } })
            banding.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat pembanding batch.')
            banding.value = null
        } finally {
            sedangProses.value = false
        }
    }

    // =========================================================
    // RESEP & KAPASITAS
    // =========================================================

    /** GET produksi/resep/ — terpaginasi */
    const muatResep = async (params = {}) => {
        galat.value = ''
        try {
            const { data } = await api.get('produksi/resep/', { params })
            daftarResep.value = data.results ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat daftar resep.')
        }
    }

    /**
     * GET produksi/kapasitas/?grup=&produk=&tanggal= — objek polos.
     * Bukan sub-resource resep: hitung_kapasitas() bekerja dari grup_bahan +
     * produk_jadi, resepnya dipilih server lewat Resep.berlaku().
     */
    const muatKapasitas = async ({ grup, produk, tanggal }) => {
        kapasitas.value = null
        if (!grup || !produk) return
        try {
            const { data } = await api.get('produksi/kapasitas/', { params: { grup, produk, tanggal } })
            kapasitas.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal menghitung kapasitas.')
        }
    }

    // =========================================================
    // DATA ACUAN untuk dropdown form
    // Bukan endpoint produksi — dipakai apa adanya dari core/master.
    // =========================================================
    const muatAcuan = async () => {
        try {
            const [g, e, p] = await Promise.all([
                api.get('core/grup-bahan/'),
                api.get('core/entitas/', { params: { aktif: true } }),
                api.get('master/produk/', { params: { aktif: true } }),
            ])

            daftarGrupBahan.value = g.data.results ?? []
            daftarEntitas.value = e.data.results ?? []
            daftarProduk.value = p.data.results ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data acuan.')
        }
    }

    return {
        daftarSesi, sesi, daftarResep, kapasitas, pratinjauKerugian, banding,
        daftarGrupBahan, daftarEntitas, daftarProduk,
        sedangProses, galat, galatField,
        muatSesi, muatDetail, buatSesi, jalankanAksi,
        muatPratinjauKerugian, muatBanding,
        muatResep, muatKapasitas, muatAcuan,
    }
}