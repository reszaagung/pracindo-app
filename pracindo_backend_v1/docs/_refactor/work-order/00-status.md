# FASE 0 — STATUS SEBENARNYA `work_order`

Sumber kebenaran = kode + resolver Django + state DB, **bukan** `docs/_scan/`.
Semua angka di bawah bisa direproduksi:

```
python docs/_refactor/work-order/_status_wo.py
```

READ-ONLY: skrip itu hanya membaca URLconf, tabel `information_schema`, dan
`SELECT COUNT(*)`. Tidak ada `INSERT`/`UPDATE`/`DELETE`/`CREATE`.

---

## 0. Putusan utama — laporan scan BASI untuk app ini

`docs/_scan/` di-commit di **`ea998b4`**. Commit berikutnya, **`e05535e`**
(*"merombak work order menjadi sistem chatting dan pesanan produksi"*,
Wed Aug 5 2026 20:25:57 +0700), **menulis ulang `work_order` sesudah scan
dibuat**:

| Berkas | Perubahan di `e05535e` |
|---|---|
| `work_order/views.py` | +112 / −… — tambah `kirim_pesan`, ganti permission |
| `work_order/models.py` | +89 — tambah `DetailPesananProduksi`, `WorkOrderPesan` |
| `work_order/serializers.py` | +55 — tambah `@transaction.atomic`, `pic_id`, chat |
| `work_order/permissions.py` | +24 — berkas baru `CanAksesWorkOrder` |
| `work_order/services.py` | +25 — dua stub `pass` |
| `work_order/migrations/0001_initial.py` | **+33 / −2 — DIEDIT DI TEMPAT** |

Akibatnya beberapa temuan scan sudah **tidak berlaku lagi**:

| Temuan scan | Status sekarang |
|---|---|
| H1 — `permission_classes = [IsAuthenticated]` tanpa penjaga | **Sebagian teratasi.** Sekarang `[IsAuthenticated, CanAksesWorkOrder]` (`work_order/views.py:20`). Lihat §5 — masih ada lubang. |
| H8 — `create()` tanpa `transaction.atomic` | **Teratasi.** `@transaction.atomic` ada di `work_order/serializers.py:58`. |
| H2 — `profil_staff_id` | **MASIH HIDUP**, malah menyebar dari 2 jadi 3 titik. Lihat §3. |
| H7 — penomoran leksikografis tanpa lock | **MASIH HIDUP** (`work_order/models.py:61-70`). |
| M20 — `WorkOrderPenugasan.staff` `CASCADE` | **MASIH HIDUP** (`work_order/models.py:110`), dan menular ke `WorkOrderPesan.pengirim` (`:128`). |
| "9 endpoint, semua dead" | **SALAH.** Sekarang **10** endpoint, dan statusnya berbeda-beda per endpoint. |

> **Dampak ke tugas graph sebelumnya:** angka final FASE 0 di
> `docs/_scan/graph/00-reconcile.md` (**152**) kini **153**, karena
> `POST /api/v1/work-order/{id}/kirim_pesan/` belum ada saat itu.
> `validate_graph.py` pemeriksaan #4 akan GAGAL kalau dijalankan ulang
> terhadap kode hari ini. Itu bukan cacat validator — itu memang gunanya.

---

## 1. Penyebab akar: migrasi yang tidak akan pernah jalan

Ini penjelasan sesungguhnya di balik nama branch `fix/migrasi-tertunda`.

```
migrasi di disk    : ['0001_initial']
migrasi ter-apply  : ['0001_initial']          <- Django: "sudah selesai"
tabel wo_* di DB   : ['wo_penugasan', 'wo_work_order']
```

`e05535e` **menyisipkan dua `migrations.CreateModel` baru ke dalam
`0001_initial.py` yang sudah ter-`apply`**:

```
+        migrations.CreateModel(name='DetailPesananProduksi', ...
+                'db_table': 'wo_detail_produksi',
+        migrations.CreateModel(name='WorkOrderPesan', ...
+                'db_table': 'wo_pesan',
```

Django mencatat `0001_initial` di `django_migrations` sebagai selesai, jadi
**tidak akan menjalankannya lagi**. Kedua tabel tidak pernah dibuat.

Yang membuat ini berbahaya: **seluruh pemeriksaan standar Django lulus.**

