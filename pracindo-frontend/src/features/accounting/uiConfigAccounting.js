// src/features/accounting/uiConfigAccounting.js

// Diekstrak dari useNavTransaction.js
export const menuTransaksi = [
    { id: 'po', label: 'Purchase Order (PO)', rute: '/accounting/input/po', ikon: 'pi-file-edit', activate: true }, //
    { id: 'so', label: 'Sales Order (SO)', rute: '/accounting/input/so', ikon: 'pi-file-export', activate: true }, //[cite: 7]
    { id: 'pengeluaran', label: 'Catat Pengeluaran', rute: '/accounting/input/pengeluaran/buat', ikon: 'pi-wallet', activate: true } //[cite: 7]
]

// Diekstrak dari useNavInvoice.js
export const menuInvoice = [
    { id: 'dokumen', label: 'Dokumen & Audit', ikon: 'pi-folder-open', rute: '/accounting/invoice/dokumen', activate: true }, //[cite: 7]
    { id: 'tagihan', label: 'Manajemen Tagihan', ikon: 'pi-receipt', rute: '/accounting/invoice/tagihan', activate: true }, //[cite: 7]
    { id: 'catatan', label: 'Catatan Pengeluaran', ikon: 'pi-wallet', rute: '/accounting/invoice/catatan', activate: true } //[cite: 7]
]