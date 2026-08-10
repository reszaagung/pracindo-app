# FASE 0 — INVENTARIS

Sumber kebenaran: kode. Semua klaim di bawah disertai rujukan `file:baris`.
Tanggal scan: 2026-08-05. Branch: `fix/migrasi-tertunda`.

---

## 1. Konfigurasi proyek (`pracindo_erp/settings.py`)

| Aspek | Nilai | Rujukan |
|---|---|---|
| Django | 5.2.10 (terpasang di venv) | `pracindo_erp/settings.py:1-6` |
| Python | 3.12.10 | — (verifikasi runtime) |
| `SECRET_KEY` | wajib dari `.env`, `RuntimeError` kalau kosong | `settings.py:34-40` |
| `DEBUG` | default `False` | `settings.py:43` |
| `ALLOWED_HOSTS` | dari env, fallback hardcode 6 host termasuk `testserver` | `settings.py:45-52` |
| `AUTH_USER_MODEL` | `staff_user.Profil` | `settings.py:100` |
| `ROOT_URLCONF` | `pracindo_erp.urls` | `settings.py:115` |
| `DEFAULT_AUTO_FIELD` | `BigAutoField` | `settings.py:147` |
| `TIME_ZONE` | `Asia/Jakarta`, `USE_TZ=True` | `settings.py:222,225` |
| `TOKEN_EXPIRE_HOURS` | dari env, default 12 | `settings.py:180` |
| Media upload max | 10 MB (data & file) | `settings.py:251-252` |
| Logging | console + RotatingFileHandler `logs/pracindo.log`, 5 MB × 5 | `settings.py:276-312` |

### INSTALLED_APPS

```
DJANGO_APPS       admin, auth, contenttypes, sessions, messages, staticfiles   settings.py:58-65
THIRD_PARTY_APPS  rest_framework, rest_framework.authtoken, corsheaders,
                  django_filters, drf_spectacular                              settings.py:67-73
LOCAL_APPS        core, staff_user            (lapis 1)
                  master, dokumen             (lapis 2)
                  inventory                   (lapis 3)
                  akunting, keuangan, pajak, warehouse, produksi,
                  sales_order, logistik, work_order  (lapis 4)                 settings.py:75-96
```

> **TEMUAN — app `audit/` TIDAK terdaftar di INSTALLED_APPS.**
> Direktori `audit/` berisi `models.py` (117 baris), `views.py`, `serializers.py`,
> `services.py`, `urls.py`, `admin.py`, dan `migrations/0001_initial.py` (44 baris),
> tetapi tidak muncul di `settings.py:75-96` dan `audit.urls` tidak di-include di
> `pracindo_erp/urls.py:7-27`. Konsekuensi terverifikasi: tabel `audit_jejak_aktivitas`
> tidak pernah dibuat oleh `migrate`, model tidak terdaftar di app registry, dan
> `audit.services.catat()` tidak dipanggil satu file pun (lihat FASE 4).
> Whitenoise juga dipakai di MIDDLEWARE/STORAGES tapi `whitenoise` tidak ada di
> THIRD_PARTY_APPS — ini normal, whitenoise memang tidak butuh entri app.

### MIDDLEWARE (urutan) — `settings.py:103-113`

1. `django.middleware.security.SecurityMiddleware`
2. `whitenoise.middleware.WhiteNoiseMiddleware`
3. `corsheaders.middleware.CorsMiddleware`
4. `django.contrib.sessions.middleware.SessionMiddleware`
5. `django.middleware.common.CommonMiddleware`
6. `django.middleware.csrf.CsrfViewMiddleware`
7. `django.contrib.auth.middleware.AuthenticationMiddleware`
8. `django.contrib.messages.middleware.MessageMiddleware`
9. `django.middleware.clickjacking.XFrameOptionsMiddleware`

Tidak ada middleware kustom buatan sendiri. Tidak ada middleware audit/logging request.

### REST_FRAMEWORK — `settings.py:150-172`

