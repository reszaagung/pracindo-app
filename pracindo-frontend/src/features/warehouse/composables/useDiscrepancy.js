// src/features/warehouse/composables/useDiscrepancy.js
// Kontrak diverifikasi dari warehouse/views.py & serializers.py — lihat
// SPEK-BACKEND.md §3.3. Composable ini SENGAJA tidak pernah mengirim
// ?sisi=akunting — ini layar gudang, uang bukan urusannya.

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useDiscrepancy() {
    const daftarSelisih = ref([])
    const daftarTerbuka = ref([])
    const sedangProses = ref(false)
    const galat = ref('')

    const muatSelisih = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/laporan-selisih/', { params })
            daftarSelisih.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat laporan selisih.')
        } finally {
            sedangProses.value = false
        }
    }

    /** GET .../terbuka/ mengembalikan array polos, BUKAN {results}. */
    const muatTerbuka = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('warehouse/laporan-selisih/terbuka/', { params })
            daftarTerbuka.value = data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat klaim terbuka.')
        } finally {
            sedangProses.value = false
        }
    }

    const buatLaporanManual = async (payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.post('warehouse/laporan-selisih/', payload)
            return { success: true, data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal membuat laporan selisih.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    const ajukan = async (id, catatan = '') => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.post(`warehouse/laporan-selisih/${id}/ajukan/`, { catatan })
            return { success: true, data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal mengajukan klaim ke suplier.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarSelisih, daftarTerbuka, sedangProses, galat,
        muatSelisih, muatTerbuka, buatLaporanManual, ajukan,
    }
}
