// src/features/distribusi/api.js
import api from '@/utils/api'

export const apiDistribusi = {
    getDistribusiTersedia: (entitasId = '') => api.get(`logistik/distribusi-tersedia/?entitas=${entitasId}`).then(r => r.data),
    rakitPengiriman: (payload) => api.post('logistik/pengiriman/', payload).then(r => r.data),
    getSemuaPengiriman: (params) => api.get('logistik/pengiriman/', { params }).then(r => r.data),
    getDetailPengiriman: (id) => api.get(`logistik/pengiriman/${id}/`).then(r => r.data),
    hitungRute: (id, pakaiUsulan = false) => api.post(`logistik/pengiriman/${id}/hitung-rute/`, { pakai_usulan: pakaiUsulan }).then(r => r.data),
    getArmada: () => api.get('logistik/kendaraan/').then(r => r.data)
}
