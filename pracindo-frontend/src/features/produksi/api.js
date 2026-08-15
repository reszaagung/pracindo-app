import { http } from '@/utils/http'

// 1. SISIPKAN 'v1' DI SINI (Hilangkan garis miring di depan)
const P = 'v1/produksi'

export const apiTangki = {
  daftar: (params) => http.get(`${P}/tangki/`, { params }).then((r) => r.data),
  buat: (data) => http.post(`${P}/tangki/`, data).then((r) => r.data),
  saldo: (id) => http.get(`${P}/tangki/${id}/saldo/`).then((r) => r.data),
  ubah: (id, payload) => http.patch(`${P}/tangki/${id}/`, payload).then((r) => r.data),
  hapus: (id) => http.delete(`${P}/tangki/${id}/`)
}

export const apiBatch = {
  daftar: (params) => http.get(`${P}/batch/`, { params }).then((r) => r.data),
  detail: (id) => http.get(`${P}/batch/${id}/`).then((r) => r.data),
  buat: (payload) => http.post(`${P}/batch/`, payload).then((r) => r.data),
  ubah: (id, payload) => http.patch(`${P}/batch/${id}/`, payload).then((r) => r.data),
  hapus: (id) => http.delete(`${P}/batch/${id}/`),

  posting: (id) => http.post(`${P}/batch/${id}/post/`).then((r) => r.data),
  void: (id, alasan) => http.post(`${P}/batch/${id}/void/`, { alasan }).then((r) => r.data),

  saldo: (id) => http.get(`${P}/batch/${id}/saldo/`).then((r) => r.data),
  komposisi: (id) => http.get(`${P}/batch/${id}/komposisi/`).then((r) => r.data),

  tersedia: (tangki) => http.get(`${P}/batch/tersedia/`, { params: { tangki } }).then((r) => r.data),
  nomorBaru: (jenis) => http.get(`${P}/batch/nomor-baru/`, { params: { jenis } }).then((r) => r.data),
}

export const apiPratinjau = (payload) =>
  http.post(`${P}/pratinjau/`, payload).then((r) => r.data)

export const apiRawUntukProduksi = {
  // 2. SISIPKAN 'v1' JUGA DI SINI UNTUK RAW INVENTORY
  daftar: () => http.get('v1/inventory/raw/', { params: { aktif: true } }).then((r) => r.data),
}