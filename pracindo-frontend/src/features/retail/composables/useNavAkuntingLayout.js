import { useRoute, useRouter } from 'vue-router'
import { useLayout } from '@/composables/useLayout'

export function useNavAkuntingLayout() {
    const route = useRoute()
    const router = useRouter()

    // Kita tetap mengambil fungsi tutup menu mobile dari useLayout utama
    const { tutupDiMobile } = useLayout()

    const menuAkuntansi = [
        {
            id: 'buku-besar',
            label: 'Buku Besar',
            rute: '/akuntansi/buku-besar',
            ikon: 'pi-book'
        },
        {
            id: 'buku-jurnal',
            label: 'Buku Jurnal Umum',
            rute: '/akuntansi/jurnal',
            ikon: 'pi-folder-open'
        },
        {
            id: 'entri-jurnal',
            label: 'Entri Jurnal',
            rute: '/akuntansi/jurnal/entri',
            ikon: 'pi-file-edit'
        },
        {
            id: 'laporan',
            label: 'Laporan Keuangan',
            rute: '/akuntansi/laporan',
            ikon: 'pi-receipt'
        }
    ]

    const aktif = (path) => route.path.startsWith(path)

    const kembali = () => router.push('/')

    const klikMenu = (menu) => {
        router.push(menu.rute)
        tutupDiMobile()
    }

    return {
        menuAkuntansi,
        aktif,
        kembali,
        klikMenu
    }
}
