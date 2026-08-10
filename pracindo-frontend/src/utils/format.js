/**
 * utils/format.js
 * ================
 * ⚠ MENGGANTIKAN paymentHelper.js — file itu sebaiknya DIHAPUS.
 *
 * Kenapa calculatePOFinance dibuang:
 *
 * 1. Backend SUDAH mengirim `status_pembayaran` (UNPAID/PARTIAL/PAID) yang
 *    dihitung dengan row lock di catat_pembayaran(). Menghitung ulang di
 *    client = dua sumber kebenaran yang bisa berbeda.
 *
 * 2. Versi lama menjumlahkan SEMUA riwayat_pembayaran termasuk yang
 *    DIBATALKAN. Setelah fitur batalkan-pembayaran aktif, PO bisa terlihat
 *    lunas di layar padahal di database UNPAID.
 *
 * 3. PPN hardcode 0.11 mengabaikan `tarif_ppn` yang di-snapshot PER ITEM.
 *    PO lama dengan tarif berbeda akan salah hitung.
 *
 * 4. Subtotal dihitung `total_unit x harga_satuan`, padahal backend memakai
 *    `quantity x harga_satuan`. Untuk item dengan unit_kg != 1, hasilnya beda.
 *
 * Yang DIPERTAHANKAN: deteksi jatuh tempo — status OVERDUE memang tidak
 * dikirim backend, jadi itu memang urusan tampilan.
 */

export const rupiah = (n, { ringkas = false } = {}) => {
  const angka = Number(n || 0)
  if (ringkas && angka >= 1_000_000) {
    return `Rp ${(angka / 1_000_000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} jt`
  }
  return `Rp ${angka.toLocaleString('id-ID', { maximumFractionDigits: 0 })}`
}

/** Desimal dari DRF datang sebagai STRING — jangan asumsikan number. */
export const angka = (n, desimal = 0) =>
  Number(n || 0).toLocaleString('id-ID', {
    minimumFractionDigits: desimal,
    maximumFractionDigits: desimal,
  })

export const tanggal = (iso, { panjang = false } = {}) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('id-ID', panjang
    ? { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
    : { day: 'numeric', month: 'short', year: 'numeric' })
}

export const tanggalJam = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })} ${d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}`
}

/** "2 jam lagi" / "3 hari lalu" — untuk tenggat WO & jatuh tempo. */
export const jarakWaktu = (iso) => {
  if (!iso) return ''
  const selisih = new Date(iso) - Date.now()
  const jam = Math.round(selisih / 3_600_000)
  const hari = Math.round(jam / 24)

  if (Math.abs(jam) < 1) return 'sebentar lagi'
  if (jam > 0) return jam < 24 ? `${jam} jam lagi` : `${hari} hari lagi`
  return Math.abs(jam) < 24 ? `${Math.abs(jam)} jam lalu` : `${Math.abs(hari)} hari lalu`
}

/** Tanggal input HTML (YYYY-MM-DD) untuk hari ini, aman terhadap timezone. */
export const hariIni = () => {
  const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
  return t.toISOString().slice(0, 10)
}

/**
 * Satu-satunya bagian paymentHelper yang layak dipertahankan.
 * OVERDUE bukan status backend — itu turunan tanggal, murni tampilan.
 * @returns 'PAID' | 'OVERDUE' | 'UNPAID' | 'PARTIAL'
 */
export const statusTagihan = (po) => {
  if (po.status_pembayaran === 'PAID') return 'PAID'
  if (po.tanggal_jatuh_tempo && new Date() > new Date(po.tanggal_jatuh_tempo)) {
    return 'OVERDUE'
  }
  return po.status_pembayaran
}

/**
 * Sisa tagihan. Memakai total_po dari backend (yang sudah menghitung PPN
 * per item dengan tarif snapshot), dan HANYA menjumlahkan pembayaran yang
 * masih aktif — inilah yang keliru di paymentHelper lama.
 */
export const sisaTagihan = (po) => {
  const total = Number(po.total_po || 0)
  const dibayar = (po.riwayat_pembayaran || [])
    .filter(r => !r.dibatalkan_pada)
    .reduce((s, r) => s + Number(r.nominal_dibayar || 0), 0)
  return total - dibayar
}