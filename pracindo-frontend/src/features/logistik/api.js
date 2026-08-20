// src/features/logistik/api.js
import api from '@/utils/api'

export const apiKurir = {
    getTugasSaya: () => api.get('logistik/pengiriman/tugas-saya/').then(r => r.data),
    berangkatkanTugas: (id) => api.post(`logistik/pengiriman/${id}/berangkatkan/`).then(r => r.data),
    kirimPosisi: (id, payload) => api.post(`logistik/pengiriman/${id}/posisi/`, payload).then(r => r.data),
    tandaiSampai: (pengirimanId, perhentianId) => api.post(`logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/sampai/`).then(r => r.data),
    unggahBukti: (pengirimanId, perhentianId, formData, idemKey) => api.post(`logistik/pengiriman/${pengirimanId}/perhentian/${perhentianId}/bukti/`, formData, { headers: { 'Content-Type': 'multipart/form-data', 'Idempotency-Key': idemKey } }).then(r => r.data),
}
