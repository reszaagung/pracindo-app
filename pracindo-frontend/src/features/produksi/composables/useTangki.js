import { ref } from 'vue'
import { apiTangki } from '../api'

export function useTangki() {
  const tangkiList = ref([])
  const tangkiSaldo = ref(null)
  const memuat = ref(false)
  const memuatSimpan = ref(false)
  const galat = ref(null)

  const muatTangki = async (params = {}) => {
    memuat.value = true
    galat.value = null
    try {
      const res = await apiTangki.daftar(params)
      tangkiList.value = Array.isArray(res) ? res : (res.results || [])
      return tangkiList.value
    } catch (err) {
      galat.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      memuat.value = false
    }
  }

  const buatTangki = async (data) => {
    memuatSimpan.value = true
    galat.value = null
    try {
      const res = await apiTangki.buat(data)
      const dataBaru = res.data || res
      await muatTangki()
      return dataBaru
    } catch (err) {
      galat.value = err.response?.data?.pesan || err.message
      throw err
    } finally {
      memuatSimpan.value = false
    }
  }

  const muatSaldo = async (id) => {
    memuat.value = true
    try {
      const res = await apiTangki.saldo(id)
      tangkiSaldo.value = res.data || res
      return tangkiSaldo.value
    } catch (err) {
      galat.value = err.message
      throw err
    } finally {
      memuat.value = false
    }
  }

  return {
    tangkiList,
    tangkiSaldo,
    memuat,
    memuatSimpan,
    galat,
    muatTangki,
    buatTangki,
    muatSaldo
  }
}
