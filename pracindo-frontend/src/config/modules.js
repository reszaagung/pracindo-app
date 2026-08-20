/**
 * src/config/modules.js
 * ======================
 * Katalog UI SAJA. Siapa yang boleh masuk modul apa ditentukan backend lewat
 * GET auth/portal/ (lihat useAuth().modul) — file ini tidak menyimpan aturan
 * peran, hanya bagaimana modul itu tampil (ikon, label, menu, status siap).
 */

// 1. IMPORT KONFIGURASI MENU DARI MODUL PRODUKSI
import { produksiModul } from '@/features/produksi/uiConfig'

export const MODUL = [
  {
    id: 'akunting',
    nama: 'Input Entry',
    ringkas: 'Purchase order, faktur, dan pembayaran',
    ikon: 'buku',
    rute: '/accounting/input',
    siap: true,
    menu: [
      { label: 'Purchase Order', rute: '/accounting/input/po' },
      { label: 'Pengeluaran', rute: '/accounting/input/expend' },
    ],
  },
  {
    id: 'buku_tagihan',
    nama: 'Buku Tagihan',
    ringkas: 'Manajemen invoice, dokumen, dan catatan pengeluaran',
    ikon: 'transaksi',
    rute: '/accounting/invoice',
    siap: true,
    indukModul: 'akunting',
    menu: [
      { label: 'Dokumen', rute: '/accounting/invoice/dokumen' },
    ],
  },
  {
    id: 'warehouse',
    nama: 'Gudang',
    ringkas: 'Goods receipt, pencatatan masuk, dan cek selisih',
    ikon: 'gudang',
    rute: '/warehouse',
    siap: true,
    menu: [
      { label: 'Goods Receipt', rute: '/warehouse/input/receipt' },
      { label: 'Daftar Selisih', rute: '/warehouse/input/discrepancy' },
    ],
  },
  {
    id: 'warehouse_distribusi',
    nama: 'Distribusi & Kemasan',
    ringkas: 'Manajemen jadwal pengiriman, armada, dan loading',
    ikon: 'kirim',
    rute: '/distribusi',
    siap: true,
    indukModul: 'warehouse',
    menu: [
      { label: 'Jadwal Pengiriman', rute: '/distribusi' },
      { label: 'Rakit Pengiriman', rute: '/distribusi/buat' },
      { label: 'Loading Muatan', rute: '/distribusi/loading' },
      { label: 'Status Armada', rute: '/distribusi/armada' },
    ],
  },
  {
    id: 'master',
    nama: 'Master Data',
    ringkas: 'Suplier, produk, dan data acuan lain',
    ikon: 'master',
    rute: '/master/suplier',
    siap: true,
    menu: [
      { label: 'Suplier', rute: '/master/suplier' },
    ],
  },

  // ==========================================
  // BLOK MODUL PRODUKSI (Modular)
  // ==========================================
  produksiModul,

  {
    id: 'logistik',
    nama: 'Logistik (Kurir)',
    ringkas: 'Aplikasi lapangan kurir dan status pengiriman',
    ikon: 'kirim',
    rute: '/kurir',
    siap: true,
    catatan: '',
    menu: [
      { label: 'Dashboard', rute: '/kurir' },
      { label: 'Tugas Saya', rute: '/kurir/tugas-saya' },
    ],
  },
  {
    id: 'sales_order',
    nama: 'Sales Order',
    ringkas: 'Pesanan penjualan dan piutang',
    ikon: 'transaksi',
    rute: '/sales-order',
    siap: false,
    catatan: 'Belum dibangun backend maupun frontend',
    menu: [],
  },
  {
    id: 'inventory',
    nama: 'Inventory',
    ringkas: 'Stok tiga lapis dan posisi klaim',
    ikon: 'gudang',
    rute: '/inventory',
    siap: true,
    sembunyiDiDashboardUntuk: ['AKUNTING'],
    menu: [
      { label: 'Stok', rute: '/inventory' },
      { label: 'Kalkulasi Klaim', rute: '/inventory/formulation' },
    ],
  },
  {
    id: 'keuangan',
    nama: 'Keuangan',
    ringkas: 'Pembayaran dan kas',
    ikon: 'buku',
    rute: '/keuangan',
    siap: false,
    catatan: 'Sebagian lewat modul akunting, layar sendiri belum ada',
    menu: [],
  },
  {
    id: 'staff_user',
    nama: 'Pengguna',
    ringkas: 'Kelola akun dan persetujuan staf',
    ikon: 'master',
    rute: '/pengguna',
    siap: false,
    catatan: 'Layar belum dibangun',
    menu: [],
  },
  {
    id: 'work_order',
    nama: 'Papan Tugas',
    ringkas: 'Tugas dan penugasan antar staf',
    ikon: 'transaksi',
    rute: '/work-order',
    siap: true,
    sembunyiDiDashboard: true,
    menu: [],
  },
  {
    id: 'dokumen',
    nama: 'Dokumen',
    ringkas: 'Arsip dan audit dokumen',
    ikon: 'buku',
    rute: '/dokumen',
    siap: false,
    sembunyiDiDashboard: true,
    menu: [],
  },
  {
    id: 'pajak',
    nama: 'Pajak',
    ringkas: 'Manajemen pelaporan pajak',
    ikon: 'buku',
    rute: '/pajak',
    siap: false,
    sembunyiDiDashboard: true,
    menu: [],
  },
  {
    id: 'dashboard',
    nama: 'Dashboard',
    ringkas: 'Halaman ini sendiri',
    ikon: 'panah',
    rute: '/',
    siap: false,
    catatan: 'Kamu sudah di sini',
    sembunyiDiDashboard: true,
    menu: [],
  },
]

