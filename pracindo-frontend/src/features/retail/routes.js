import RetailLayout from './layout/RetailLayout.vue'

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
                path: 'laporan',
                name: 'retail-laporan',
                component: () => import('./views/KeuanganView.vue') // Sesuaikan nama file jika berbeda
            },
            {
                path: 'buku-besar',
                name: 'retail-buku-besar',
                component: () => import('./views/BukuBesarView.vue')
            },
            {
                path: 'jurnal',
                name: 'retail-jurnal',
                component: () => import('./views/JurnalView.vue')
            }
        ]
    }
]
