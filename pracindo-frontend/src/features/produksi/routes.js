// src/features/produksi/routes.js
const ProduksiLayout = () => import('./layout/ProduksiLayout.vue')

export default [
    {
        path: '/produksi',
        component: ProduksiLayout,
        meta: { perluLogin: true, modul: 'produksi' },
        children: [
            {
                path: '',
                redirect: { name: 'produksi-batch' }
            },
            {
                path: 'batch',
                name: 'produksi-batch',
                component: () => import('./views/BatchList.vue')
            },
            {
                path: 'batch/baru',
                name: 'produksi-batch-baru',
                component: () => import('./views/InputProduksi.vue') // <-- Diperbarui di sini
            },
            {
                path: 'batch/:id',
                name: 'produksi-batch-detail',
                props: true,
                component: () => import('./views/BatchDetail.vue')
            },
            {
                path: 'tangki',
                name: 'produksi-tangki',
                component: () => import('./views/TangkiMonitor.vue')
            },
        ],
    },
]
