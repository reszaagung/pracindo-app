import RetailLayout from './layout/RetailLayout.vue'
import AkuntansiLayout from './layout/AkuntansiLayout.vue'

export const retailRoutes = [
    {
        path: '/retail',
        meta: { perluLogin: true, modul: 'retail' },
        component: RetailLayout,
        children: [
            {
                path: '',
                redirect: '/retail/pos'
            },
            {
                path: 'pos',
                name: 'retail-pos',
                component: () => import('./views/PosView.vue')
            },
            {
                path: 'piutang',
                name: 'retail-piutang',
                component: () => import('./views/PiutangView.vue')
            },
            {
                path: 'penerimaan',
                name: 'retail-penerimaan',
                component: () => import('./views/PenerimaanView.vue')
            }
        ]
    },

    {
        path: '/akuntansi',
        meta: { perluLogin: true, modul: 'akuntansi' },
        component: AkuntansiLayout,
        children: [
            {
                path: '',
                redirect: '/akuntansi/buku-besar'
            },
            {
                path: 'buku-besar',
                name: 'akuntansi-buku-besar',
                component: () => import('./views/BukuBesarView.vue')
            },
            {
                path: 'jurnal',
                name: 'akuntansi-jurnal',
                component: () => import('./views/JurnalView.vue')
            },
            {
                path: 'jurnal/entri',
                name: 'akuntansi-jurnal-entri',
                component: () => import('./views/EntriJurnalView.vue')
            },
            {
                path: 'laporan',
                name: 'akuntansi-laporan',
                component: () => import('./views/KeuanganView.vue')
            }
        ]
    }
]
