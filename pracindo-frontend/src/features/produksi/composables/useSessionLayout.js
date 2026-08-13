// src/composables/useNavSession.js
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export function useNavSession() {
    const route = useRoute()
    const router = useRouter()

    const sidebarAktif = ref(false)
    const isMobile = ref(false)
    const notifikasi = ref(null)
    let timerNotifikasi = null

    const cekLayar = () => {
        isMobile.value = window.innerWidth < 1024
        if (!isMobile.value) sidebarAktif.value = true
        else sidebarAktif.value = false
    }

    onMounted(() => {
        cekLayar()
        window.addEventListener('resize', cekLayar)
    })

    onUnmounted(() => {
        window.removeEventListener('resize', cekLayar)
        if (timerNotifikasi) clearTimeout(timerNotifikasi)
    })

    const toggleSidebar = () => sidebarAktif.value = !sidebarAktif.value
    const tutupDiMobile = () => { if (isMobile.value) sidebarAktif.value = false }
    const navigasi = (ruteTujuan) => { router.push(ruteTujuan); tutupDiMobile() }
    const kembaliKeUtama = (ruteDasar = '/') => router.push(ruteDasar)
    const isAktif = (path) => route.path === path || route.path.startsWith(path + '/')

    watch(() => route.fullPath, tutupDiMobile)

    const setNotifikasi = (pesan, tipe = 'sukses', durasi = 5000) => {
        if (timerNotifikasi) clearTimeout(timerNotifikasi)
        notifikasi.value = { pesan, tipe }
        if (durasi > 0) timerNotifikasi = setTimeout(tutupNotifikasi, durasi)
    }
    const tutupNotifikasi = () => notifikasi.value = null

    return { route, sidebarAktif, isMobile, notifikasi, toggleSidebar, tutupDiMobile, navigasi, kembaliKeUtama, isAktif, setNotifikasi, tutupNotifikasi }
}