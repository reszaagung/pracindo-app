import { ref } from 'vue'
import { warehouseApi } from '../api' 
import { apiProduksi } from '@/features/produksi/api'
import { bacaError } from '@/utils/error'
import { angka } from '@/utils/format'

export function usePacking() {
    const daftarEntitas = ref([])
    const daftarKemasan = ref([])
    const daftarBatch = ref([])
    const daftarProduk = ref([])

    const sedangProses = ref(false)
    const galat = ref('')

    const pratinjau = ref({
        valid: false, qty_kg: 0, harga_per_kg: 0, nilai_tagihan: 0,
        sisa_qty_batch: 0, menghabiskan: false, peringatan: [], pesan: ''
    })

    const muatMasterData = async () => {
        sedangProses.value = true
        galat.value = ''
        try {
            const [resEntitas, resKemasan, resBatch, resProduk] = await Promise.all([
                warehouseApi.getEntitasAktif(),
                warehouseApi.getKemasanAktif(),
                apiProduksi.getBatches({ status: 'POSTED' }),
                warehouseApi.getMasterProduk({ kategori: 'FINISHED_GOODS' })
            ])

            const ekstrakData = (res) => res?.data?.results || res?.results || res?.data || (Array.isArray(res) ? res : [])

            daftarEntitas.value = ekstrakData(resEntitas)

            const rawKemasan = ekstrakData(resKemasan)
            daftarKemasan.value = rawKemasan.map(k => {
                const qtyUnit = Number(k.qty_unit) || 0
                const totalNilai = Number(k.nilai) || 0
                const unitCost = k.harga_satuan ?? (qtyUnit > 0 ? totalNilai / qtyUnit : 0)

                return {
                    ...k,
                    harga_satuan_calculated: unitCost,
                    label_dropdown: `${k.produk_nama || 'Kemasan'} (Stok: ${angka(qtyUnit, 0)} Unit | @Rp ${angka(unitCost)})`
                }
            })

            const rawProduk = ekstrakData(resProduk)
            daftarProduk.value = rawProduk.map(p => ({
                ...p,
                label_display: p.nama_item || p.nama || p.nama_produk || `Produk #${p.kode_item}`
            }))

            const rawBatch = ekstrakData(resBatch)
            const batchAdaIsi = rawBatch.filter(b => Number(b.qty_hasil ?? 0) > 0)

            daftarBatch.value = batchAdaIsi.map(b => {
                const qty = b.qty_hasil ?? 0
                const kodeTangki = b.tangki_kode ?? 'TANGKI'
                const namaHasil = b.nama_hasil ?? 'WIP'
                const noBatch = b.nomor ? ` | Batch: ${b.nomor}` : ''

                return {
                    ...b,
                    label_dropdown: `[${kodeTangki}] ${namaHasil} (Sisa: ${angka(qty, 3)} Kg${noBatch})`
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
            pratinjau.value = { 
                valid: false, qty_kg: 0, harga_per_kg: 0, nilai_tagihan: 0, sisa_qty_batch: 0,
                menghabiskan: false, peringatan: [],
                pesan: bacaError(err, 'Kalkulasi HPP gagal.') 
            }
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
        daftarEntitas, daftarKemasan, daftarBatch, daftarProduk,
        pratinjau, sedangProses, galat,
        muatMasterData, cekPratinjau, simpanPacking
    }
}