| Perintah | Keluaran | Kenyataan |
|---|---|---|
| `makemigrations --check --dry-run` | `No changes detected` (exit 0) | model **cocok** dengan berkas migrasi — yang salah adalah DB |
| `showmigrations work_order` | `[X] 0001_initial` | tabelnya tidak ada |

Tidak ada satu pun alat bawaan yang menangkap keadaan ini. Hanya query nyata
yang menampakkannya.

---

## 2. Tabel endpoint × dipakai-frontend × ada-data

**10 endpoint** dari resolver (`api/` saja, varian `.{format}` dan
`APIRootView` dibuang). Total seluruh proyek sekarang **153** pasangan
method+path unik.

| # | Method | Path | Action | Status sebenarnya | Penyebab (file:baris) | Dipakai FE | Ada data |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/work-order/` | `list` | **live-rapuh** — 200 `[]` sekarang; **500** begitu ada 1 baris | `views.py:17` prefetch `pesan_chat__pengirim` → `wo_pesan` tidak ada. Django melewati prefetch saat hasil kosong, itulah sebabnya sekarang lolos | ✅ `useWorkOrder.js:44` | 0 baris |
| 2 | POST | `/api/v1/work-order/` | `create` | **dead — 500 + baris yatim** | `serializers.py:36` field `pesan_chat` diserialisasi di respons → query `wo_pesan` → `ProgrammingError`. `@transaction.atomic` (`serializers.py:58`) sudah *commit* sebelum serialisasi | ✅ `useWorkOrder.js:72` | 0 baris |
| 3 | GET | `/api/v1/work-order/mading/` | `mading` | **live-kosong-palsu** — 200 `[]` (2 byte) | dua sebab menumpuk, lihat §4 | ✅ `useWorkOrder.js:32` | 0 baris |
| 4 | GET | `/api/v1/work-order/staff/` | `staff` | **live** — 200, 231 byte | `views.py:50` `Profil.objects.aktif()`; tidak menyentuh `WorkOrder` sama sekali | ✅ `useWorkOrder.js:57` | — (baca `staff_user`) |
| 5 | GET | `/api/v1/work-order/{id}/` | `retrieve` | **404 sekarang**; **500** kalau ada data | idem #1 | ❌ | 0 baris |
| 6 | PUT | `/api/v1/work-order/{id}/` | `update` | **404 sekarang**; **500** kalau ada data | idem #2 | ❌ | 0 baris |
| 7 | PATCH | `/api/v1/work-order/{id}/` | `partial_update` | **404 sekarang**; **500** kalau ada data | idem #2 | ❌ | 0 baris |
| 8 | DELETE | `/api/v1/work-order/{id}/` | `destroy` | **404 sekarang**; 204 kalau ada data | satu-satunya tulis yang tidak menyerialisasi respons. `CASCADE` menghapus penugasan + pesan (`models.py:109,127`) | ❌ | 0 baris |
| 9 | POST | `/api/v1/work-order/{id}/approve/` | `approve` | **dead — selalu 403** | `views.py:61` → `None` → `views.py:66` `penugasan.filter(staff_id=None).first()` → `None` → `views.py:67-68` `403` | ✅ `useWorkOrder.js:87` | 0 baris |
| 10 | POST | `/api/v1/work-order/{id}/kirim_pesan/` | `kirim_pesan` | **dead — 500** | `views.py:121` `WorkOrderPesan.objects.create()` → tabel `wo_pesan` tidak ada | ❌ | tabel tidak ada |

**Jumlah baris (SELECT COUNT saja):**

| Model | Tabel | Baris |
|---|---|---|
| `WorkOrder` | `wo_work_order` | **0** |
| `WorkOrderPenugasan` | `wo_penugasan` | **0** |
| `WorkOrderPesan` | `wo_pesan` | **TABEL TIDAK ADA** |
| `DetailPesananProduksi` | `wo_detail_produksi` | **TABEL TIDAK ADA** |

> **Konsekuensi besar untuk refactor: tidak ada satu baris data pun yang perlu
> diselamatkan.** Risiko migrasi data pada seluruh opsi Fase 3 mendekati nol.

---

## 3. Kalimat "profil_st…" yang terpotong — versi utuh

Temuan H2 dalam bentuk lengkap, dan **lebih luas** dari yang tertulis di scan:

> `getattr(request.user, 'profil_staff_id', None)` membaca atribut
> **`profil_staff_id` yang tidak ada pada model `Profil`**. Karena
> `AUTH_USER_MODEL = 'staff_user.Profil'`, `request.user` **adalah** sebuah
> `Profil` — dan `Profil` tidak punya field, property, maupun relasi bernama
> `profil_staff_id` (juga tidak `profil_staff`). `getattr` karena itu selalu
> jatuh ke nilai default **`None`**, tanpa galat, tanpa peringatan.

