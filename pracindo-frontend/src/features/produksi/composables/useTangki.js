import { ref } from 'vue'
import { apiTangki } from '../api'

export function useTangki() {
    const tangkiList = ref([])
    const memuat = ref(false)
    const memuatSimpan = ref(false)

    async function muatTangki() {
        memuat.value = true
        try {
            const res = await apiTangki.daftar({ aktif: true })
            tangkiList.value = Array.isArray(res) ? res : (res.results || [])
        } catch (e) {
            console.error('Gagal memuat daftar tangki:', e)
        } finally {
            memuat.value = false
        }
    }

    async function buatTangki(payload) {
        memuatSimpan.value = true
        try {
            const tangkiBaru = await apiTangki.buat(payload)
            tangkiList.value.push(tangkiBaru)
            return tangkiBaru
        } catch (e) {
            console.error('Gagal membuat tangki:', e)
            throw e
        } finally {
            memuatSimpan.value = false
        }
    }

    return {
        tangkiList,
        memuat,
        memuatSimpan,
        muatTangki,
        buatTangki
    }
}