export const cariModul = (id) => MODUL.find((m) => m.id === id) ?? null

export const modulDariBackend = (modulBackend = []) =>
  modulBackend.map((mb) => {
    const lokal = cariModul(mb.kode)
    return {
      id: mb.kode,
      nama: lokal?.nama ?? mb.label ?? mb.kode,
      ikon: lokal?.ikon || 'master',
      rute: lokal?.rute || mb.rute || '/',
      ringkas: lokal?.ringkas ?? '',
      catatan: lokal?.catatan ?? '',
      siap: lokal?.siap ?? false,
      sembunyiDiDashboardUntuk: lokal?.sembunyiDiDashboardUntuk || [],
      sembunyiDiDashboard: lokal?.sembunyiDiDashboard || false,
      menu: lokal?.menu ?? [],
    }
  })

/**
 * Rute pendaratan setelah login: modul PERTAMA yang siap dan bukan kartu
 * tersembunyi. Dipakai guards.js dan LoginView.vue — dua tempat yang dulu
 * sama-sama meng-hardcode '/accounting' lalu '/warehouse'.
 *
 * Urutannya mengikuti urutan entri di MODUL, BUKAN urutan kiriman backend.
 * Jadi mengubah prioritas pendaratan = memindahkan entri di file ini, bukan
 * menambah if-else di guard. Itu juga sebabnya rute tidak boleh ditulis
 * ulang di guard: pernah kena 404 waktu path akunting berubah.
 *
 * @returns {string|null} path, atau null kalau tidak ada modul yang siap
 */
export const rutePertamaSiap = (modulBackend = []) => {
  const urutan = (m) => {
    const i = MODUL.findIndex((k) => k.id === m.id)
    return i === -1 ? Number.MAX_SAFE_INTEGER : i
  }
  const siap = modulDariBackend(modulBackend)
    .filter((m) => m.siap && !m.sembunyiDiDashboard)
    .sort((a, b) => urutan(a) - urutan(b))

  return siap[0]?.rute ?? null
}

export const IKON = {
  transaksi: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
  buku: '<path d="M5 3h14v18H5zM9 8h6M9 12h6M9 16h3"/>',
  gudang: '<path d="M3 9l9-5 9 5v11H3z"/><path d="M8 20v-7h8v7"/>',
  produksi: '<path d="M4 20V9l5 3V9l5 3V6l6 4v10z"/><path d="M4 20h16"/>',
  kirim: '<path d="M2 7h11v9H2zM13 10h4l3 3v3h-7z"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
  master: '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/>',
  panah: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  balik: '<path d="M19 12H5M12 19l-7-7 7-7"/>',
  tambah: '<path d="M12 5v14M5 12h14"/>',
}
