// src/features/warehouse/composables/usePackageReceipt.js
import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function usePackageReceipt() {
    const daftarPOKemasan = ref([])
    const daftarPenerimaan = ref([])
    const ringkasan = ref(null)
    const sedangProses = ref(false)
    const galat = ref('')

    // 1. Memuat daftar PO Kemasan (Memakai endpoint utama + filter)
    const muatPOKemasan = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/po-siap-terima/', {
                params: { kategori: 'kemasan', ...params }
            })
            daftarPOKemasan.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat PO Kemasan siap terima.')
        } finally {
            sedangProses.value = false
        }
    }

    // 2. Memuat riwayat daftar penerimaan kemasan (Memakai endpoint utama + filter)
    const muatPenerimaan = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/penerimaan/', {
                params: { kategori: 'kemasan', ...params }
            })
            daftarPenerimaan.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat daftar penerimaan kemasan.')
        } finally {
            sedangProses.value = false
        }
    }

    // 3. Memuat detail/ringkasan satu dokumen penerimaan kemasan
    const muatRingkasan = async (id) => {
        if (!id || id === 'undefined' || id === 'null') {
            ringkasan.value = null
            return
        }
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`warehouse/penerimaan/${id}/ringkasan/`)
            ringkasan.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat detail ringkasan kemasan.')
        } finally {
            sedangProses.value = false
        }
    }

    // 4. Menyimpan data penerimaan
    const simpanPenerimaan = async (payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const response = await api.post('warehouse/penerimaan/', payload)
            return { success: true, data: response.data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal menyimpan penerimaan kemasan.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarPOKemasan,
        daftarPenerimaan,
        ringkasan,
        sedangProses,
        galat,
        muatPOKemasan,
        muatPenerimaan,
        muatRingkasan,
        simpanPenerimaan,
    }
}
