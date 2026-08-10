import { useRoute } from 'vue-router'

export function useNavInvoice() {
    const route = useRoute()

    // Daftar menu untuk Sidebar InvoiceLayout
    const menu = [
        {
            id: 'dokumen',
            label: 'Dokumen & Audit',
            ikon: 'pi-folder-open', // Ikon folder untuk manajemen dokumen
            rute: '/accounting/invoice/dokumen',
            activate: true // Set true karena Document.vue (DocumentAuditView) sudah siap
        },
        {
            id: 'tagihan',
            label: 'Manajemen Tagihan',
            ikon: 'pi-receipt', // Ikon struk/invoice untuk tagihan
            rute: '/accounting/invoice/tagihan',
            activate: true // Ubah ke false jika halaman Vue-nya belum Anda buat
        },
        {
            id: 'catatan',
            label: 'Catatan Pengeluaran',
            ikon: 'pi-wallet', // Ikon dompet untuk pengeluaran kas
            rute: '/accounting/invoice/catatan',
            activate: true // Ubah ke false jika halaman Vue-nya belum Anda buat
        }
    ]

    // Fungsi untuk mengecek apakah tombol menu harus disorot (aktif)
    const aktif = (ruteTujuan) => {
        if (!route) return false

        // Cek pencocokan eksak atau jika sedang berada di sub-rute (misal: /accounting/invoice/dokumen/detail)
        return route.path === ruteTujuan || route.path.startsWith(ruteTujuan + '/')
    }

    return {
        menu,
        aktif
    }
}