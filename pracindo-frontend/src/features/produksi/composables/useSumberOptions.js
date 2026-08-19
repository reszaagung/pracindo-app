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

            opsiRaw.value = rawRes.filter(r => Number(r.saldo_qty) > 0)
            opsiBatch.value = batchRes
        } catch (e) {
            console.error('Gagal memuat opsi sumber:', e)
        } finally {
            memuat.value = false
        }
    }

    return { opsiRaw, opsiBatch, memuat, muatOpsi }
}
