// src/features/warehouse/api.js
import api from '@/utils/api'

export const warehouseApi = {
    // ==========================================
    // 1. MODUL PENERIMAAN (GOODS RECEIPT)
    // ==========================================
    getPOSiapTerima: (params) => api.get('warehouse/po-siap-terima/', { params }),
    getPenerimaan: (params) => api.get('warehouse/penerimaan/', { params }),
    getRingkasanPenerimaan: (id) => api.get(`warehouse/penerimaan/${id}/ringkasan/`),
    simpanPenerimaan: (payload) => api.post('warehouse/penerimaan/', payload),

    // ==========================================
    // 2. MODUL PACKING
    // ==========================================
    getEntitasAktif: () => api.get('inventory/entitas/', { params: { aktif: true } }),
    getKemasanAktif: () => api.get('inventory/kemasan/', { params: { aktif: true } }),
    getBatchTersedia: () => api.get('produksi/batch/', { params: { status: 'POSTED' } }),
    getPratinjauPacking: (batchId, qtyKg) => api.get('inventory/packing/pratinjau/', { params: { batch: batchId, qty: qtyKg } }),
    simpanDraftPacking: (payload) => api.post('inventory/packing/', payload),
    postingPacking: (id) => api.post(`inventory/packing/${id}/post/`),

    // ==========================================
    // 3. MODUL SELISIH / RETUR (DISCREPANCY)
    // ==========================================
    getLaporanSelisih: (params) => api.get('warehouse/laporan-selisih/', { params }),
    getSelisihTerbuka: (params) => api.get('warehouse/laporan-selisih/terbuka/', { params }),
    buatLaporanManual: (payload) => api.post('warehouse/laporan-selisih/', payload),
    ajukanKlaim: (id, catatan) => api.post(`warehouse/laporan-selisih/${id}/ajukan/`, { catatan })
}

export default warehouseApi
