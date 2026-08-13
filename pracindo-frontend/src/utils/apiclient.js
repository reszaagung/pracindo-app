/* ===============================================================
   apiClient.js — transport + autentikasi

   KENAPA BERKAS INI ADA
   Backend membalas 401, bukan 403. DRF hanya melakukan itu kalau
   authenticator pertama punya authenticate_header() -- artinya proyek
   memakai TokenAuthentication atau JWT, bukan SessionAuthentication.
   `credentials: 'include'` saja tidak akan pernah lolos.

   TOKEN TIDAK BOLEH ADA DI SOURCE. Yang di-hardcode ikut ter-bundle ke
   setiap browser dan bisa dibaca lewat DevTools. Di sini token hanya
   masuk dari hasil login saat runtime.
   =============================================================== */

export const BASE = '/api/v1'
export const SKEMA = 'Token'

const RUTE_LOGIN = `${BASE}/auth/token/`
const KUNCI = 'pracindo.token'

let tokenMemori = sessionStorage.getItem(KUNCI) || null

export function simpanToken(t) {
    tokenMemori = t || null
    if (t) sessionStorage.setItem(KUNCI, t)
    else sessionStorage.removeItem(KUNCI)
}

export function hapusToken() { simpanToken(null) }
export function sudahLogin() { return Boolean(tokenMemori) }


function csrfToken() {
    return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)?.[1] ?? ''
}

function header(tambahan = {}) {
    const h = { Accept: 'application/json', ...tambahan }
    if (tokenMemori) h.Authorization = `${SKEMA} ${tokenMemori}`

    const csrf = csrfToken()
    if (csrf) h['X-CSRFToken'] = csrf
    return h
}


export class GalatApi extends Error {
    constructor(pesan, { status, rincian, perField, skemaAuth }) {
        super(pesan)
        this.name = 'GalatApi'
        this.status = status
        this.rincian = rincian
        this.perField = perField
        this.skemaAuth = skemaAuth
        this.butuhLogin = status === 401
    }
}

async function bacaGalat(r) {
    let isi
    try { isi = await r.json() } catch { isi = { detail: `HTTP ${r.status}` } }

    if (r.status === 401) {
        const skema = r.headers.get('WWW-Authenticate')
        hapusToken()
        return new GalatApi(
            isi.detail || 'Sesi berakhir. Masuk kembali.',
            { status: 401, rincian: isi, perField: {}, skemaAuth: skema },
        )
    }

    const perField = {}
    let pesan = isi.detail
    if (!pesan) {
        for (const [k, v] of Object.entries(isi)) {
            perField[k] = Array.isArray(v) ? v.join(' ') : String(v)
        }
        pesan = Object.entries(perField).map(([k, v]) => `${k}: ${v}`).join('\n')
            || `HTTP ${r.status}`
    }
    return new GalatApi(pesan, { status: r.status, rincian: isi, perField })
}


export async function apiGet(url, params = {}) {
    const q = new URLSearchParams(
        Object.entries(params).filter(
            ([, v]) => v !== null && v !== '' && v !== undefined)
    )
    const r = await fetch(`${url}?${q}`, {
        credentials: 'include',
        headers: header(),
    })
    if (!r.ok) throw await bacaGalat(r)
    return r.json()
}

export async function apiGetList(url, params = {}) {
    const d = await apiGet(url, params)
    return Array.isArray(d) ? d : (d.results ?? [])
}

export async function apiPost(url, body) {
    const r = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: header({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
    })
    if (!r.ok) throw await bacaGalat(r)
    return r.json()
}

export async function login(username, password) {
    const r = await fetch(RUTE_LOGIN, {
        method: 'POST',
        credentials: 'include',
        headers: header({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ username, password }),
    })
    if (!r.ok) throw await bacaGalat(r)
    const d = await r.json()
    const t = d.token ?? d.access
    if (!t) {
        throw new GalatApi(
            'Balasan login tidak memuat token. Periksa RUTE_LOGIN.',
            { status: 500, rincian: d, perField: {} },
        )
    }
    simpanToken(t)
    return d
}

export function logout() { hapusToken() }