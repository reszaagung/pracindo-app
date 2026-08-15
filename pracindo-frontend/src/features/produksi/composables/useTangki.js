import { ref } from 'vue'
import { apiTangki } from '../api'

export function useTangki() {
    const tangkiList = ref([])
    const memuat = ref(false)

    async function muatTangki() {
        memuat.value = true
        try {
            const res = await apiTangki.daftar({ aktif: true })

            // PERBAIKAN DI SINI: Ambil array 'results' jika bentuknya paginasi
            tangkiList.value = Array.isArray(res) ? res : (res.results || [])

        } catch (e) {
            console.error('Gagal memuat daftar tangki:', e)
        } finally {
            memuat.value = false
        }
    }

    return { tangkiList, memuat, muatTangki }
}