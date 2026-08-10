import { useRoute } from 'vue-router'

export function useNavMonitorLayout() {
    const route = useRoute()

    // Daftar menu untuk Sidebar Monitor Inventory
    const menu = [
        {
            id: 'stok',
            label: 'Posisi Stok Gudang',
            ikon: 'pi-box',
            rute: '/inventory',
            activate: true
        },
        {
            id: 'tangki',
            label: 'Monitor Tangki',
            ikon: 'pi-database',
            rute: '/inventory/tangki',
            activate: true
        },
        {
            id: 'klaim-distribusi',
            label: 'Transaksi & Klaim Pool',
            ikon: 'pi-truck',
            rute: '/inventory/distribusi',
            activate: true
        }
    ]

    const aktif = (ruteTujuan) => {
        if (!route) return false

        // Logika khusus agar menu utama 'Stok' tetap menyala saat masuk ke detail stok atau mutasi
        if (ruteTujuan === '/inventory') {
            return route.path === '/inventory' || route.path.startsWith('/inventory/stok')
        }

        return route.path.startsWith(ruteTujuan)
    }

    return {
        menu,
        aktif
    }
}