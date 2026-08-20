// src/features/produksi/composables/useSumberOptions.js

import { ref } from 'vue'
import { apiBatch, apiRawUntukProduksi } from '../api'

export function useSumberOptions() {
    const opsiRaw = ref([])
    const opsiBatch = ref([])
    const memuat = ref(false)

    async function muatOpsi(tangkiTujuanId = null) {
        memuat.value = true
        try {
            const [rawRes, batchRes] = await Promise.all([
                apiRawUntukProduksi.daftar(),
                apiBatch.tersedia(tangkiTujuanId)
            ])
            const rawData = Array.isArray(rawRes) ? rawRes : (rawRes.rincian || rawRes.results || [])
            const batchData = Array.isArray(batchRes) ? batchRes : (batchRes.results || [])

            opsiRaw.value = rawData.filter(r => Number(r.qty_kg) > 0)
            opsiBatch.value = batchData
        } catch (e) {
            console.error(e)
        } finally {
            memuat.value = false
        }
    }

    return { opsiRaw, opsiBatch, memuat, muatOpsi }
}