Terverifikasi: `getattr(Profil(), 'profil_staff_id', '<TIDAK ADA>')` →
`<TIDAK ADA>`.

**Sekarang ada di 3 titik backend** (bertambah dari 2 saat scan):

| Titik | Akibat |
|---|---|
| `work_order/views.py:32` (`mading`) | selalu masuk cabang "tanpa profil staf" → hanya `kategori='PRODUKSI'` yang tampil. Tugas yang di-*tag* ke diri sendiri **tidak pernah muncul** |
| `work_order/views.py:61` (`approve`) | `penugasan.filter(staff_id=None)` tidak pernah cocok → **selalu 403** |
| `work_order/permissions.py:13` (`CanAksesWorkOrder`) | cabang "saya di-tag" (`:20`) mati → yang bisa membaca WO non-PRODUKSI hanya pembuatnya |

**Dan kesalahan yang sama ada di frontend**, tiga lapis menumpuk:

1. `useWorkOrder.js:17` — `accessCard?.value?.profil_staff_id ?? null`.
2. Backend **tidak pernah mengirim** field itu. `PortalView`
   (`staff_user/views.py`) mengembalikan `{profil, modul, entitas}`; `grep -rn
   "profil_staff_id" --include="*.py"` hanya menemukan 3 pemakaian rusak di
   atas — **nol** di serializer mana pun.
3. `accessCard` sendiri **tidak pernah di-*export*** oleh `useAuth()`.
   `WorkOrderPanel.vue:98` menulis `const { accessCard: kartu } = useAuth()`,
   tapi string `accessCard` tidak muncul sama sekali di
   `src/composables/useAuth.js` → hasil destructuring `undefined`.

Jadi `bisaApprove()` (`useWorkOrder.js:20-21`) **selalu `false`**: tombol
setujui tidak pernah aktif di UI, dan seandainya aktif pun backend membalas
403.

**Nilai yang benar: `request.user.id`.** `WorkOrderPenugasan.staff` menunjuk
`'staff_user.Profil'` langsung (`work_order/models.py:110`), dan
`request.user` sudah `Profil`. Di frontend: `profil.id` dari `PortalView`.

---

## 4. Mengapa `/mading/` 200 `2 byte` dan `/staff/` 200 `231 byte`

Log runtime Anda **benar**, dan klaim scan "seluruh app dead" **juga tidak
sepenuhnya salah**. Keduanya menggambarkan hal berbeda:

- **`/staff/` (231 byte) — sungguh sehat.** `views.py:47-52` hanya membaca
  `Profil.objects.aktif()` lewat `ProfilStaffRingkasSerializer`. Tidak
  menyentuh `WorkOrder`, tidak menyentuh `profil_staff_id`, tidak menyentuh
  tabel yang hilang. Ini satu-satunya endpoint `work_order` yang benar-benar
  berfungsi hari ini.

- **`/mading/` (2 byte = `[]`) — 200 yang menyesatkan.** Dua kegagalan
  independen kebetulan saling menutupi:
  1. `profil_staff_id` selalu `None` (`views.py:32`) → masuk cabang
     `views.py:36`, hanya `kategori='PRODUKSI'`.
  2. `wo_work_order` punya **0 baris**, jadi hasilnya kosong apa pun
     filternya — dan **karena kosong, Django melewatkan seluruh query
     `prefetch_related`**, termasuk `pesan_chat__pengirim` yang akan menabrak
     tabel `wo_pesan` yang tidak ada.

  Begitu satu baris `WorkOrder` masuk, prefetch itu jalan dan endpoint ini
  berubah dari `200 []` menjadi **`500 ProgrammingError`**. Statusnya bukan
  "live", melainkan **live-rapuh**: hijau hanya selama tabelnya kosong.

---

## 5. Penjaga akses yang berlaku sekarang

`work_order/views.py:20` → `permission_classes = [IsAuthenticated, CanAksesWorkOrder]`

