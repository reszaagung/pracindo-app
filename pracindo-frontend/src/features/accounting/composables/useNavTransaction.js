import { useRoute } from 'vue-router'

export function useNavTransaksi() {
    const route = useRoute()
    const transaksi = [
        {
            id: 'po',
            label: 'Purchase Order (PO)',
            ikon: 'pi-file-edit',
            rute: '/accounting/input/po',
            activate: true
        },
        {
            id: 'so',
            label: 'Sales Order (SO)',
            ikon: 'pi-file-export',
            rute: '/accounting/input/so',
            activate: true
        },
        {
            id: 'pengeluaran',
            label: 'Catat Pengeluaran',
            ikon: 'pi-wallet',
            rute: '/accounting/input/pengeluaran/buat',
            activate: true
        }
    ]

    const aktif = (ruteTujuan) => {
        if (!route) return false
        return route.path === ruteTujuan || route.path.startsWith(ruteTujuan + '/')
    }

    return {
        transaksi,
        aktif
    }
}
