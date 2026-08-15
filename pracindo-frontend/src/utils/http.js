/**
 * Klien HTTP bersama SELURUH fitur.
 *
 * SATU TEMPAT UNTUK MENAFSIRKAN GALAT
 *
 *   Backend membedakan 409 (kenyataan menolak) dari 422 (isian salah)
 *   dari 500+InvariantMelenceng (rupiah tercipta atau menguap). Kalau
 *   tiap fitur menanganinya sendiri, ketiganya cepat atau lambat
 *   berakhir sebagai "terjadi kesalahan" -- dan pelanggaran invariant
 *   tersembunyi di antara typo isian, persis jenis kegagalan yang tidak
 *   pernah dilaporkan siapa pun.
 */
import axios from 'axios'
import { API_BASE, API_TIMEOUT } from '@/config/api'

export const http = axios.create({
    baseURL: API_BASE,
    timeout: API_TIMEOUT,
    headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((cfg) => {
    const token = localStorage.getItem('token')
    if (token) cfg.headers.Authorization = `Token ${token}`
    return cfg
})

export class GalatApi extends Error {
    constructor({ status, kode, pesan, field, raw }) {
        super(pesan)
        this.name = 'GalatApi'
        Object.assign(this, { status, kode, pesan, field, raw })
    }

    /** 409: saldo berubah sejak layar dimuat. Segarkan, jangan retry. */
    get konflikSaldo() { return this.status === 409 }

    /** 400/422: operator bisa memperbaikinya sendiri. */
    get bisaDiperbaiki() { return this.status === 400 || this.status === 422 }

    /** Token 12 jam habis. */
    get sesiHabis() { return this.status === 401 }

    /**
     * Rupiah tercipta atau menguap. Transaksi SUDAH di-rollback di server,
     * jadi datanya aman -- tapi ada yang salah secara sistemik, dan angka
     * di layar mana pun tidak boleh dipercaya sampai diperiksa.
     */
    get invariantMelenceng() {
        return this.status === 500 && this.kode === 'InvariantMelenceng'
    }
}

http.interceptors.response.use(
    (r) => r,
    (err) => {
        const res = err.response
        if (!res) {
            return Promise.reject(new GalatApi({
                status: 0, kode: 'JARINGAN',
                pesan: 'Tidak bisa menghubungi server.',
            }))
        }
        const d = res.data || {}
        const g = new GalatApi({
            status: res.status,
            kode: d.kode || `HTTP_${res.status}`,
            pesan: d.pesan || d.detail || 'Permintaan ditolak.',
            field: d.field,
            raw: d,
        })
        if (g.sesiHabis) {
            localStorage.removeItem('token')
            window.location.assign('/login')
        }
        return Promise.reject(g)
    },
)