import { ref, reactive } from 'vue'
import { apiBatch } from '../api'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

export function useBatchList() {
    const baris = ref([])
    const memuat = ref(false)

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
            const params = Object.fromEntries(
                Object.entries(filter).filter(([_, v]) => v !== '' && v !== null)
            )
            const res = await apiBatch.daftar(params)
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
            await muatDaftar()
        } catch (e) {
            throw e
        }
    }

    async function postingDraft(id) {
        try {
            await apiBatch.posting(id)
            usePemeriksaanStore().periksa()
            await muatDaftar()
        } catch (e) {
            throw e
        }
    }

    return { baris, memuat, filter, muatDaftar, hapusDraft, postingDraft }
}
