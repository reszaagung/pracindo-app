import { computed } from 'vue'
import { useRoute } from 'vue-router'

export function useNavDistribution() {
    const route = useRoute()
    const menus = [
        {
            id: 'packaging',
            label: 'Pengemasan',
            ikon: 'pi-box',
            rute: '/warehouse/distribution/packaging',
            activate: true
        },
        {
            id: 'log-packaging',
            label: 'Riwayat Kemas',
            ikon: 'pi-history', // Ikon jam/riwayat
            rute: '/warehouse/distribution/logs',
            activate: true
        },
        {
            id: 'dispatch',
            label: 'Pengiriman',
            ikon: 'pi-truck',
            rute: '/warehouse/distribution/dispatch',
            activate: false
        }
    ]

    const aktif = (path) => {
        return computed(() => route.path.startsWith(path)).value
    }

    return {
        menus,
        aktif
    }
}
