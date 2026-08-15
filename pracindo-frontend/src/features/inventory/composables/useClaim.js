// src/features/inventory/composables/useClaim.js

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useClaim() {
    const posisiKlaim = ref([])
    const isiPool = ref(null)
    const sedangProses = ref(false)
    const galat = ref('')

    const muatPosisiKlaim = async (grup) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/posisi-klaim/', { params: { grup } })
            posisiKlaim.value = data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat posisi klaim.')
        } finally {
            sedangProses.value = false
        }
    }

    const muatIsiPool = async (grup) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/pool/', { params: { grup } })
            isiPool.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat isi pool.')
        } finally {
            sedangProses.value = false
        }
    }

    const kirimAksi = async (url, payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.post(url, payload)
            return { success: true, data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal menyimpan.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    const setorKePool = (payload) => kirimAksi('inventory/setor-ke-pool/', payload)
    const klaimHasil = (payload) => kirimAksi('inventory/klaim-hasil/', payload)
    const opname = (payload) => kirimAksi('inventory/pemeriksaan/', payload)

    return {
        posisiKlaim, isiPool, sedangProses, galat,
        muatPosisiKlaim, muatIsiPool, setorKePool, klaimHasil, opname,
    }
}