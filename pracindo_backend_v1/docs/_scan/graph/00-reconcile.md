# FASE 0 — REKONSILIASI JUMLAH ENDPOINT

**Putusan: angka final = 152 pasangan `method + path` unik.**
Dipakai sebagai target validator (`type=endpoint` di `graph.json` harus 152).

Dibuktikan ulang dengan skrip yang bisa dijalankan siapa pun:

```
python docs/_scan/graph/_reconcile.py     # membandingkan 3 sumber
python docs/_scan/graph/_endpoints.py     # menghasilkan graph/endpoints.json (152 baris)
```

---

## 1. Selisih 151 vs 107 — sebabnya bukan endpoint yang hilang

Perbandingan awal **apel vs jeruk**:

| Angka | Sebenarnya menghitung apa |
|---|---|
| **151** di `01-api-map.md` | pasangan `method+path` di `openapi.yaml` |
| **107** di `api-map.json` | **entri** JSON, bukan pasangan — satu entri boleh memampatkan beberapa method (`"GET\|POST\|PUT\|PATCH\|DELETE"`) dan dua path (`"/api/v1/auth/jabatan/ , /{id}/"`) |

Pemampatan itu terukur:

| | jumlah |
|---|---|
| entri `api-map.json` | 107 |
| entri dengan method majemuk (`\|`) | 12 |
| entri dengan path majemuk (`,`) | 16 |
| entri tunggal murni | 83 |
| **hasil ekspansi kasar** | **163** |

Jadi 107 entri **melebihi** 151, bukan kurang. Selisih 44 = 151 − 107 tidak
pernah berarti "44 endpoint hilang".

---

## 2. Cross-check tiga sumber (sebelum perbaikan)

| Sumber | Cara hitung | Hasil |
|---|---|---|
| **A. Resolver Django** — `get_resolver()` ditelusuri rekursif, `(?P<pk>…)` dinormalkan jadi `{id}` | pasangan method+path unik | **152** |
| **B. `openapi.yaml`** — drf-spectacular | pasangan method+path | **151** |
| **C. `api-map.json`** — ekspansi `\|` dan `,` | pasangan unik | 163 (kasar), **148 benar** |

Yang **dibuang** resolver secara sengaja, supaya angkanya bermakna:

| Kategori | Jumlah | Alasan |
|---|---|---|
| Varian sufiks format (`…\.(?P<format>[a-z0-9]+)`) | **96** | duplikat murni dari route yang sama, dibuat `DefaultRouter`; tidak menambah kemampuan |
| `APIRootView` (`GET /api/v1/<app>/`) | **9** | indeks navigasi bawaan router untuk 9 app ber-router (auth, master, inventory, akunting, keuangan, warehouse, produksi, work-order, core); bukan endpoint domain |
| Route di luar `api/` (admin Django + static) | 233 | di luar cakupan API |

> Total route terdaftar di URLconf = 152 + 96 + 9 = **257** pola `api/…`.

---

## 3. Tiga selisih nyata yang ditemukan — dan putusannya

### 3.1 Resolver 152 vs OpenAPI 151 → selisih **1**

| Endpoint | Sebab | Putusan |
|---|---|---|
| `GET /api/docs/` (`pracindo_erp/urls.py:13`) | `SpectacularSwaggerView` **tidak mendokumentasikan dirinya sendiri**; `SpectacularAPIView` (`/api/schema/`) ikut tampil, viewer-nya tidak | **Bukan cacat kode.** Endpoint nyata dan bisa dipanggil → **masuk hitungan**. Angka 151 adalah artefak generator, bukan kebenaran. |

Tidak ada satu pun path di OpenAPI yang tidak ada di resolver (`openapi − resolver = ∅`),
jadi schema tidak mengarang endpoint.

### 3.2 `api-map.json` kelebihan **15** pasangan (kartesian palsu)

Empat entri majemuk menghasilkan kombinasi method×path yang **tidak ada di URLconf**:

| Entri di `api-map.json` | Ekspansi | Nyata | Palsu |
|---|---|---|---|
| `GET\|POST\|PUT\|PATCH\|DELETE` × `/auth/jabatan/ , /{id}/` | 10 | 6 | 4 — `PUT/PATCH/DELETE` pada list, `POST` pada detail |
| `GET\|POST\|PUT\|PATCH\|DELETE` × `/auth/kepegawaian/ , /{id}/` | 10 | 6 | 4 |
| `GET\|POST\|PUT\|PATCH\|DELETE` × `/warehouse/packaging/ , /{id}/` | 10 | 6 | 4 |
| `POST\|PUT\|PATCH` × `/master/suplier/ , /{id}/` | 6 | 3 | 3 |
| | | | **15** |

**Sebab:** notasi ringkas untuk keterbacaan manusia, tapi tidak sah dibaca mesin —
`DefaultRouter` memasang `list/create` di path list dan
`retrieve/update/partial_update/destroy` di path detail, bukan semua method di
kedua path.
**Putusan:** entri dipecah jadi pasangan list vs detail yang eksplisit.

### 3.3 `api-map.json` kekurangan **4** pasangan

| Endpoint | Sebab |
|---|---|
| `GET /api/v1/master/produk/{id}/` | entri detail hanya menulis `PUT\|PATCH`; `retrieve` terlewat |
| `GET /api/v1/master/suplier/{id}/` | tercakup entri majemuk yang salah bentuk (§3.2) |
| `GET /api/schema/` | endpoint infrastruktur, sebelumnya tidak dicatat |
| `GET /api/docs/` | idem |

**Putusan:** keempatnya ditambahkan.

---

## 4. Perbaikan yang diterapkan pada `api-map.json`

