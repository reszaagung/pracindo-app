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
      }
    ]
  }
]
