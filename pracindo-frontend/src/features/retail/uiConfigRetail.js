export const retailModul = {
  id: 'retail',
  nama: 'Retail & POS',
  ringkas: 'Mesin kasir cabang, penerimaan logistik, dan laporan shift',
  ikon: 'transaksi',
  rute: '/retail/pos',
  siap: true,
  menu: [
    { label: 'Kasir Cabang', rute: '/retail/pos' },
    { label: 'Penerimaan Stok', rute: '/retail/penerimaan' },
    { label: 'Riwayat Penjualan', rute: '/retail/riwayat' },
    { label: 'Keuangan Shift', rute: '/retail/keuangan' },
  ],
}
