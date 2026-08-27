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
      // 1. UBAH KE KOMPONEN WRAPPER (ReceiptIndex)
      {
        path: 'receipt',
        name: 'warehouse-receipt-index',
        component: () => import('@/features/warehouse/views/ReceiptIndex.vue')
      },
      // 2. DETAIL BAHAN BAKU
      {
        path: 'receipt/:id',
        name: 'warehouse-receipt-detail',
        component: () => import('@/features/warehouse/views/GoodsReceiptDetail.vue'),
        props: true // Memungkinkan pengiriman ID sebagai props ke dalam komponen Vue
      },
      // 3. TAMBAHAN: DETAIL KEMASAN
      {
        path: 'package-receipt/:id',
        name: 'warehouse-package-receipt-detail',
        component: () => import('@/features/warehouse/views/PackageReceiptDetail.vue'),
        props: true
      },
      {
        path: 'packing',
        name: 'warehouse-packing',
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