| Aspek | Keadaan |
|---|---|
| Atribut `modul` di viewset | **TIDAK ADA** → `AksesModul` tidak dipakai → endpoint ini **tidak dikunci `AKSES_MODUL` sama sekali** |
| `CanAksesWorkOrder` | hanya mengimplementasikan `has_object_permission` (`permissions.py:9`). **Tidak ada `has_permission`** |
| Akibat | `list`, `create`, `mading`, `staff` adalah endpoint **non-objek** → DRF tidak pernah memanggil `has_object_permission` → penjaganya **hanya `IsAuthenticated`** |
| Tulis pada objek | `permissions.py:24` → hanya `obj.dibuat_oleh == request.user`. Supervisor/Admin pun tidak bisa mengubah WO orang lain (kecuali `is_superuser`, `:10`) |
| Baca pada objek | `PRODUKSI` terbuka untuk semua (`:16-17`); cabang "saya di-tag" (`:20`) **mati** karena §3 |

Apakah string `'work_order'` terdaftar di `AKSES_MODUL`
(`staff_user/permissions.py:24-41`) sehingga muncul di `modul_terbuka()` —
**UNKNOWN**, belum diverifikasi. Yang pasti: nilai itu **tidak berpengaruh**
pada backend `work_order`, karena viewset-nya tidak memasang `AksesModul`.

Catatan frontend: rute `/work-order` (`router/index.js:195-199`) digerbangi
`meta.modul: 'work_order'` **tetapi merender `ModulBelumSiap.vue`**, bukan
panel aslinya. `WorkOrderPanel.vue` justru dirender di luar rute itu —
di `DashboardView.vue:45` dan `ModulLayout.vue:41`, yang **tidak** digerbangi
modul. Jadi papan tugas tampil untuk setiap pengguna yang login.

---

## 6. Cacat lain yang terverifikasi, di luar temuan scan

| # | Lokasi | Masalah |
|---|---|---|
| N1 | `work_order/views.py:101-107` | `approve()` **tidak punya `return` terakhir**. Kalau `aturan_penyelesaian` di luar 3 nilai yang ditangani, `wo_selesai_sekarang` tetap `False`, blok `:101` dilewati, fungsi mengembalikan `None` → DRF melempar *"The view didn't return an HttpResponse object"* → **500**. `choices` tidak ditegakkan DB (tidak ada `CheckConstraint`), jadi nilai liar bisa masuk lewat admin/SQL |
| N2 | `work_order/serializers.py:68` | `is_pic = (s_id == pic_id)`. Frontend **tidak pernah mengirim `pic_id`** (`useWorkOrder.js:72-74`) → `pic_id=None` → seluruh `is_pic=False` → WO beraturan `PIC` **tidak akan pernah bisa diselesaikan siapa pun** |
| N3 | `work_order/serializers.py:42-44` | `staff_ids = ListField(IntegerField)` tanpa validasi keberadaan → `staff_id` asing menabrak FK `IntegrityError`. Kini di dalam `atomic` (`:58`) sehingga tidak lagi meninggalkan WO yatim — tapi tetap 500, bukan 400 |
| N4 | `work_order/models.py:1-3` | Satu-satunya app transaksional yang **tidak** mewarisi `core.models.TimeStampedModel`/`DiauditModel` dan **tidak** punya FK ke `core.Entitas`. `dibuat_pada` ditulis manual (`:45`), `diubah_pada` tidak ada |
| N5 | `work_order/models.py:128` | `WorkOrderPesan.pengirim` `CASCADE` ke user — melanggar kebijakan `staff_user/models.py:22-25` (semua model transaksional `PROTECT`), sama seperti M20 |
| N6 | `work_order/services.py:11-25` | Dua fungsi hanya `pass`. Docstring `:19-24` menjanjikan cek stok lintas modul ke `warehouse` yang tidak ada implementasinya |

---

## 7. Yang BELUM terverifikasi (UNKNOWN)

| Hal | Kenapa penting |
|---|---|
| Apakah `ATOMIC_REQUESTS = True` di `settings.py` | Menentukan apakah baris `WorkOrder` pada endpoint #2 benar-benar tertinggal yatim setelah 500, atau ikut ter-*rollback*. Klaim "baris yatim" di §2 berlaku **hanya jika** `ATOMIC_REQUESTS` tidak aktif |
| Apakah `'work_order'` ada di `AKSES_MODUL` | Menentukan apakah rute frontend `/work-order` bisa dibuka — lihat §5 |
| Apakah `wo_pesan`/`wo_detail_produksi` pernah ada lalu di-*drop* | Tidak mengubah putusan (0 baris di mana-mana), hanya mengubah cerita bagaimana sampai ke sini |
