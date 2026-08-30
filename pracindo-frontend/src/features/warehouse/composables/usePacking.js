// src/features/warehouse/composables/usePacking.js
import { ref } from 'vue'
import { warehouseApi } from '../api' 
import { apiProduksi } from '@/features/produksi/api'
import api from '@/utils/api' // Tambahkan ini untuk akses API master produk
import { bacaError } from '@/utils/error'
import { angka } from '@/utils/format' 

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([]) 
    const daftarProduk = ref([]) // STATE BARU: Untuk menyimpan daftar produk/barang

    const sedangProses = ref(false)
    const galat = ref('')

    const pratinjau = ref({
        valid: false, qty_kg: 0, harga_rata: 0, nilai_hpp: 0, sisa_qty_batch: 0, pesan: ''
    })

const muatMasterData = async () => {
        sedangProses.value = true
        galat.value = ''
        try {
            // Tarik semua master data secara paralel
            const [resEntitas, resKemasan, resBatch, resProduk] = await Promise.all([
                warehouseApi.getEntitasAktif(),
                warehouseApi.getKemasanAktif(),
                apiProduksi.getBatches({ status: 'POSTED' }),
                // Sesuaikan URL ini dengan router di master/urls.py
                api.get('master/master-produk/') 
            ])

            const ekstrakData = (res) => res?.data?.results || res?.results || res?.data || (Array.isArray(res) ? res : [])

            daftarEntitas.value = ekstrakData(resEntitas)
            daftarKemasan.value = ekstrakData(resKemasan)
            daftarProduk.value = ekstrakData(resProduk) 
            
            const rawBatch = ekstrakData(resBatch)

            const batchAdaIsi = rawBatch.filter(b => {
                const qty = b.qty_hasil ?? 0
                return Number(qty) > 0 
            })

            daftarBatch.value = batchAdaIsi.map(b => {
                const qty = b.qty_hasil ?? 0
                const harga = b.harga_per_kg ?? 0
                const kodeTangki = b.tangki_kode ?? 'TANGKI-??' 
                const namaHasil = b.nama_hasil ?? 'WIP'
                const idBatch = b.nomor ?? '-'
                
                return {
                    ...b, 
                    label_dropdown: `[${kodeTangki}] ${namaHasil} (Sisa: ${angka(qty, 3)} Kg | Batch: ${idBatch})`
                }
            })

        } catch (err) {
            galat.value = bacaError(err, 'Gagal memuat data Master & WIP Produksi.')
        } finally {
            sedangProses.value = false
        }
    }

    const cekPratinjau = async (batchId, qtyKg) => {
        if (!batchId || qtyKg <= 0) {
            pratinjau.value.valid = false; return
        }
        try {
            const { data } = await warehouseApi.getPratinjauPacking(batchId, qtyKg)
            pratinjau.value = data
        } catch (err) {
            pratinjau.value = { valid: false, qty_kg: 0, harga_rata: 0, nilai_hpp: 0, sisa_qty_batch: 0, pesan: bacaError(err, 'Kalkulasi HPP gagal.') }
        }
    }

    const simpanPacking = async (payload) => {
        sedangProses.value = true; galat.value = ''
        try {
            const resDraft = await warehouseApi.simpanDraftPacking(payload)
            const resPost = await warehouseApi.postingPacking(resDraft.data.id)
            return { success: true, data: resPost.data }
        } catch (err) {
            galat.value = bacaError(err, 'Gagal mengeksekusi klaim dan absorpsi COGS.')
            return { success: false, message: galat.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarEntitas, daftarKemasan, daftarBatch, daftarProduk, // Tambahkan ini
        pratinjau, sedangProses, galat,
        muatMasterData, cekPratinjau, simpanPacking
    }
}