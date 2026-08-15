import { ref, reactive } from 'vue'
import { apiBatch } from '../api'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

export function useBatchList() {
    const baris = ref([])
    const memuat = ref(false)

    // Parameter pencarian yang sesuai dengan backend
    const filter = reactive({
        tangki: '',
        jenis: '',
        status: '',
        dari: '',
        sampai: ''
    })

    async function muatDaftar() {
        memuat.value = true
        try {
            // Membersihkan parameter kosong agar URL rapi
            const params = Object.fromEntries(
                Object.entries(filter).filter(([_, v]) => v !== '' && v !== null)
            )

            const res = await apiBatch.daftar(params)
            // Menyesuaikan kalau backend pakai paginasi (res.results) atau array langsung
            baris.value = Array.isArray(res) ? res : (res.results || [])
        } catch (e) {
            console.error('Gagal memuat riwayat batch:', e)
        } finally {
            memuat.value = false
        }
    }

    async function hapusDraft(id) {
        try {
            await apiBatch.hapus(id)
            await muatDaftar() // Segarkan tabel setelah hapus
        } catch (e) {
            throw e // Biarkan komponen menangkap galatnya
        }
    }

    async function postingDraft(id) {
        try {
            await apiBatch.posting(id)
            usePemeriksaanStore().periksa() // Beritahu global store bahwa mutasi terjadi
            await muatDaftar()
        } catch (e) {
            throw e
        }
    }

    return { baris, memuat, filter, muatDaftar, hapusDraft, postingDraft }
}