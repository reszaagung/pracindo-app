/**
 * features/produksi/composables/usePengukuran.js
 * ================================================
 * Pengukuran + catatan eksperimen. Keduanya APPEND-ONLY di backend
 * (API D: PUT/PATCH/DELETE -> 405, pola RiwayatAkses.save()).
 * Tidak ada fungsi ubah/hapus di file ini, dan itu disengaja — kalau
 * fungsinya tidak ada, tombolnya tidak akan pernah tidak sengaja dibuat.
 * Koreksi = entri BARU dengan `mengoreksi` menunjuk entri lama.
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { bacaError, errorPerField } from '@/utils/error'

export const TAHAP = [
    { nilai: 'PROSES', label: 'Proses' },
    { nilai: 'UJI', label: 'Hasil uji' },
]

export function usePengukuran() {
    const katalog = ref([])
    const daftarPengukuran = ref([])
    const daftarCatatan = ref([])
    const sedangProses = ref(false)
    const galat = ref('')
    const galatField = ref({})

    /**
     * Urutan katalog: terakhir-dipakai di depan. Ini yang membuat pencatatan
     * cukup dua ketukan — jenis yang baru saja dicatat hampir selalu jenis
     * berikutnya yang dicatat, jadi jarang perlu menggulir sama sekali.
     */
    const katalogTerurut = computed(() => {
        const terakhir = new Map()
        for (const p of daftarPengukuran.value) {
            const t = new Date(p.waktu).getTime()
            if (!terakhir.has(p.nama) || terakhir.get(p.nama) < t) terakhir.set(p.nama, t)
        }
        return [...katalog.value].sort(
            (a, b) => (terakhir.get(b.id) ?? 0) - (terakhir.get(a.id) ?? 0),
        )
    })

    /** Lini masa gabungan pengukuran + catatan, terbaru di atas. */
    const liniMasa = computed(() => {
        const dikoreksi = new Set(
            daftarPengukuran.value.map((p) => p.mengoreksi).filter(Boolean),
        )
        const baris = [
            ...daftarPengukuran.value.map((p) => ({
                kunci: `u${p.id}`, jenis: 'ukur', waktu: p.waktu, data: p,
                digantikan: dikoreksi.has(p.id),
            })),
            ...daftarCatatan.value.map((c) => ({
                kunci: `c${c.id}`, jenis: 'catatan', waktu: c.waktu, data: c,
                digantikan: false,
            })),
        ]
        return baris.sort((a, b) => new Date(b.waktu) - new Date(a.waktu))
    })

    const gagal = (err, pesan) => {
        galat.value = bacaError(err, pesan)
        galatField.value = errorPerField(err)
        return { success: false, message: galat.value, errors: galatField.value }
    }

    /** GET produksi/jenis-pengukuran/ — router resource, terpaginasi */
    const muatKatalog = async () => {
        try {
            const { data } = await api.get('produksi/jenis-pengukuran/')
            katalog.value = data.results ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat katalog jenis pengukuran.')
        }
    }

    /** GET produksi/sesi/{id}/pengukuran/ — @action, array polos */
    const muatPengukuran = async (sesiId) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`produksi/sesi/${sesiId}/pengukuran/`)
            daftarPengukuran.value = data ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat pengukuran.')
        } finally {
            sedangProses.value = false
        }
    }

    /** GET produksi/sesi/{id}/catatan/ — @action, array polos */
    const muatCatatan = async (sesiId) => {
        galat.value = ''
        try {
            const { data } = await api.get(`produksi/sesi/${sesiId}/catatan/`)
            daftarCatatan.value = data ?? []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat catatan eksperimen.')
        }
    }

    /**
     * POST produksi/sesi/{id}/pengukuran/
     * body { nama, nilai | nilai_teks, tahap, catatan?, mengoreksi? }
     * `nama` adalah id JenisPengukuran (FK), bukan teks bebas — satuan dan
     * ejaannya ikut dari katalog, jadi antar batch selalu sebanding.
     */
    const simpanPengukuran = async (sesiId, payload) => {
        sedangProses.value = true
        galat.value = ''
        galatField.value = {}
        try {
            const { data } = await api.post(`produksi/sesi/${sesiId}/pengukuran/`, payload)
            daftarPengukuran.value = [...daftarPengukuran.value, data]
            return { success: true, data }
        } catch (err) {
            return gagal(err, 'Gagal menyimpan pengukuran.')
        } finally {
            sedangProses.value = false
        }
    }

    /** POST produksi/sesi/{id}/catatan/ — body { teks } */
    const simpanCatatan = async (sesiId, payload) => {
        sedangProses.value = true
        galat.value = ''
        galatField.value = {}
        try {
            const { data } = await api.post(`produksi/sesi/${sesiId}/catatan/`, payload)
            daftarCatatan.value = [...daftarCatatan.value, data]
            return { success: true, data }
        } catch (err) {
            return gagal(err, 'Gagal menyimpan catatan.')
        } finally {
            sedangProses.value = false
        }
    }

    return {
        katalog, katalogTerurut, daftarPengukuran, daftarCatatan, liniMasa,
        sedangProses, galat, galatField,
        muatKatalog, muatPengukuran, muatCatatan,
        simpanPengukuran, simpanCatatan,
    }
}