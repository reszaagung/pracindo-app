/**
 * Format dan parse. TIDAK MENGHITUNG.
 *
 * Setiap rupiah di layar berasal dari endpoint pratinjau atau dari
 * respons posting. Frontend tidak pernah mengalikan qty dengan harga
 * sendiri -- dua tempat yang menghitung hal sama akan berbeda;
 * pertanyaannya hanya kapan, dan bedanya baru ketahuan saat ada yang
 * menagih.
 *
 * Backend mengirim SEMUA angka sebagai string. parseFloat merusak sen
 * pada nilai besar, dan kerusakannya menumpuk diam-diam.
 */
import Decimal from 'decimal.js'

Decimal.set({ precision: 28, rounding: Decimal.ROUND_HALF_UP })

export function d(v) {
    if (v === null || v === undefined || v === '') return new Decimal(0)
    try { return new Decimal(String(v)) } catch { return new Decimal(0) }
}

const ribuan = (s) => s.replace(/\B(?=(\d{3})+(?!\d))/g, '.')

export const formatRp = (v) => `Rp ${ribuan(d(v).toFixed(2))}`
export const formatKg = (v, n = 3) => `${ribuan(d(v).toFixed(n))} Kg`
export const formatHarga = (v) => `Rp ${ribuan(d(v).toFixed(2))}/Kg`

/** Input pengguna -> string 3 desimal siap kirim, atau null kalau tak valid. */
export function normalKg(v) {
    const n = d(String(v ?? '').replace(',', '.'))
    return n.isNaN() || n.lte(0) ? null : n.toFixed(3)
}

export const nol = (v) => d(v).isZero()
export const positif = (v) => d(v).gt(0)
export const negatif = (v) => d(v).lt(0)