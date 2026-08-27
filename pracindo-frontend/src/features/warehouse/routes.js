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
      {
        path: 'receipt/:id',
        name: 'warehouse-receipt-detail',
        component: () => import('@/features/warehouse/views/GoodsReceiptDetail.vue')
      },
      {
        path: 'packing',
        name: 'warehouse-packing',
        // --- DIUBAH MENJADI LIST AGAR BISA MEMUAT TABEL & FORM SEKALIGUS ---
        component: () => import('@/features/warehouse/views/InputPackingList.vue')
      },
      {
        path: 'packaging/log',
        name: 'warehouse-packaging-log',
        component: () => import('@/features/warehouse/views/LogPackageingList.vue')
      },
      {
        path: 'discrepancy',
        name: 'warehouse-discrepancy-list',
        component: () => import('@/features/warehouse/views/DiscrepancyList.vue')
      }
    ]
  }
]
