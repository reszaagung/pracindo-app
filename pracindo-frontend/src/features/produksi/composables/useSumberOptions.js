import { ref } from 'vue'
import { apiRawUntukProduksi, apiBatch } from '../api'

export function useSumberOptions() {
  const opsiRaw = ref([])
  const opsiBatch = ref([])
  const memuatOpsi = ref(false)

  const extractArray = (res) => {
    if (Array.isArray(res)) return res
    if (Array.isArray(res?.rincian)) return res.rincian
    if (Array.isArray(res?.results)) return res.results
    if (Array.isArray(res?.data)) return res.data
    if (Array.isArray(res?.data?.rincian)) return res.data.rincian
    if (Array.isArray(res?.data?.results)) return res.data.results
    return []
  }

  const muatOpsi = async (tangkiId = null) => {
    memuatOpsi.value = true
    try {
      const [resRaw, resBatch] = await Promise.all([
        apiRawUntukProduksi.daftar(),
        apiBatch.tersedia(tangkiId)
      ])

      opsiRaw.value = extractArray(resRaw)
      opsiBatch.value = extractArray(resBatch)
    } catch (e) {
      console.error('Gagal memuat opsi bahan sumber:', e)
    } finally {
      memuatOpsi.value = false
    }
  }

  return { opsiRaw, opsiBatch, memuatOpsi, muatOpsi }
}
