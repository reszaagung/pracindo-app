/**
 * Status keseimbangan sistem.
 *
 * Ditaruh di store global, bukan di fitur mana pun, karena
 * pelanggarannya menyentuh SEMUA layar sekaligus. Kalau invariant
 * melenceng, laporan penjualan, kartu stok, dan rekap hutang semuanya
 * menampilkan angka yang salah -- masing-masing dengan tenang.
 *
 * Angka yang salah tidak pernah mengumumkan diri sendiri. Store ini
 * yang mengumumkannya.
 */
import { defineStore } from 'pinia'
import { http } from '@/utils/http'

export const usePemeriksaanStore = defineStore('pemeriksaan', {
    state: () => ({
        status: null,   
        selisih: '0.00',
        catatan: [],
        diperiksa: null,
        memuat: false,
    }),

    getters: {
        melenceng: (s) => s.status === 'MELENCENG',
    },

    actions: {
        async periksa() {
            this.memuat = true
            try {
                const { data } = await http.get('/inventory/pemeriksaan/')
                this.status = data.status
                this.selisih = data.selisih
                this.catatan = data.catatan
                this.diperiksa = new Date()
            } finally {
                this.memuat = false
            }
        },
    },
})