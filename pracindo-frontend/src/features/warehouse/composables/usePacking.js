// src/features/warehouse/composables/usePacking.js
import { ref } from 'vue'
import { warehouseApi } from '../api' // Memanggil dari api.js lokal modul warehouse
import { bacaError } from '@/utils/error'

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([])

    const sedangProses = ref(false)
    const galat = ref('')

    // Menyimpan hasil kalkulasi COGS dari Backend
    const pratinjau = ref({
        valid: false,
        qty_kg: 0,
        harga_rata: 0,
        nilai_hpp: 0,
        sisa_qty_batch: 0,
        pesan: ''
    })

    // --- INI ADALAH VERSI FINAL muatMasterData ---
    const muatMasterData = async () => {
        sedangProses.value = true
        galat.value = ''
        try {
            // Memanggil endpoint API dari warehouseApi secara bersamaan
            const [resEntitas, resKemasan, resBatch] = await Promise.all([
                warehouseApi.getEntitasAktif(),
                warehouseApi.getKemasanAktif(),
                warehouseApi.getBatchTersedia()
            ])

            daftarEntitas.value = resEntitas.data?.results || resEntitas.data || []
            daftarKemasan.value = resKemasan.data?.results || resKemasan.data || []
            daftarBatch.value = resBatch.data?.results || resBatch.data || []
        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data referensi packing.')
        } finally {
            sedangProses.value = false
        }
    }

    const cekPratinjau = async (batchId, qtyKg) => {
        if (!batchId || qtyKg <= 0) {
            pratinjau.value.valid = false
            return
        }
        try {
            // Menggunakan fungsi dari warehouseApi
            const { data } = await warehouseApi.getPratinjauPacking(batchId, qtyKg)
            pratinjau.value = data
        } catch (err) {
            pratinjau.value = {
                valid: false,
                qty_kg: 0,
                harga_rata: 0,
                nilai_hpp: 0,
                sisa_qty_batch: 0,
                pesan: bacaError(err, 'Kalkulasi HPP gagal.')
            }
        }
    }

    const simpanPacking = async (payload) => {
        sedangProses.value = true
        galat.value = ''
        try {
            // FASE 1: Buat Dokumen (DRAFT) via warehouseApi
            const resDraft = await warehouseApi.simpanDraftPacking(payload)
            const draftId = resDraft.data.id

            // FASE 2: Posting & Absorpsi COGS (POSTED) via warehouseApi
            const resPost = await warehouseApi.postingPacking(draftId)
            return { success: true, data: resPost.data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal mengeksekusi klaim dan absorpsi COGS.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarEntitas, daftarKemasan, daftarBatch, pratinjau, sedangProses, galat,
        muatMasterData, cekPratinjau, simpanPacking
    }
}
