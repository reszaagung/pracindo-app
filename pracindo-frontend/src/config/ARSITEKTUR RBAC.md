# Arsitektur RBAC & Visibilitas Modul (Frontend)

Dokumen ini menjelaskan alur *Role-Based Access Control* (RBAC) pada aplikasi *frontend* Pracindo dan bagaimana sistem memisahkan antara **hak akses otorisasi mutlak** (dari *backend*) dengan **visibilitas antarmuka pengguna** (di *frontend*).

> **Aturan pemeliharaan:** dokumen ini mengikuti kode, bukan sebaliknya. Setiap perubahan pada `src/composables/useAuth.js`, `src/config/modules.js`, atau `src/views/DashboardView.vue` wajib menyinkronkan snippet di §5. Jika ada selisih, perbarui dokumennya.

---

## 1. Filosofi Arsitektur: Single Source of Truth

Aplikasi ini menganut prinsip keamanan di mana **backend adalah satu-satunya sumber kebenaran (*Single Source of Truth*)**.

*   *Frontend* **tidak pernah** menentukan, memanipulasi, memperluas, atau memotong hak akses pengguna secara sepihak.
*   Segala penambahan atau pengurangan izin akses ke modul hanya boleh dilakukan di *backend* (`staff_user/permissions.py`; ringkasannya terdokumentasi di `SPEK-BACKEND.md`).
*   Tugas *frontend* hanyalah mencatat apa yang dikirimkan *backend* dan melindunginya di level klien (*router guard*).

---

## 2. Alur Otorisasi (Auth Flow)

1. **Autentikasi (LoginView):** pengguna login, *backend* merespons dengan data profil (termasuk `role` berformat UPPERCASE, contoh: `AKUNTING`) dan *array* `modul` yang diizinkan — mentah, menggunakan *key* `kode` (contoh: `[{ kode: 'akunting' }, { kode: 'inventory' }]`).
2. **Pencatatan state (`useAuth.js` — `simpan`):** fungsi ini mengambil `data.modul` mentah dari *backend* dan langsung menyimpannya ke memori (`modul.value`) dan `localStorage` **tanpa filter atau override apa pun**.
3. **Pengecekan akses (`guards.js`):** pelindung rute membaca `meta.modul` pada rute tujuan dan memanggil `useAuth().bisaAkses(kode)`. Pengecekan ini WAJIB dilakukan terhadap `modul.value` mentah (*key* `.kode`), bukan terhadap array hasil *mapping* UI.
4. **Proteksi final (backend API):** sekalipun *router guard* klien ditembus, seluruh *request* API ke modul tersebut tetap ditolak (`403 Forbidden`) oleh `permission_classes` di *backend* jika pengguna tidak sah.

---

## 3. Pemisahan Hak Akses vs Visibilitas UI

Ada kasus di mana pengguna **diizinkan** *backend* mengakses suatu modul, tetapi kartunya **tidak perlu** tampil di *Dashboard*. Dua contoh nyata di kode saat ini:

*   Role `AKUNTING` boleh membuka `/inventory` (backend mengirim modulnya — lihat `SPEK-BACKEND.md` bagian inventory), tetapi kartu Inventory bukan prioritas operasional mereka.
*   Modul `dashboard` dikirim *backend* ke hampir semua role, tetapi kartu "buka dashboard" di halaman dashboard sendiri tidak berguna.

Solusinya: **filter tata letak visual** melalui dua *flag* UI murni di `config/modules.js`:

*   `sembunyiDiDashboardUntuk: ['ROLE_NAME']` — sembunyikan kartu untuk role tertentu.
*   `sembunyiDiDashboard: true` — sembunyikan kartu untuk semua role.

Kedua *flag* ini **hanya menyaring kartu di Dashboard**. Keduanya tidak menyentuh *state* otorisasi maupun *router guard* — rute tetap hidup dan bisa diakses langsung via URL selama *backend* memang mengirim modulnya.

---

## 4. Perhatian Khusus (Gotchas)

