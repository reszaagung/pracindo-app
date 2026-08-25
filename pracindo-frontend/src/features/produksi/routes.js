export default [
  {
    path: '/produksi',
    component: () => import('./layout/ProduksiLayout.vue'),
    meta: { perluLogin: true, modul: 'produksi' },
    children: [
      {
        path: '',
        redirect: '/produksi/batch'
      },
      {
        path: 'batch',
        name: 'produksi-batch-list',
        component: () => import('./views/BatchList.vue')
      },
      {
        path: 'batch/buat',
        name: 'produksi-batch-buat',
        component: () => import('./views/BatchForm.vue')
      },
      {
        path: 'batch/:id',
        name: 'produksi-batch-detail',
        component: () => import('./views/BatchDetail.vue'),
        props: true
      },
      {
        path: 'tangki',
        name: 'produksi-tangki-list',
        component: () => import('./views/TangkiList.vue')
      }
    ]
  }
]
