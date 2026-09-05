import api from '@/utils/api'

export const warehouseApi = {
  // === MODUL PENERIMAAN ===
  getPOSiapTerima: (params) => api.get('warehouse/po-siap-terima/', { params }),
  getPenerimaan: (params) => api.get('warehouse/penerimaan/', { params }),
  getRingkasanPenerimaan: (id) => api.get(`warehouse/penerimaan/${id}/ringkasan/`),
  simpanPenerimaan: (payload) => api.post('warehouse/penerimaan/', payload),

  // === MODUL PACKING (BARU) ===
  getEntitasAktif: () => api.get('inventory/entitas/', { params: { aktif: true } }),
  getKemasanAktif: () => api.get('inventory/pool/kemasan/'), 
  getBatchTersedia: () => api.get('produksi/batch/', { params: { status: 'POSTED' } }),
  getRiwayatPacking: (params) => api.get('inventory/packing/', { params }), // <--- TAMBAHAN
  getPratinjauPacking: (batchId, qtyKg) => api.get('inventory/packing/pratinjau/', { params: { batch: batchId, qty: qtyKg } }),
  simpanPacking: (payload) => api.post('inventory/packing/', payload),
  voidPacking: (id, payload) => api.post(`inventory/packing/${id}/void_dokumen/`, payload), // <--- TAMBAHAN

  // === MODUL SELISIH ===
  getLaporanSelisih: (params) => api.get('warehouse/laporan-selisih/', { params }),
  getSelisihTerbuka: (params) => api.get('warehouse/laporan-selisih/terbuka/', { params }),
  buatLaporanManual: (payload) => api.post('warehouse/laporan-selisih/', payload),
  ajukanKlaim: (id, catatan) => api.post(`warehouse/laporan-selisih/${id}/ajukan/`, { catatan }),

  // === MASTER ===
  getMasterProduk: (params) => api.get('master/master-produk/', { params }),
  getDetailMasterProduk: (id) => api.get(`master/master-produk/${id}/`),
  buatMasterProduk: (payload) => api.post('master/master-produk/', payload),
  updateMasterProduk: (id, payload) => api.put(`master/master-produk/${id}/`, payload),
  patchMasterProduk: (id, payload) => api.patch(`master/master-produk/${id}/`, payload),
}

export default warehouseApi