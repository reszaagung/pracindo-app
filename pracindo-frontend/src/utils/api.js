import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/',
  headers: { Accept: 'application/json' },
})

const PUBLIK = ['auth/login/', 'auth/daftar/', 'auth/lupa-password/']
const endpointPublik = (url = '') => PUBLIK.some((p) => url.includes(p))

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('token')

  if (token && !endpointPublik(cfg.url)) {
    cfg.headers.Authorization = `Token ${token}`
  }
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const { response, config } = err

    if (!response) return Promise.reject(err)

    if (response.status === 401 && !endpointPublik(config?.url)) {
      localStorage.removeItem('token')
      localStorage.removeItem('profil')
      localStorage.removeItem('modul')

      const { default: router } = await import('@/router')
      const kini = router.currentRoute.value

      if (kini.name !== 'login') {
        router.push({
          name: 'login',
          query: { sesi: 'berakhir', next: kini.fullPath },
        })
      }
    }

    return Promise.reject(err)
  }
)



export default api