1. **Jebakan `kode` vs `id`.** Data mentah dari *backend* memakai *key* `kode`; hasil *mapping* `modulDariBackend` mengubahnya menjadi `id`. **`bisaAkses` harus selalu dipanggil terhadap data mentah (`modul.value`).** Jika tertukar dengan hasil *mapping*, seluruh cek akses menjadi `false` secara diam-diam, tanpa error.
2. **Ekspor `kartu`, `modul`, dan `logout`.** `DashboardView` mendestrukturisasi `{ kartu, modul, logout }` dari `useAuth()`. `kartu` adalah *computed* berisi `nama`, `role`, `role_display`, `entitas_default_kode`; `logout` adalah alias dari `logout_api`. Menghapus salah satunya dari objek *return* `useAuth` memicu `ReferenceError`/`TypeError` saat *render*.
3. **Properti `roles` sengaja TIDAK ada di katalog `modules.js`.** Dulu ada dan dipakai blok override di `simpan()` — anti-pattern yang sudah dihapus. Jangan menambahkannya kembali sebagai logika akses dalam bentuk apa pun; daftar role otoritatif per modul hanya hidup di *backend*. Menambahkan filter berbasis `roles` di *frontend* berarti menghidupkan lagi anti-pattern override.
4. **Papan tugas (work order) sudah dicabut dari `DashboardView`.** `useWorkOrder.js` tidak ada lagi di *tree*, dan variabel `hitungan` (counter kartu) ikut hilang. Jika fitur ini dihidupkan lagi, jangan mendestrukturisasi properti dari *composable* tanpa memastikan properti itu benar-benar ada di objek *return*-nya — itulah sumber `TypeError` versi lama.

---

## 5. Implementasi (sinkron dengan kode)

Snippet di bawah adalah cuplikan dari kode aktual. Bagian yang tidak relevan diringkas dengan `...`.

### A. `src/config/modules.js` — katalog & flag UI

```javascript
export const MODUL = [
  {
    id: 'dashboard',
    // ...
    // Backend mengirim modul 'dashboard' ke hampir semua role; kartu
    // "buka dashboard" di halaman dashboard sendiri tidak berguna.
    sembunyiDiDashboard: true,
    menu: [],
  },
  {
    id: 'inventory',
    nama: 'Inventory',
    rute: '/inventory',
    siap: true,
    // AKUNTING punya akses rute /inventory (backend kirim modulnya — lihat
    // SPEK-BACKEND.md), tapi kartunya tidak perlu memenuhi dashboard mereka.
    // Murni urusan tampilan, bukan otorisasi.
    sembunyiDiDashboardUntuk: ['AKUNTING'],
    menu: [ /* ... */ ],
  },
  // ... modul lainnya — TANPA properti `roles` (lihat §4.3)
]

export const cariModul = (id) => MODUL.find((m) => m.id === id) ?? null

export const modulDariBackend = (modulBackend = []) =>
  modulBackend.map((mb) => {
    const lokal = cariModul(mb.kode)
    return {
      id: mb.kode,
      // ...
      siap: lokal?.siap ?? false,
      // Flag visibilitas kartu dashboard — hanya memengaruhi TAMPILAN kartu,
      // tidak pernah dipakai untuk otorisasi (guard tetap baca modul mentah).
      sembunyiDiDashboardUntuk: lokal?.sembunyiDiDashboardUntuk || [],
      sembunyiDiDashboard: lokal?.sembunyiDiDashboard || false,
      menu: lokal?.menu ?? [],
    }
  })
```

### B. `src/composables/useAuth.js` — state bersih tanpa override

```javascript
const PERAN_LABEL = {
  // ...
  AKUNTING: 'Akunting', // ejaan role mengikuti backend (SPEK-BACKEND.md)
}

// Beroperasi PADA DATA MENTAH backend (key .kode) — dipanggil router guard
const bisaAkses = (kode) => modul.value.some((m) => m.kode === kode)

const simpan = (data) => {
  token.value = data.token
  profil.value = data.profil

  // Single Source of Truth: terima mentah-mentah dari backend,
  // tanpa filter/override lokal.
  modul.value = data.modul || []

  localStorage.setItem('token', data.token)
  localStorage.setItem('profil', JSON.stringify(data.profil))
  localStorage.setItem('modul', JSON.stringify(modul.value))
}

return {
  token, profil, modul, sedangProses,
  masuk, bisaAkses, kartu,
  simpan, keluar, login, logout: logout_api,
  register,
}
```

### C. `src/views/DashboardView.vue` — filter UI

```javascript
import { useAuth } from '@/composables/useAuth'
import { modulDariBackend } from '@/config/modules'

const { kartu, modul, logout } = useAuth()

// Filter KARTU TAMPILAN saja — otorisasi tetap milik backend
// (di useAuth + guard). Jangan pernah memutasi modul.value di sini.
const modulSaya = computed(() => {
  const roleUser = kartu.value?.role || ''
  return modulDariBackend(modul.value).filter(
    (m) => !m.sembunyiDiDashboard && !m.sembunyiDiDashboardUntuk.includes(roleUser),
  )
})
```