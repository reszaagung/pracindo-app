import { createRouter, createWebHistory } from 'vue-router'
import { useGuards } from './guards'
import ModulLayout from '@/components/layout/ModulLayout.vue'

import ruteProduksi from '@/features/produksi/routes.js'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { publik: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { publik: true }
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { perluLogin: true }
  },
  {
    path: '/accounting',
    meta: { perluLogin: true, modul: 'akunting' },
    component: ModulLayout,
    children: [
      {
        path: '',
        name: 'accounting-landing',
        redirect: '/accounting/input/po'
      }
    ]
  },
  {
    path: '/accounting/input',
    meta: { perluLogin: true, modul: 'akunting' },
    component: () => import('@/features/accounting/layout/TransactionEntryLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/accounting/input/po'
      },
      {
        path: 'po',
        name: 'transaksi-po-list',
        component: () => import('@/features/accounting/views/PurchaseOrderList.vue')
      },
      {
        path: 'po/buat',
        name: 'transaksi-po-buat',
        component: () => import('@/features/accounting/views/ProcurementCreate.vue')
      },
      {
        path: 'so',
        name: 'transaksi-so-list',
        component: () => import('@/features/accounting/views/SalesOrderList.vue')
      },
      {
        path: 'so/buat',
        name: 'transaksi-so-buat',
        component: () => import('@/features/accounting/views/SalesOrderCreate.vue')
      },
      {
        path: 'pengeluaran/buat',
        name: 'transaksi-pengeluaran',
        component: () => import('@/features/accounting/views/Expense.vue')
      },
    ]
  },
  {
    path: '/accounting/invoice',
    meta: { perluLogin: true, modul: 'akunting' },
    component: () => import('@/features/accounting/layout/InvoiceLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/accounting/invoice/dokumen'
      },
      {
        path: 'dokumen',
        name: 'accounting-invoice-dokumen',
        component: () => import('@/features/accounting/views/DocumentAuditView.vue')
      },
      {
        path: 'tagihan',
        name: 'accounting-invoice-tagihan',
        component: () => import('@/features/accounting/views/InvoiceList.vue')
      },
      {
        path: 'tagihan/create',
        name: 'accounting-invoice-buat',
        component: () => import('@/features/accounting/views/InvoiceCreate.vue')
      },
      {
        path: 'catatan',
        name: 'accounting-invoice-catatan',
        component: () => import('@/features/accounting/views/Expense.vue')
      }
    ]
  },
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
        path: 'receipt/buat',
        name: 'warehouse-receipt-buat',
        component: () => import('@/features/warehouse/views/GoodsReceiptForm.vue')
      },
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
  },
  {
    path: '/master/suplier',
    name: 'master-suplier',
    meta: { perluLogin: true, modul: 'master' },
    component: () => import('@/features/master/views/Supplier.vue')
  },
  {
    path: '/inventory',
    meta: { perluLogin: true, modul: 'inventory' },
    component: () => import('@/features/inventory/layout/MonitoringLayout.vue'),
    children: [
      {
        path: '',
        name: 'inventory-stok-list',
        component: () => import('@/features/inventory/views/StockList.vue')
      },
      {
        path: 'stok/:id',
        name: 'inventory-stok-detail',
        component: () => import('@/features/inventory/views/StockDetail.vue'),
        props: true
      },
      {
        path: 'klaim/:grup',
        name: 'inventory-klaim',
        component: () => import('@/features/inventory/views/ClaimPosition.vue'),
        props: true
      },
    ]
  },
  {
    path: '/distribusi',
    meta: { perluLogin: true, modul: 'distribusi' },
    component: () => import('@/features/distribusi/layout/DistributionLayout.vue'),
    children: [
      {
        path: '',
        name: 'distribusi-jadwal',
        component: () => import('@/features/distribusi/views/DeliverySchedule.vue')
      },
      {
        path: 'loading',
        name: 'distribusi-loading',
        component: () => import('@/features/distribusi/views/LoadingValidation.vue')
      },
      {
        path: 'armada',
        name: 'distribusi-armada',
        component: () => import('@/features/distribusi/views/FleetStatus.vue')
      },
    ]
  },
  {
    path: '/kurir',
    meta: { perluLogin: true, modul: 'logistik' },
    component: () => import('@/features/logistik/layout/CourirLayout.vue'),
    children: [
      {
        path: '',
        name: 'kurir-dashboard',
        component: () => import('@/features/logistik/views/CourirDashboard.vue')
      },
      {
        path: 'tugas-saya',
        name: 'kurir-tugas-saya',
        component: () => import('@/features/logistik/views/CourirTaskList.vue')
      },
      {
        path: 'tugas/:id',
        name: 'kurir-tugas-detail',
        component: () => import('@/features/logistik/views/CourirTaskDetail.vue')
      }
    ]
  },
  ...ruteProduksi,
  {
    path: '/work-order',
    name: 'work-order',
    meta: { perluLogin: true, modul: 'work_order' },
    component: () => import('@/features/work-order/views/WorkOrderBoard.vue')
  },
  {
    path: '/dokumen',
    name: 'dokumen',
    meta: { perluLogin: true, modul: 'dokumen' },
    component: () => import('@/views/ModulBelumSiap.vue')
  },
  {
    path: '/akses-ditolak',
    name: 'akses-ditolak',
    meta: { perluLogin: true },
    component: () => import('@/views/AksesDitolak.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    meta: { perluLogin: true },
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0, behavior: 'smooth' }
  }
})

useGuards(router)

export default router
