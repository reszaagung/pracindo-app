const RetailLayout = () => import('./layout/RetailLayout.vue')
const AkuntansiLayout = () => import('./layout/AkuntansiLayout.vue')

export const retailRoutes = [
  // 1. Rute Portal Utama (Halaman dengan 2 kotak pilihan)
  {
    path: '/retail-portal',
    name: 'retail-portal',
    meta: { perluLogin: true, modul: 'retail' },
    component: () => import('./views/DashboardView.vue')
  },

  // 2. Rute Operasional Retail (Mesin Kasir, Penerimaan, Piutang)
  {
    path: '/retail',
    component: RetailLayout,
    meta: { perluLogin: true, modul: 'retail' },
    children: [
      {
        path: '',
        redirect: { name: 'retail-pos' }
      },
      {
        path: 'pos',
        name: 'retail-pos',
        component: () => import('./views/PosView.vue')
      },
      {
        path: 'penerimaan',
        name: 'retail-penerimaan',
        component: () => import('./views/PenerimaanView.vue')
      },
      {
        path: 'piutang',
        name: 'retail-piutang',
        component: () => import('./views/PiutangView.vue')
      },
      {
        path: 'riwayat',
        name: 'retail-riwayat',
        component: () => import('./views/RiwayatView.vue')
      }
    ]
  },

  // 3. Rute Akuntansi & Keuangan Retail (Buku Besar, Jurnal)
  {
    path: '/retail/keuangan',
    component: AkuntansiLayout,
    meta: { perluLogin: true, modul: 'retail' },
    children: [
      {
        path: '',
        name: 'retail-keuangan-dashboard',
        component: () => import('./views/KeuanganView.vue')
      },
      {
        path: 'buku-besar',
        name: 'retail-buku-besar',
        component: () => import('./views/BukuBesarView.vue')
      },
      {
        path: 'jurnal',
        name: 'retail-jurnal',
        component: () => import('./views/EntryJurnalView.vue')
      }
    ]
  }
]
