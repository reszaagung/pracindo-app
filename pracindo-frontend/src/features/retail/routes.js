const RetailLayout = () => import('./layout/RetailLayout.vue')
const AkuntansiLayout = () => import('./layout/AkuntansiLayout.vue')

export const retailRoutes = [
  {
    path: '/retail',
    name: 'retail-portal',
    meta: { perluLogin: true, modul: 'retail' },
    component: () => import('./views/DashboardView.vue')
  },
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
        // PERBAIKAN: Arahkan ke file yang ada logikanya, bukan yang dummy!
        component: () => import('./views/Penerimaan.vue')
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
