import ModulLayout from '@/components/layout/ModulLayout.vue'

export default [
  {
    path: '/warehouse',
    meta: { perluLogin: true, modul: 'gudang' },
    component: ModulLayout,
    children: [
      {
        path: '',
        name: 'warehouse-landing',
        redirect: '/warehouse/input/receipt'
      }
    ]
  },
  {
    path: '/warehouse/input',
    meta: { perluLogin: true, modul: 'warehouse' },
    component: () => import('@/features/warehouse/layout/InputEntryLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/warehouse/input/receipt'
      },
      {
        path: 'receipt',
        name: 'warehouse-receipt-index',
        component: () => import('@/features/warehouse/views/ReceiptIndex.vue')
      },
      {
        path: 'receipt/:id',
        name: 'warehouse-receipt-detail',
        component: () => import('@/features/warehouse/views/GoodsReceiptDetail.vue'),
        props: true
      },
      {
        path: 'package-receipt/:id',
        name: 'warehouse-package-receipt-detail',
        component: () => import('@/features/warehouse/views/PackageReceiptDetail.vue'),
        props: true
      },
      {
        path: 'packing',
        name: 'InputPackingList',
        component: () => import('@/features/warehouse/views/InputPackingList.vue')
      },
      {
        path: 'packing/form',
        name: 'InputPackingForm',
        component: () => import('@/features/warehouse/views/InputPackingForm.vue')
      },
      {
        path: 'discrepancy',
        name: 'warehouse-discrepancy-list',
        component: () => import('@/features/warehouse/views/DiscrepancyList.vue')
      }
    ]
  }
]