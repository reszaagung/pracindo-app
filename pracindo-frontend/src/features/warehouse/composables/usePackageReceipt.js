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

    // 1. Memuat daftar PO khusus kemasan yang siap masuk gudang
    const muatPOKemasan = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/po-kemasan-siap-terima/', { params })
            daftarPOKemasan.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat PO Kemasan siap terima.')
        } finally {
            sedangProses.value = false
        }
    }

    // 2. Memuat riwayat daftar penerimaan kemasan
    const muatPenerimaan = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/penerimaan-kemasan/', { params })
            daftarPenerimaan.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat daftar penerimaan kemasan.')
        } finally {
            sedangProses.value = false
        }
    }

    // 3. Memuat detail/ringkasan satu dokumen penerimaan kemasan
    const muatRingkasan = async (id) => {
        // PERLINDUNGAN: Cegah request API jika ID tidak valid/undefined (menghindari Error 500)
        if (!id || id === 'undefined' || id === 'null') {
            console.warn('muatRingkasan dibatalkan: ID kemasan tidak valid atau kosong.')
            ringkasan.value = null
            return
        }

        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`warehouse/penerimaan-kemasan/${id}/ringkasan/`)
            ringkasan.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat detail ringkasan kemasan.')
        } finally {
            sedangProses.value = false
        }
    }

    // 4. Menyimpan data penerimaan (langsung simpan walau ada selisih)
    const simpanPenerimaan = async (payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const response = await api.post('warehouse/penerimaan-kemasan/', payload)
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
