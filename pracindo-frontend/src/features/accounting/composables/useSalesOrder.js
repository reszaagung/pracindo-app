import { ref, computed } from 'vue'
import api from '@/utils/api'

export function useSalesOrder() {
    const listEntitas = ref([])
    const listPelanggan = ref([])
    const listProduk = ref([])

    const daftarSO = ref([])
    const isLoading = ref(false)

    const sedangProses = ref(false)
    const pesanError = ref('')
    const periodeDitutup = ref(false)
    const previewNomor = ref('Pilih entitas & tanggal')

    // Nomor dokumen dihasilkan CounterDokumen di server, per entitas per
    // bulan. Preview saja -- angka finalnya bisa bergeser kalau ada SO
    // lain terbit di antara preview dan submit.
    const muatPreviewNomor = async (entitasId, tanggal) => {
        if (!entitasId || !tanggal) {
            previewNomor.value = 'Pilih entitas & tanggal'
            return
        }
        try {
            const res = await api.get('sales-order/preview-nomor/', {
                params: { entitas: entitasId, tanggal },
            })
            previewNomor.value = res.data?.nomor || 'Otomatis saat disimpan'
        } catch {
            previewNomor.value = 'Otomatis saat disimpan'
        }
    }

    const muatDataMaster = async () => {
        try {
            // allSettled, bukan all.
            //
            // Promise.all gagal SELURUHNYA begitu satu request meleset --
            // satu 404 mengosongkan ketiga dropdown, dan pesannya tidak
            // menyebut yang mana. Dengan allSettled, yang berhasil tetap
            // terisi dan yang gagal disebut namanya.
            //
            // Entitas ada di app core, bukan master.
            const [rEnt, rPlg, rPrd] = await Promise.allSettled([
                api.get('core/entitas/'),
                api.get('master/pelanggan/'),
                api.get('master/produk/'),
            ])

            const ambil = (r) => (r.status === 'fulfilled'
                ? (r.value.data.results ?? r.value.data ?? [])
                : [])

            listEntitas.value = ambil(rEnt)
            listPelanggan.value = ambil(rPlg)
            listProduk.value = ambil(rPrd)

            const gagal = []
            if (rEnt.status === 'rejected') gagal.push('entitas')
            if (rPlg.status === 'rejected') gagal.push('pelanggan')
            if (rPrd.status === 'rejected') gagal.push('produk')
            if (gagal.length) {
                pesanError.value = `Master belum tersedia: ${gagal.join(', ')}.`
                console.error('Master SO gagal:', gagal)
            }
        } catch (error) {
            console.error("Gagal memuat master data SO:", error)
            pesanError.value = "Gagal memuat data master dari server."
        }
    }

    const fetchSO = async () => {
        isLoading.value = true
        pesanError.value = ''
        try {
            const response = await api.get('sales-order/')

            let rawData = Array.isArray(response.data) ? response.data
                : (response.data?.results || response.data?.data || [response.data])

            daftarSO.value = rawData.map(so => ({
                id: so.id,
                nomor_so: so.no_so,
                tanggal: so.tanggal,
                entitas: so.entitas ? { kode: so.entitas.kode } : { kode: 'UMUM' },
                pelanggan: so.pelanggan ? { nama: so.pelanggan.nama, kota: so.pelanggan.kota || '-' } : { nama: '-', kota: '-' },
                grand_total: so.grand_total ?? 0,
                status: so.status
            }))
        } catch (error) {
            console.error("Gagal mengambil data Sales Order:", error)
            pesanError.value = "Gagal memuat daftar Sales Order."
        } finally {
            isLoading.value = false
        }
    }

    const simpanSO = async (payload) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            const res = await api.post('sales-order/', payload)
            await fetchSO()
            return { success: true, data: res.data }
        } catch (error) {
            pesanError.value = error.response?.data?.detail || "Gagal menyimpan Sales Order."
            return { success: false }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        listEntitas, listPelanggan, listProduk, daftarSO,
        isLoading, sedangProses, pesanError, periodeDitutup,
        previewNomor, muatDataMaster, muatPreviewNomor, fetchSO, simpanSO
    }
}