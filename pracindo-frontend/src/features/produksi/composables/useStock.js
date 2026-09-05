// src/features/produksi/composables/useStock.js
import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useStock() {
    const daftarStok = ref([])
    const sedangProses = ref(false)
    const galat = ref('')

    const muatStok = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('v1/produksi/pool/', { params })
            daftarStok.value = data.rincian || data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data stok.')
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarStok,
        sedangProses,
        galat,
        muatStok
    }
}

export function useMutasi() {
    const sedangMemproses = ref(false)
    const galatMutasi = ref('')
    const suksesMutasi = ref(false)

    const tarikStokPool = async (payload) => {
        sedangMemproses.value = true
        galatMutasi.value = ''
        suksesMutasi.value = false
        try {
            await api.post('v1/produksi/mutasi/tarik/', payload)
            suksesMutasi.value = true
        } catch (err) {
            galatMutasi.value = bacaError(err, 'Gagal mencatat pemakaian stok.')
        } finally {
            sedangMemproses.value = false
        }
    }

    return {
        tarikStokPool,
        sedangMemproses,
        galatMutasi,
        suksesMutasi
    }
}