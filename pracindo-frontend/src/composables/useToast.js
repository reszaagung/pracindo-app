import { useToast as usePrimeToast } from 'primevue/usetoast'

export function useToast() {
    const toast = usePrimeToast()

    return {
        success: (pesan) => {
            toast.add({ severity: 'success', summary: 'Berhasil', detail: pesan, life: 3000 })
        },
        error: (pesan) => {
            toast.add({ severity: 'error', summary: 'Gagal', detail: pesan, life: 4000 })
        },
        info: (pesan) => {
            toast.add({ severity: 'info', summary: 'Informasi', detail: pesan, life: 3000 })
        },
        warn: (pesan) => {
            toast.add({ severity: 'warn', summary: 'Peringatan', detail: pesan, life: 4000 })
        }
    }
}