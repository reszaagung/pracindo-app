import { ref } from 'vue'
import api from '@/utils/api'

export function useWorkOrder() {
    const isLoading = ref(false)
    const isSending = ref(false)
    const isCreating = ref(false)
    const isChatLoading = ref(false)

    const madingList = ref([])
    const staffList = ref([])

    const fetchMading = async () => {
        isLoading.value = true
        try {
            const response = await api.get('work-order/mading/')
            madingList.value = response.data.results || response.data
        } catch (error) {
            console.error("Gagal memuat mading Work Order:", error)
        } finally {
            isLoading.value = false
        }
    }

    const fetchStaff = async () => {
        try {
            const response = await api.get('work-order/staff/')
            staffList.value = response.data.results || response.data
        } catch (error) {
            console.error("Gagal memuat daftar staff:", error)
        }
    }

    const fetchChat = async (woId) => {
        isChatLoading.value = true
        try {
            const response = await api.get(`work-order/${woId}/pesan/`)
            return response.data.results || response.data
        } catch (error) {
            console.error("Gagal memuat pesan:", error)
            return []
        } finally {
            isChatLoading.value = false
        }
    }

    const createTask = async (payload) => {
        isCreating.value = true
        try {
            await api.post('work-order/', payload)
            await fetchMading()
            return { success: true }
        } catch (error) {
            console.error("Gagal membuat tugas:", error)
            const detailError = error.response?.data?.detail || JSON.stringify(error.response?.data)
            return { success: false, message: detailError || "Gagal menyimpan tugas baru." }
        } finally {
            isCreating.value = false
        }
    }

    const approveTask = async (woId, catatan = '') => {
        try {
            const response = await api.post(`work-order/${woId}/approve/`, { catatan })
            alert(response.data.detail || "Berhasil diperbarui!")
            await fetchMading()
            return true
        } catch (error) {
            alert(error.response?.data?.detail || "Gagal memproses persetujuan.")
            return false
        }
    }

    // FUNGSI BARU: Untuk Tutup Sesi Tugas (Menyembunyikan dari mading)
    const closeTask = async (woId) => {
        try {
            // PERHATIAN: Sesuaikan url /close/ ini dengan pengaturan view/endpoint Django Anda
            const response = await api.post(`work-order/${woId}/close/`)
            alert(response.data?.detail || "Sesi tugas berhasil ditutup.")
            await fetchMading()
            return true
        } catch (error) {
            console.error("Gagal menutup sesi:", error)
            alert(error.response?.data?.detail || "Gagal menutup sesi tugas.")
            return false
        }
    }

    const sendReply = async (woId, teksPesan) => {
        if (!teksPesan.trim()) return null
        isSending.value = true
        try {
            const response = await api.post(`work-order/${woId}/kirim_pesan/`, { teks: teksPesan })
            return response.data
        } catch (error) {
            console.error("Gagal mengirim pesan:", error)
            alert("Gagal mengirim pesan. Cek koneksi Anda.")
            return null
        } finally {
            isSending.value = false
        }
    }

    return {
        isLoading, isSending, isCreating, isChatLoading,
        madingList, staffList,
        fetchMading, fetchStaff, fetchChat, createTask, approveTask, closeTask, sendReply
    }
}
