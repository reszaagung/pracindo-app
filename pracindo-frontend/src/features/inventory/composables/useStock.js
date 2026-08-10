// src/features/inventory/composables/useStock.js
// Kontrak diverifikasi langsung dari inventory/views.py & serializers.py
// (pracindo_backend_v1) — lihat SPEK-BACKEND.md §3.x Inventory.
//
// nilai/harga_rata TIDAK ADA di serializer default (bukan null — memang
// tidak dideklarasikan) kecuali diminta dengan ?sisi=akunting DAN
// penggunanya benar boleh masuk modul akunting. Untuk lapis POOL, field
// itu tetap muncul tapi selalu null (POOL tidak pernah punya pemilik).

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
            const { data } = await api.get('inventory/stok/', { params })
            daftarStok.value = data.results || data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data stok.')
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
