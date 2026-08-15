// src/features/inventory/composables/useStock.js

import { ref } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

export function useStock() {
    const daftarStok = ref([])
    const stokDetail = ref(null)
    const daftarMutasi = ref([])
    const sedangProses = ref(false)
    const galat = ref('')

    const muatStok = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            // Arahkan ke endpoint spesifik berdasarkan Lapis yang dipilih
            if (params.lapis === 'ENTITAS') {
                const { data } = await api.get('inventory/mutasi/rekap/', { params })
                daftarStok.value = data.entitas || []
            } else if (params.lapis === 'POOL') {
                const { data } = await api.get('inventory/pool/', { params })
                daftarStok.value = data.rincian || []
            } else {
                daftarStok.value = []
            }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data persediaan stok.')
        } finally {
            sedangProses.value = false
        }
    }

    const muatStokDetail = async (id, params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get(`inventory/stok/${id}/`, { params })
            stokDetail.value = data
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat detail stok.')
        } finally {
            sedangProses.value = false
        }
    }

    const muatMutasi = async (params = {}) => {
        sedangProses.value = true
        galat.value = ''
        try {
            const { data } = await api.get('inventory/mutasi/', { params })
            daftarMutasi.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat riwayat mutasi.')
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarStok, stokDetail, daftarMutasi, sedangProses, galat,
        muatStok, muatStokDetail, muatMutasi,
    }
}