const DistributionLayout = () => import('./layout/DistributionLayout.vue')

export default [
    {
        path: '/distribusi',
        component: DistributionLayout,
        meta: { perluLogin: true, modul: 'warehouse_distribusi' },
        children: [
            {
                path: '',
                name: 'distribusi-jadwal',
                component: () => import('./views/DeliverySchedule.vue')
            },
            {
                path: 'buat',
                name: 'distribusi-buat',
                component: () => import('./views/DeliveryCreate.vue')
            },
            {
                path: 'loading',
                name: 'distribusi-loading',
                component: () => import('./views/LoadingValidation.vue')
            },
            {
                path: 'armada',
                name: 'distribusi-armada',
                component: () => import('./views/FleetStatus.vue')
            }
        ]
    }
]
