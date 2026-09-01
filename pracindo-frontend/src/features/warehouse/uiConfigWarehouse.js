export const gudangModul = {
  id: 'gudang',
  nama: 'Penerimaan & Packing',
  ringkas: 'Penerimaan barang, pengemasan (packing), laporan selisih, dan QC',
  ikon: 'box',
  rute: '/warehouse/input/receipt',
  siap: true,
  menu: [
    { label: 'Penerimaan', rute: '/warehouse/input/receipt' },
    { label: 'Input Packageing', rute: '/warehouse/input/packing' },
    { label: 'Riwayat Packing', rute: '/warehouse/input/packaging/log' },
    { label: 'Selisih / Retur', rute: '/warehouse/input/discrepancy' },
    { label: 'Inspeksi QC', rute: '/warehouse/input/qc' },
  ],
}

export const distribusiModul = {
  id: 'warehouse_distribusi',
  nama: 'Distribusi Pengiriman',
  ringkas: 'Manajemen jadwal pengiriman, perakitan muatan, dan status armada',
  ikon: 'truck',
  rute: '/distribusi',
  siap: true,
  menu: [
    { label: 'Jadwal Pengiriman', rute: '/distribusi' },
    { label: 'Rakit Pengiriman', rute: '/distribusi/buat' },
    { label: 'Loading Muatan', rute: '/distribusi/loading' },
    { label: 'Status Armada', rute: '/distribusi/armada' },
  ],
}
