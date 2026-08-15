import { ref } from 'vue'
import { apiBatch } from '../api'
import { STATUS_BATCH } from '../constants'
import { usePemeriksaanStore } from '@/stores/pemeriksaan'

export function useBatchDetail() {
    const detail = ref(null)
    const komposisi = ref(null)
    const memuat = ref(true)

    async function muatDetail(id) {
        memuat.value = true
        try {
            detail.value = await apiBatch.detail(id)

            // Komposisi (BOM) hanya ada maknanya jika dokumen sudah POSTED atau VOID
            if (detail.value.status === STATUS_BATCH.POSTED || detail.value.status === STATUS_BATCH.VOID) {
                komposisi.value = await apiBatch.komposisi(id)
            }
        } catch (e) {
            console.error('Gagal memuat detail batch:', e)
            throw e
        } finally {
            memuat.value = false
        }
    }

    async function batalkan(id, alasan) {
        try {
            const hasil = await apiBatch.void(id, alasan)
            usePemeriksaanStore().periksa() // Segarkan panel global
            await muatDetail(id) // Muat ulang detail agar status berubah jadi VOID
            return hasil
        } catch (e) {
            throw e // Dilempar ke komponen untuk dirender
        }
    }

    return { detail, komposisi, memuat, muatDetail, batalkan }
}