import { ref, onMounted } from 'vue'
import { apiTangki } from '../api' // Sesuaikan path import api jika diperlukan

export function useTangkiList() {
  const loading = ref(true)
  const errorMsg = ref('')
  const tangkis = ref([])

  async function muatData() {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await apiTangki.daftar()
      const dataTangki = Array.isArray(res) ? res : (res?.results || [])

      tangkis.value = dataTangki.map(t => ({
        ...t,
        loadingSaldo: true,
        saldo: null
      }))

      // Load saldo masing-masing tangki secara paralel
      await Promise.all(
        tangkis.value.map(async (t) => {
          try {
            if (t.aktif) {
              t.saldo = await apiTangki.saldo(t.id)
            }
          } catch (e) {
            console.error(`Gagal memuat saldo tangki ${t.kode}`, e)
          } finally {
            t.loadingSaldo = false
          }
        })
      )
    } catch (e) {
      errorMsg.value = 'Gagal memuat data tangki. Periksa koneksi Anda.'
    } finally {
      loading.value = false
    }
  }

  // Otomatis muat data saat komponen pertama kali dibuka
  onMounted(() => {
    muatData()
  })

  return {
    loading,
    errorMsg,
    tangkis,
    muatData
  }
}
