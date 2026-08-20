const CourirLayout = () => import('./layout/CourirLayout.vue')

export default [
    {
        path: '/kurir',
        component: CourirLayout,
        meta: { perluLogin: true, modul: 'logistik' },
        children: [
            {
                path: '',
                name: 'kurir-dashboard',
                component: () => import('./views/CourirDashboard.vue')
            },
            {
                path: 'tugas-saya',
                name: 'kurir-tugas-saya',
                component: () => import('./views/CourirTaskList.vue')
            },
            {
                path: 'tugas/:id',
                name: 'kurir-tugas-detail',
                component: () => import('./views/CourirTaskDetail.vue')
            }
        ]
    }
]
