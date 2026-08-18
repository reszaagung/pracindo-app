import { ref } from 'vue'
import { apiTangki } from '../api'

export function useTangki() {
    const tangkiList = ref([])
    const memuat = ref(false)

    // State baru untuk indikator loading saat menyimpan tangki
    const memuatSimpan = ref(false)

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

    // FUNGSI BARU: Untuk menyimpan tangki langsung dari form Input Produksi
    async function buatTangki(payload) {
        memuatSimpan.value = true
        try {
            const tangkiBaru = await apiTangki.buat(payload)

            // Langsung masukkan ke list lokal agar otomatis muncul di dropdown form
            tangkiList.value.push(tangkiBaru)

            return tangkiBaru
        } catch (e) {
            console.error('Gagal membuat tangki:', e)
            throw e // Lempar error agar bisa ditangkap oleh catch di InputProduksi.vue
        } finally {
            memuatSimpan.value = false
        }
    }

    // Jangan lupa return memuatSimpan dan buatTangki
    return {
        tangkiList,
        memuat,
        memuatSimpan,
        muatTangki,
        buatTangki
    }
}
