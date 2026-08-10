// src/features/distribusi/composables/useNavDistribution.js
import { useRoute } from 'vue-router'

export function useNavDistribution() {
    const route = useRoute()

    const menu = [
        {
            id: 'jadwal',
            label: 'Jadwal Pengiriman',
            ikon: 'pi-calendar-clock',
            rute: '/distribusi',
            activate: true
        },
        {
            id: 'muat',
            label: 'Validasi Muat (Loading)',
            ikon: 'pi-check-square',
            rute: '/distribusi/loading',
            activate: true
        },
        {
            id: 'armada',
            label: 'Status Armada',
            ikon: 'pi-truck',
            rute: '/distribusi/armada',
            activate: true
        },
        // 👇 TAMBAHKAN MENU KURIR DI SINI 👇
        {
            id: 'kurir',
            label: 'Tugas Kurir / Supir',
            ikon: 'pi-map',
            rute: '/distribusi/kurir',
            activate: true
        }
    ]

    const aktif = (ruteTujuan) => {
        if (!route) return false
        if (ruteTujuan === '/distribusi') {
            return route.path === '/distribusi'
        }
        return route.path.startsWith(ruteTujuan)
    }

    return { menu, aktif }
}