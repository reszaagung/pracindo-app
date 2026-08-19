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
        name: 'warehouse-receipt-list',
        component: () => import('@/features/warehouse/views/GoodsReceiptList.vue')
      },
      // Catatan: path 'receipt/buat' SUDAH DIHAPUS karena form sekarang menggunakan Lazy View
      {
        path: 'receipt/:id',
        name: 'warehouse-receipt-detail',
        component: () => import('@/features/warehouse/views/GoodsReceiptDetail.vue')
      },
      {
        path: 'discrepancy',
        name: 'warehouse-discrepancy-list',
        component: () => import('@/features/warehouse/views/DiscrepancyList.vue')
      }
    ]
  },
  {
    path: '/warehouse/distribution',
    meta: { perluLogin: true, modul: 'gudang' },
    component: () => import('@/features/warehouse/layout/DistributionLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/warehouse/distribution/packaging'
      },
      {
        path: 'packaging/log',
        name: 'warehouse-packaging-log',
        component: () => import('@/features/warehouse/views/LogPackageingList.vue')
      }
    ]
  }
]
