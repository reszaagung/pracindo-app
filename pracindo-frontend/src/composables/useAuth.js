// src/composables/useAuth.js
import { ref, computed } from 'vue'
import api from '@/utils/api'
const token = ref(localStorage.getItem('token') || null)
const profil = ref(JSON.parse(localStorage.getItem('profil') || 'null'))
const modul = ref(JSON.parse(localStorage.getItem('modul') || '[]'))
const sedangProses = ref(false)


const PERAN_LABEL = {
    SUPERVISOR: 'Supervisor',
    STAFF: 'Staf',
    PRODUKSI: 'Produksi',
    GUDANG: 'Gudang',
    SALES: 'Sales',
    AKUNTING: 'Akunting',
}

export function useAuth() {
    const masuk = computed(() => !!token.value)
    const bisaAkses = (kode) => modul.value.some((m) => m.kode === kode)

    const kartu = computed(() => profil.value && {
        nama: profil.value.nama || profil.value.username || 'Pengguna',
        role: profil.value.role,
        role_display: PERAN_LABEL[profil.value.role] || profil.value.role || 'Staf',
        entitas_default_kode: profil.value.entitas_default_kode ?? null,
    })

    const simpan = (data) => {
        token.value = data.token
        profil.value = data.profil
        modul.value = data.modul || []

        localStorage.setItem('token', data.token)
        localStorage.setItem('profil', JSON.stringify(data.profil))
        localStorage.setItem('modul', JSON.stringify(data.modul || []))
    }

    const keluar = () => {
        token.value = null
        profil.value = null
        modul.value = []

        localStorage.removeItem('token')
        localStorage.removeItem('profil')
        localStorage.removeItem('modul')
    }

    const login = async (username, password) => {
        sedangProses.value = true
        try {
            const { data } = await api.post('auth/login/', { username, password })
            simpan(data)
            return { success: true, data }
        } catch (err) {
            const pesan = err.response?.data?.detail || 'Username atau password salah.'
            return { success: false, message: pesan }
        } finally {
            sedangProses.value = false
        }
    }

    const register = async (payload) => {
        sedangProses.value = true
        try {
            await api.post('auth/register/', payload)
            return { success: true }
        } catch (err) {
            const pesan = err.response?.data?.detail || 'Pendaftaran gagal. Username atau email mungkin sudah terdaftar.'
            return { success: false, message: pesan }
        } finally {
            sedangProses.value = false
        }
    }

    const logout_api = async () => {
        try {
            await api.post('auth/logout/')
        } catch (err) {
            console.warn('Logout API gagal atau sesi sudah berakhir di server:', err)
        } finally {
            keluar()
        }
    }

    return {
        token, profil, modul, sedangProses,
        masuk, bisaAkses, kartu,
        simpan, keluar, login, logout: logout_api,
        register
    }
}