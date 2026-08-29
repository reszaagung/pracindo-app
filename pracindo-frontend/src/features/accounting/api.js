// src/features/accounting/api.js
import api from '@/utils/api'

export const accountingApi = {
    // ---- MASTER DATA (Digunakan Lintas Form) ----
    master: {
        getPortalEntitas: () => api.get('auth/portal/'), //[cite: 7]
        getEntitasCore: () => api.get('core/entitas/'), //[cite: 7]
        getSupplier: (params) => api.get('master/suplier/', { params }), //[cite: 7]
        getPelanggan: () => api.get('master/pelanggan/'), //[cite: 7]
        getProduk: () => api.get('master/produk/'), //[cite: 7]
        getSatuan: (params) => api.get('master/satuan/', { params }), //[cite: 7]
        buatProduk: (payload) => api.post('master/produk/', payload), //[cite: 7]
        cekPeriode: (params) => api.get('core/periode/status/', { params }) //[cite: 7]
    },

    // ---- PURCHASE ORDER (usePurchaseOrder.js) ----
    po: {
        getDaftar: () => api.get('akunting/purchase-order/'), //[cite: 7]
        getPreviewNomor: (params) => api.get('akunting/purchase-order/preview-nomor/', { params }), //[cite: 7]
        simpanBaru: (payload) => api.post('akunting/purchase-order/', payload), //[cite: 7]
        // Aksi Status
        ajukan: (id) => api.post(`akunting/purchase-order/${id}/ajukan/`), //[cite: 7]
        setujui: (id) => api.post(`akunting/purchase-order/${id}/setujui/`), //[cite: 7]
        tolak: (id, payload) => api.post(`akunting/purchase-order/${id}/tolak/`, payload), //[cite: 7]
        kirim: (id) => api.post(`akunting/purchase-order/${id}/kirim/`), //[cite: 7]
        batalkan: (id, payload) => api.post(`akunting/purchase-order/${id}/batalkan/`, payload) //[cite: 7]
    },

    // ---- SALES ORDER (useSalesOrder.js) ----
    so: {
        getDaftar: () => api.get('sales-order/'), //[cite: 7]
        getPreviewNomor: (params) => api.get('sales-order/preview-nomor/', { params }), //[cite: 7]
        simpanBaru: (payload) => api.post('sales-order/', payload) //[cite: 7]
    },

    // ---- PENGELUARAN KAS (useExpense.js) ----
    expense: {
        getAkun: () => api.get('akunting/akun/'), //[cite: 7]
        getDaftar: (params) => api.get('akunting/pengeluaran-kas/', { params }), //[cite: 7]
        simpanBaru: (payload, config) => api.post('akunting/pengeluaran-kas/', payload, config), //[cite: 7]
        posting: (id) => api.post(`akunting/pengeluaran-kas/${id}/posting/`) //[cite: 7]
    },

    // ---- INVOICE (useInvoice.js) ----
    invoice: {
        getFakturJual: () => api.get('akunting/faktur-jual/'), //[cite: 7]
        terbitkanDariDO: (deliveryOrderId, payload) => api.post(`akunting/faktur-jual/dari-do/${deliveryOrderId}/`, payload) //[cite: 7]
    },

    // ---- DOKUMEN & AUDIT (useDocument.js) ----
    dokumen: {
        upload: (payload) => api.post('dokumen-audit/', payload), //[cite: 7]
        hapus: (po_id, config) => api.delete(`dokumen-audit/${po_id}/`, config) //[cite: 7]
    }
}