| Setting | Nilai |
|---|---|
| `DEFAULT_SCHEMA_CLASS` | `drf_spectacular.openapi.AutoSchema` |
| `DEFAULT_AUTHENTICATION_CLASSES` | `staff_user.authentication.ExpiringTokenAuthentication` (tunggal) |
| `DEFAULT_PERMISSION_CLASSES` | `rest_framework.permissions.IsAuthenticated` |
| `DEFAULT_FILTER_BACKENDS` | `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` |
| `DEFAULT_PAGINATION_CLASS` | `PageNumberPagination`, `PAGE_SIZE = 25` |
| `DATETIME_FORMAT` / `DATE_FORMAT` | `%Y-%m-%d %H:%M:%S` / `%Y-%m-%d` |
| `COERCE_DECIMAL_TO_STRING` | `True` |
| **Throttle** | **TIDAK ADA.** Grep `throttle` di seluruh `*.py` → 0 hasil. |

Autentikasi: token DRF dengan kedaluwarsa, `staff_user/authentication.py:24-50`.
Tidak ada SessionAuthentication di DRF (admin Django tetap pakai session lewat middleware).

### DATABASES — `settings.py:134-145`

Engine default `django.db.backends.postgresql`, semua kredensial dari `.env`
(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
`CONN_MAX_AGE` default 60, `connect_timeout` 10. Satu database, tanpa replica/router.

### CORS & CSRF — `settings.py:186-197`

`CORS_ALLOW_CREDENTIALS = True`; origin dari env dengan fallback domain produksi +
`localhost:5173`. `CORS_ALLOW_ALL_ORIGINS` tidak diset (aman).

### Keamanan produksi (`if not DEBUG`) — `settings.py:258-267`

`SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, cookie secure, HSTS 1 tahun +
preload, `nosniff`, `X_FRAME_OPTIONS='DENY'`.

### Task queue / background job

**TIDAK ADA.** Grep `celery|shared_task|@task|apply_async|delay(` di seluruh `*.py`
non-migration → 0 hasil. Semua pekerjaan sinkron di dalam request.

### Signal

**TIDAK ADA.** Grep `signals|receiver|post_save|pre_save|post_delete|m2m_changed|def ready`
di seluruh `*.py` non-migration → 0 hasil. Semua `apps.py` hanya berisi
`AppConfig` polos tanpa `ready()`.

---

## 2. URL root — `pracindo_erp/urls.py`

| Prefix | Include | Baris |
|---|---|---|
| `8243e09f…bfe/` | `admin.site.urls` (path admin diobfuskasi) | `:9` |
| `api/schema/` | `SpectacularAPIView` | `:12` |
| `api/docs/` | `SpectacularSwaggerView` | `:13` |
| `api/v1/auth/` | `staff_user.urls` | `:14` |
| `api/v1/master/` | `master.urls` | `:15` |
| `api/v1/dokumen/` | `dokumen.urls` — **urlpatterns kosong** (`dokumen/urls.py:5-6`) | `:16` |
| `api/v1/inventory/` | `inventory.urls` | `:17` |
| `api/v1/akunting/` | `akunting.urls` | `:18` |
| `api/v1/keuangan/` | `keuangan.urls` | `:19` |
| `api/v1/pajak/` | `pajak.urls` — **urlpatterns kosong** (`pajak/urls.py:5-6`) | `:20` |
| `api/v1/warehouse/` | `warehouse.urls` | `:21` |
| `api/v1/produksi/` | `produksi.urls` | `:22` |
| `api/v1/sales-order/` | `sales_order.urls` — **urlpatterns kosong** (`sales_order/urls.py:5-6`) | `:23` |
| `api/v1/logistik/` | `logistik.urls` — **urlpatterns kosong** (`logistik/urls.py:5-6`) | `:24` |
| `api/v1/work-order/` | `work_order.urls` | `:25` |
| `api/v1/core/` | `core.urls` | `:26` |

`audit.urls` tidak di-include di mana pun.
`api/schema/` dan `api/docs/` memakai permission default DRF (`IsAuthenticated`)
karena `SpectacularAPIView` tidak dioverride — tidak ada `AllowAny` eksplisit di
`pracindo_erp/urls.py:12-13`.

---

## 3. Inventaris file per app

Legenda: `—` = file tidak ada · `(kosong)` = 0 baris · `(stub)` = hanya komentar
scaffold Django · angka = jumlah baris.

### core — lapis 1 (fondasi)
| File | Baris | Isi |
|---|---|---|
| `models.py` | 270 | `TimeStampedModel`, `DiauditModel` (abstract); `GrupBahan`, `Entitas`, `CounterDokumen`, `PeriodeAkuntansi` |
| `serializers.py` | 54 | 5 serializer |
| `views.py` | 122 | 3 ViewSet |
| `urls.py` | 16 | router: `entitas`, `grup-bahan`, `periode` |
| `services.py` | 81 | `pastikan_periode_terbuka`, `tutup_periode`, `buka_periode` |
| `permissions.py` | (kosong) | — |
| `constants.py` | 10 | presisi decimal QTY/HARGA/NILAI |
| `exceptions.py` | 9 | `PeriodeTertutup`, `NomorDokumenGagal` |
| `admin.py` | 42 | 4 ModelAdmin |
| `tests.py` | 3 (stub) | — |
| `migrations/` | 0001, 0002, 0003_seed_entitas | data migration seed |
| signals/tasks/utils/managers | — | tidak ada |

### staff_user — lapis 1
| File | Baris | Isi |
|---|---|---|
| `models.py` | 347 | `Jabatan`, `Profil` (AUTH_USER_MODEL), `DataKepegawaian`, `RiwayatAkses`; enum `Role`, `StatusKerja`, `Departemen`, `JenisKelamin`, `StatusPajak`; manager `ProfilManager` |
| `serializers.py` | 144 | 12 serializer |
| `views.py` | 283 | 5 APIView + 4 ViewSet |
| `urls.py` | 26 | 6 path + router 4 viewset |
| `services.py` | 228 | 10 fungsi (daftar, aktifkan, tolak, ubah_role, nonaktifkan, aktifkan_kembali, ganti_password, reset_password, catat_akses, terbitkan_token) |
| `permissions.py` | 185 | `AKSES_MODUL`, `META_MODUL`, 9 permission class |
| `authentication.py` | 50 | `ExpiringTokenAuthentication` |
| `admin.py` | 66 | ModelAdmin |
| `tests.py` | 3 (stub) | — |
| `migrations/` | 0001, 0002, 0003 | — |

### master — lapis 2
| File | Baris | Isi |
|---|---|---|
| `models.py` | 170 | `Kategori`, `Satuan`, `Suplier`, `Produk`, `Pelanggan`; enum `JenisProduk` |
| `serializers.py` | 67 | 7 serializer (`KategoriSerializer` tidak dipakai view mana pun) |
| `views.py` | 71 | `BasisMaster` + 4 ViewSet (`Satuan`, `Produk`, `Suplier`, `Pelanggan`) |
| `urls.py` | 16 | router hanya `produk` + `suplier` → **`SatuanViewSet` & `PelangganViewSet` tidak terjangkau** |
| `utils.py` | 24 | `generate_kode_urut()` |
| `services.py` | (kosong) | — |
| `permissions.py` | (kosong) | — |
| `admin.py` | 56 | — |
| `migrations/` | 0001, 0002, **0003 (untracked)** | — |

### dokumen — lapis 2
| File | Baris | Isi |
|---|---|---|
| `models.py` | 85 | `Lampiran` (GenericFK, append-only); enum `JenisLampiran` |
| `serializers.py` | (kosong) | — |
| `views.py` | 3 (stub) | `from django.shortcuts import render` |
| `urls.py` | 7 | `urlpatterns = []` |
| `services.py` / `permissions.py` | (kosong) | — |
| `admin.py` | 19 | terdaftar di admin |
| `migrations/` | 0001 | — |
| **Status** | model hidup & bermigrasi, **tanpa satu pun endpoint API** |

### inventory — lapis 3
| File | Baris | Isi |
|---|---|---|
| `models.py` | 378 | `Tangki`, `Stok`, `MutasiStok`, `SaldoEntitas`, `NilaiEkuivalen`, `MutasiKlaim`, `PosisiKlaim`; enum `Lapis`, `JenisMutasiStok`, `JenisKlaim` |
| `serializers.py` | 232 | — |
| `views.py` | 252 | 5 ViewSet read-only + 5 APIView write |
| `urls.py` | 27 | 5 path + router 5 viewset |
| `services.py` | 577 | mesin stok & klaim (lihat FASE 3) |
| `permissions.py` | (kosong) | — |
| `admin.py` | 100 | — |
| `migrations/` | 0001 | — |

### akunting — lapis 4
| File | Baris | Isi |
|---|---|---|
| `models/__init__.py` | 31 | re-export |
| `models/akun.py` | 130 | `Akun`, enum |
| `models/jurnal.py` | 159 | `JurnalUmum`, `JurnalDetail`; enum `JenisKejadian` |
| `models/pembelian.py` | 227 | `PurchaseOrder`, `PurchaseOrderItem`; enum `StatusPO` |
| `models/hutang.py` | 277 | `FakturPembelian`, `KartuHutang`, `UangMukaSuplier`; enum `JenisFaktur`, `StatusFaktur`, `JenisMutasiHutang` |
| `serializers.py` | 222 | — |
| `views.py` | 365 | 6 ViewSet |
| `urls.py` | 19 | router 6 viewset |
| `services.py` | 674 | posting jurnal, PO, faktur, bayar |
| `posting_rules.py` | 91 | peta akun per kejadian |
| `permissions.py` | — | **file tidak ada** |
| `admin.py` | 148 | — |
| `migrations/` | 0001, 0002, 0003, **0004_trigger_jurnal_seimbang** (trigger DB), 0005_seed_coa | — |

### keuangan — lapis 4
| File | Baris | Isi |
|---|---|---|
| `models.py` | 200 | `RekeningBank`, `MutasiKas`, `RencanaBayar`, `PengeluaranKas`; enum `JenisRekening`, `StatusRencana` |
| `serializers.py` | 16 | 1 serializer |
| `views.py` | 49 | 1 ViewSet |
| `urls.py` | 11 | router `pengeluaran` |
| `services.py` | 62 | — |
| `permissions.py` | (kosong) | — |
| `admin.py` | 39 | — |
| `migrations/` | 0001, **0002_pengeluarankas (untracked)** | — |

### warehouse — lapis 4
| File | Baris | Isi |
|---|---|---|
| `models.py` | 377 | `PenerimaanBarang`, `PenerimaanItem`, `LaporanSelisih`, `Packaging`; enum `JenisKemasan`, `JenisSelisih`, `StatusSelisih`, `Resolusi` |
| `serializers.py` | 215 | — |
| `views.py` | 263 | 4 ViewSet |
| `urls.py` | 19 | router 4 viewset |
| `services.py` | 499 | penerimaan barang, selisih, packaging |
| `permissions.py` | (kosong) | — |
| `admin.py` | 68 | — |
| `migrations/` | 0001, 0002, 0003 | — |

### produksi — lapis 4
| File | Baris | Isi |
|---|---|---|
| `models.py` | 242 | `Resep`, `ResepItem`, `SesiProduksi`, `SesiInput`; enum `StatusSesi` |
| `serializers.py` | 56 | — |
| `views.py` | 97 | 1 ViewSet |
| `urls.py` | 11 | router `sesi` |
| `services.py` | 255 | — |
| `permissions.py` | (kosong) | — |
| `admin.py` | 40 | — |
| `migrations/` | 0001 | — |

### work_order — lapis 4
| File | Baris | Isi |
|---|---|---|
| `models.py` | 59 | `WorkOrder`, `WorkOrderPenugasan` |
| `serializers.py` | 43 | — |
| `views.py` | 63 | 1 ViewSet |
| `urls.py` | 11 | router `''` (root prefix) |
| `services.py` | (kosong) | — |
| `permissions.py` | (kosong) | — |
| `admin.py` | 3 (stub) | — |
| `migrations/` | **0001 (untracked)** | — |

### pajak / sales_order / logistik — lapis 4, STUB KOSONG
Ketiganya identik polanya:
`models.py` = 3 baris scaffold, `views.py` = 3 baris scaffold,
`urls.py` = `urlpatterns = []`, `serializers.py`/`services.py`/`permissions.py` = 0 baris,
`admin.py` = scaffold, `migrations/` hanya berisi `__init__.py`.
Terdaftar di INSTALLED_APPS (`settings.py:90,93,94`) dan di-include di root urls
(`pracindo_erp/urls.py:20,23,24`) tapi tidak menyumbang endpoint maupun tabel.

### audit — TIDAK TERPASANG
| File | Baris | Isi |
|---|---|---|
| `models.py` | 117 | `JejakAktivitas` (append-only, GenericFK); enum `JenisAksi` |
| `serializers.py` | 22 | — |
| `views.py` | 53 | `JejakAktivitasViewSet` |
| `urls.py` | 11 | router `jejak` — **tidak di-include root** |
| `services.py` | 83 | `catat()`, `catat_perubahan_status()`, `riwayat_objek()` |
| `permissions.py` | 1 | hanya docstring |
| `admin.py` | 22 | — |
| `migrations/` | 0001 | tidak akan pernah jalan |
| **Status** | **kode mati** — app tidak di INSTALLED_APPS, url tidak di-include, `catat()` tidak dipanggil siapa pun |

---

## 4. Ringkasan file per kategori

| Kategori | Ada isi | Kosong / stub | Tidak ada |
|---|---|---|---|
| `models.py` | core, staff_user, master, dokumen, inventory, akunting(pkg), keuangan, warehouse, produksi, work_order, audit | pajak, sales_order, logistik | — |
| `serializers.py` | core, staff_user, master, inventory, akunting, keuangan, warehouse, produksi, work_order, audit | dokumen, pajak, sales_order, logistik | — |
| `views.py` | core, staff_user, master, inventory, akunting, keuangan, warehouse, produksi, work_order, audit | dokumen, pajak, sales_order, logistik | — |
| `urls.py` | core, staff_user, master, inventory, akunting, keuangan, warehouse, produksi, work_order, audit | dokumen, pajak, sales_order, logistik | — |
| `services.py` | core, staff_user, inventory, akunting, keuangan, warehouse, produksi, audit | master, dokumen, pajak, sales_order, logistik, work_order | — |
| `permissions.py` | staff_user (185 br), audit (docstring) | core, master, dokumen, inventory, keuangan, warehouse, produksi, work_order, pajak, sales_order, logistik | **akunting** |
| `signals.py` | — | — | **semua app** |
| `tasks.py` | — | — | **semua app** |
| `utils.py` | master | — | app lain |
| `managers.py` | — (manager didefinisikan inline di `staff_user/models.py:91`) | — | semua app |
| `admin.py` | core, staff_user, master, dokumen, inventory, akunting, keuangan, warehouse, produksi, audit | work_order, pajak, sales_order, logistik | — |
| `tests.py` | — | **semua app stub/kosong — 0 test di seluruh repo** | — |

---

## 5. Catatan status git (konteks, bukan analisis kode)

Migrasi yang belum di-commit (untracked) saat scan:
`keuangan/migrations/0002_pengeluarankas.py`,
`master/migrations/0003_alter_kategori_kode_alter_pelanggan_kode_and_more.py`,
`work_order/migrations/0001_initial.py`, dan `master/utils.py`.
Nama branch `fix/migrasi-tertunda` konsisten dengan itu.

---

## 6. Cross-check drf-spectacular

`drf_spectacular` terpasang (`settings.py:72`). Perintah dijalankan:

```
python manage.py spectacular --file docs/_scan/openapi.yaml
```

Hasil: **exit 0**, file `docs/_scan/openapi.yaml` (187 KB) dibuat.
Ringkasan generator: **32 warning (14 unik), 48 error (11 unik)**.

Error yang dilaporkan generator (semua bertipe "unable to guess serializer",
artinya endpoint tersebut **hilang dari dokumentasi OpenAPI**):

| View | Baris | Akibat |
|---|---|---|
| `akunting.views.PembayaranView` | `akunting/views.py:328` | tidak terdokumentasi |
| `staff_user.views.DaftarView` | `staff_user/views.py:32` | tidak terdokumentasi |
| `staff_user.views.LoginView` | `staff_user/views.py:60` | tidak terdokumentasi |
| `staff_user.views.LogoutView` | `staff_user/views.py:104` | tidak terdokumentasi |
| `staff_user.views.PortalView` | `staff_user/views.py:113` | tidak terdokumentasi |
| `staff_user.views.GantiPasswordView` | `staff_user/views.py:134` | tidak terdokumentasi |
| `inventory.views.IsiPoolView` | `inventory/views.py:141` | tidak terdokumentasi |
| `inventory.views.SetorKePoolView` | `inventory/views.py:160` | tidak terdokumentasi |
| `inventory.views.KlaimHasilView` | `inventory/views.py:182` | tidak terdokumentasi |
| `inventory.views.OpnameView` | `inventory/views.py:208` | tidak terdokumentasi |
| `inventory.views.VerifikasiView` | `inventory/views.py:234` | tidak terdokumentasi |

Warning penting: 4 ViewSet gagal menurunkan model karena `get_queryset()`
menyentuh `request.user` yang saat generasi schema adalah `AnonymousUser` —
`FakturPembelianViewSet` (`akunting/views.py:226`), `JurnalUmumViewSet`
(`akunting/views.py:69`), `PurchaseOrderViewSet` (`akunting/views.py:112`),
`DataKepegawaianViewSet` (`staff_user/views.py:266`).
Perbandingan lengkap manual-vs-generator ada di `01-api-map.md` bagian CROSS-CHECK.
