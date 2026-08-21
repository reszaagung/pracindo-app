import api from '@/utils/api'

export const retailApi = {
  getKatalog: () => api.get('retail/pos/katalog/').then(r => r.data),
  checkout: (payload) => api.post('retail/pos/checkout/', payload).then(r => r.data),
  getRiwayat: () => api.get('retail/riwayat/').then(r => r.data),
  getSesiAktif: () => api.get('retail/sesi/').then(r => r.data),
  tutupShift: () => api.post('retail/sesi/').then(r => r.data)
}