> **Catatan lokasi berkas.** Instruksi umum menetapkan `docs/_scan/graph/`
> sebagai satu-satunya tempat menulis, tapi FASE 0 memerintahkan eksplisit
> *"Kalau api-map.json kurang → lengkapi sampai konsisten"*. Karena itu
> `docs/_scan/api-map.json` **adalah satu-satunya berkas di luar `graph/` yang
> disentuh**. Tidak ada kode aplikasi yang diubah.

| Aksi | Entri |
|---|---|
| Dipecah jadi list + detail | `auth/jabatan`, `auth/kepegawaian`, `warehouse/packaging`, `master/suplier` |
| Ditambah | `GET /master/produk/{id}/`, `GET /master/suplier/{id}/`, `GET /api/schema/`, `GET /api/docs/` |

Hasil setelah perbaikan (keluaran `_reconcile.py` apa adanya):

```
A. Resolver Django      : 152 pasangan method+path unik
   dibuang: format-suffix=96, APIRootView=9, non-api=233
B. openapi.yaml         : 151 pasangan (dari 151 baris)
C. api-map.json         : 152 pasangan hasil ekspansi (dari 115 entri)

--- ADA DI RESOLVER, TIDAK DI OPENAPI ---
    GET /api/docs/
--- ADA DI OPENAPI, TIDAK DI RESOLVER ---

--- ADA DI RESOLVER, TIDAK DI API-MAP.JSON  (kekurangan api-map) ---
    total kurang: 0

--- ADA DI API-MAP.JSON, TIDAK DI RESOLVER  (salah tulis) ---
    total kelebihan: 0
```

`api-map.json` sekarang 115 entri yang mengekspansi **tepat 152** pasangan,
identik dengan resolver. Satu-satunya selisih yang tersisa terhadap OpenAPI
adalah `/api/docs/` — dijelaskan di §3.1 dan **bukan** cacat.

---

## 5. Komposisi 152 endpoint kanonik

Dari `graph/endpoints.json` (dihasilkan `_endpoints.py`):

| Status | Jumlah | Arti |
|---|---|---|
| `live` | **127** | berfungsi normal |
| `ghost` | **16** | operasi tulis yang **selalu** membalas 405 (§6) |
| `dead` | **9** | seluruh `work_order` — modul tidak berfungsi karena `profil_staff_id` bukan atribut `Profil` (temuan H2) |
| **total** | **152** | |

Per app:

| App | Endpoint | | App | Endpoint |
|---|---|---|---|---|
| `staff_user` | 34 | | `master` | 12 |
| `akunting` | 30 | | `core` | 9 |
| `warehouse` | 25 | | `produksi` | 9 |
| `inventory` | 15 | | `work_order` | 9 *(semua dead)* |
| `keuangan` | 7 | | `pracindo_erp` | 2 *(schema + docs)* |
| `dokumen` · `pajak` · `sales_order` · `logistik` | **0** | | | |

Penanda lain yang ikut terekam di `endpoints.json`:

| Penanda | Jumlah | Keterangan |
|---|---|---|
| `permission` = `AllowAny` atau `NONE->IsAuthenticated` | **10** | 3 `AllowAny` (daftar/register/login) + 7 endpoint `keuangan` tanpa `permission_classes` (temuan C1) |
| `always_400` | **3** | `DELETE` yang membalas 400 lewat `perform_destroy`, bukan 405 |
| `multi_table_no_atomic` | **3** | `POST /auth/login/`, `POST /produksi/sesi/{id}/mulai/`, `POST /work-order/` |
| `permission` = `UNKNOWN` | **0** | seluruh 152 endpoint terpetakan permission-nya |

---

## 6. Daftar 16 operasi "hantu" (status `ghost`)

Terdaftar di URLconf dan didokumentasikan OpenAPI, tapi handler-nya selalu
mengembalikan `405 Method Not Allowed`:

| # | Operasi | Handler |
|---|---|---|
| 1-3 | `PUT` `PATCH` `DELETE` `/api/v1/akunting/purchase-order/{id}/` | `akunting/views.py:148,156` |
| 4 | `POST /api/v1/akunting/faktur/` | `akunting/views.py:244` |
| 5-7 | `PUT` `PATCH` `DELETE` `/api/v1/akunting/faktur/{id}/` | `akunting/views.py:251,260` |
| 8-10 | `PUT` `PATCH` `DELETE` `/api/v1/warehouse/penerimaan/{id}/` | `warehouse/views.py:120,129` |
| 11-13 | `PUT` `PATCH` `DELETE` `/api/v1/warehouse/laporan-selisih/{id}/` | `warehouse/views.py:183,192` |
| 14-16 | `PUT` `PATCH` `DELETE` `/api/v1/produksi/sesi/{id}/` | `produksi/views.py:33,39` |

Ketiga `DELETE` yang membalas **400** (bukan 405) sengaja **tidak** dihitung
sebagai ghost karena perilakunya berbeda — statusnya `live` dengan penanda
`always_400`: `/auth/profil/{id}/` (`staff_user/views.py:165`),
`/master/produk/{id}/` dan `/master/suplier/{id}/` (`master/views.py:24`).

---

## 7. Berkas keluaran fase ini

| Berkas | Isi |
|---|---|
| `graph/_reconcile.py` | skrip pembanding 3 sumber (bisa dijalankan ulang) |
| `graph/_reconcile.json` | keluaran mentah: 152 route resolver + daftar selisih |
| `graph/_endpoints.py` | pembangun daftar kanonik yang diperkaya |
| `graph/endpoints.json` | **152 baris** endpoint + app, view, action, permission, status, write, atomic, flag |
| `graph/00-reconcile.md` | dokumen ini |

**Tidak ada yang UNKNOWN pada fase ini** — seluruh 152 endpoint terverifikasi
dari kode (resolver), dan seluruhnya punya pemetaan permission.
