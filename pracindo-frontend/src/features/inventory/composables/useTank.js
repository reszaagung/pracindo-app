// src/features/inventory/composables/useTank.js
// GET inventory/tangki/ — terbuka untuk GUDANG, PRODUKSI, AKUNTING (+
// Supervisor). Lihat SPEK-BACKEND.md §3.x Inventory.

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useTank() {
    const daftarTangki = ref([])
    const sedangProses = ref(false)
    const galat = ref('')

    const muatTangki = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/tangki/', { params })
            daftarTangki.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data tangki.')
        } finally {
            sedangProses.value = false
        }
    }

    return { daftarTangki, sedangProses, galat, muatTangki }
}
