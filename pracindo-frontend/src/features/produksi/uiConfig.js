// src/features/produksi/uiConfig.js

export const produksiModul = {
    id: 'produksi',
    nama: 'Produksi',
    ringkas: 'Input produksi, pencampuran batch, dan monitor tangki',
    ikon: 'produksi',
    rute: '/produksi/batch', // Diperbarui dari /produksi/mixing
    siap: true,
    menu: [
        { label: 'Riwayat Batch', rute: '/produksi/batch' },
        { label: 'Input Baru', rute: '/produksi/batch/baru' },
        { label: 'Monitor Tangki', rute: '/produksi/tangki' }
    ]
}