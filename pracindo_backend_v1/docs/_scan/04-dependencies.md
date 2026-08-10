# FASE 4 — KETERHUBUNGAN ANTAR FILE

Diekstrak dengan parser AST atas seluruh `*.py` non-migration (110 berkas),
mencatat `Import`/`ImportFrom` beserta nomor baris dan apakah pernyataan itu
berada di tingkat modul atau di dalam badan fungsi.

Catatan teknis: 10 berkas punya BOM UTF-8 di awal (`core/constants.py`,
`core/exceptions.py`, `core/urls.py`, `dokumen/urls.py`, `keuangan/urls.py`,
`logistik/urls.py`, `pajak/urls.py`, `produksi/urls.py`, `sales_order/urls.py`,
`work_order/urls.py`). Python menanganinya, tapi alat yang membaca dengan
`encoding='utf-8'` polos akan gagal parse — analisis di bawah memakai `utf-8-sig`.

---

## 1. Aturan lapis yang dideklarasikan

`pracindo_erp/settings.py:75-96` menyatakan:

```
Lapis 1  core, staff_user          "fondasi, tidak mengimpor app lokal lain"
Lapis 2  master, dokumen           master data & infrastruktur generik
Lapis 3  inventory
Lapis 4  akunting, keuangan, pajak, warehouse, produksi,
         sales_order, logistik, work_order
         "kelompok sejajar, boleh saling panggil DI DALAM FUNGSI"
```

---

## 2. Graf import antar app (tingkat modul)

```
                     ┌──────────────────────────────┐
                     │            core              │  lapis 1 — tidak
                     │  (tidak mengimpor app lokal) │  mengimpor siapa pun
                     └──────────────▲───────────────┘
        ┌───────────────┬───────────┼───────────┬──────────────┬─────────────┐
        │               │           │           │              │             │
   staff_user        master      dokumen    inventory      keuangan      produksi
   (lapis 1)        (lapis 2)   (lapis 2)   (lapis 3)      (lapis 4)     (lapis 4)
        ▲                                       ▲                            │
        │                                       └────────────────────────────┘
        │                                            produksi → inventory
        │                                            (MODULE, ke lapis bawah ✅)
        │
        ├── akunting/views.py:17,18
        ├── inventory/views.py:23,24
        ├── warehouse/views.py:30
        ├── master/views.py:6
        ├── produksi/views.py:7
        ├── core/views.py:14          ⟵ lapis 1 mengimpor lapis 1
        ├── audit/views.py:17
        └── work_order/views.py:9, serializers.py:3

   akunting ◀──────────── warehouse       (MODULE: warehouse/views.py:19,
            ──────────▶                    warehouse/serializers.py:19)
            (FUNC dua arah di services)

   akunting ◀──────────── keuangan        (MODULE: keuangan/services.py:7)
```

### Tabel lengkap import lintas app

| Dari | Ke | Baris | Tingkat | Lapis | Sesuai aturan? |
|---|---|---|---|---|---|
| `akunting/models/akun.py` | `core.constants`, `core.models` | 15,16 | MODULE | 4→1 | ✅ |
| `akunting/models/hutang.py` | `core.constants`, `core.models` | 26,27 | MODULE | 4→1 | ✅ |
| `akunting/models/jurnal.py` | `core.constants`, `core.models` | 21,22 | MODULE | 4→1 | ✅ |
| `akunting/models/pembelian.py` | `core.constants`, `core.models` | 21,26 | MODULE | 4→1 | ✅ |
| `akunting/services.py` | `core.models`, `core.services` | 23,24 | MODULE | 4→1 | ✅ |
| `akunting/services.py` | `core.models` | 57 | **FUNC** | 4→1 | ⚠ redundan — sudah diimpor `:23` |
| `akunting/services.py` | `master.models` | 295 | **FUNC** | 4→2 | ⚠ tidak perlu FUNC |
| `akunting/services.py` | `dokumen.models` | 418 | **FUNC** | 4→2 | ⚠ tidak perlu FUNC |
| `akunting/services.py` | `warehouse.models` | 498, 546 | **FUNC** | 4→4 | ✅ sesuai aturan (pemutus siklus) |
| `akunting/services.py` | `warehouse.services` | 499, 547 | **FUNC** | 4→4 | ✅ sesuai aturan |
| `akunting/views.py` | `staff_user.models`, `staff_user.permissions` | 17,18 | MODULE | 4→1 | ✅ |
| `akunting/views.py` | `core.models` | 164 | **FUNC** | 4→1 | ⚠ tidak perlu FUNC |
| `core/views.py` | `staff_user.permissions` | 14 | MODULE | 1→1 | ⚠ lihat §3 |
| `dokumen/models.py` | `core.models` | 17 | MODULE | 2→1 | ✅ |
| `inventory/models.py` | `core.constants`, `core.models` | 32,33 | MODULE | 3→1 | ✅ |
| `inventory/services.py` | `core.services` | 35 | MODULE | 3→1 | ✅ |
| `inventory/views.py` | `staff_user.models`, `staff_user.permissions` | 23,24 | MODULE | 3→1 | ✅ |
| `keuangan/models.py` | `core.constants`, `core.models` | 22,23 | MODULE | 4→1 | ✅ |
| `keuangan/views.py` | `core.models` | 5 | MODULE | 4→1 | ✅ |
| **`keuangan/services.py`** | **`akunting.services`** | **7** | **MODULE** | **4→4** | ❌ **melanggar** |
| `keuangan/services.py` | `core.models` | 5 | MODULE | 4→1 | ✅ |
| `master/models.py` | `core.models` | 13 | MODULE | 2→1 | ✅ |
| `master/views.py` | `staff_user.permissions` | 6 | MODULE | 2→1 | ✅ |
| `produksi/models.py` | `core.constants`, `core.models` | 26,27 | MODULE | 4→1 | ✅ |
| `produksi/services.py` | `inventory.models` | 24 | MODULE | 4→3 | ⚠ akses model langsung |
| `produksi/services.py` | `inventory.services` | 25 | MODULE | 4→3 | ✅ |
| `produksi/views.py` | `staff_user.permissions` | 7 | MODULE | 4→1 | ✅ |
| `staff_user/models.py` | `core.models` | 34 | MODULE | 1→1 | ⚠ lihat §3 |
| `staff_user/models.py` | `core.models` | 220 | **FUNC** | 1→1 | ⚠ redundan |
| `warehouse/models.py` | `core.constants`, `core.models` | 27,28 | MODULE | 4→1 | ✅ |
| `warehouse/services.py` | `core.services` | 31 | MODULE | 4→1 | ✅ |
| **`warehouse/serializers.py`** | **`akunting.models`** | **19** | **MODULE** | **4→4** | ❌ **melanggar** |
| **`warehouse/views.py`** | **`akunting.models`** | **19** | **MODULE** | **4→4** | ❌ **melanggar** |
| `warehouse/views.py` | `staff_user.permissions` | 30 | MODULE | 4→1 | ✅ |
| `warehouse/services.py` | `akunting.models` | 83, 137, 395 | **FUNC** | 4→4 | ✅ sesuai aturan |
| `warehouse/services.py` | `akunting.services` | 213 | **FUNC** | 4→4 | ✅ sesuai aturan |
| `warehouse/services.py` | `inventory.services` | 188 | **FUNC** | 4→3 | ⚠ tidak perlu FUNC |
| `work_order/views.py` | `staff_user.models` | 9 | MODULE | 4→1 | ✅ |
| `work_order/serializers.py` | `staff_user.models` | 3 | MODULE | 4→1 | ✅ |
| `audit/views.py` | `staff_user.permissions` | 17 | MODULE | —→1 | app tidak terpasang |

---

## 3. Pelanggaran aturan import satu arah

### ❌ V1 — `keuangan/services.py:7` mengimpor `akunting.services` di tingkat modul

```python
from akunting.services import posting  # Memanggil modul akunting sesuai aturan
```

Komentar di baris itu mengklaim "sesuai aturan", tapi `keuangan/models.py:7-9`
menyatakan sebaliknya secara eksplisit:

> *"Ketergantungan satu arah: keuangan memanggil akunting, tidak pernah
> sebaliknya. **Impor ke akunting dilakukan DI DALAM FUNGSI di services.py,
> bukan di kepala file.**"*

Dampak nyata: `akunting` belum mengimpor `keuangan` sama sekali, jadi **belum**
ada siklus. Tapi begitu ada satu impor balik (mis. `akunting` perlu membaca
`RekeningBank`), siklus langsung terbentuk dan Django gagal start.

### ❌ V2 — `warehouse/views.py:19` & `warehouse/serializers.py:19` mengimpor `akunting.models` di tingkat modul

```python
from akunting.models import PurchaseOrder, PurchaseOrderItem
```

Melanggar "boleh saling panggil **di dalam fungsi**" untuk lapis 4.
`warehouse` bukan hanya membaca — lihat §4.

Yang menyelamatkan sistem dari `ImportError` saat start-up adalah bahwa
`akunting/models/*` **tidak** mengimpor `warehouse` sama sekali di tingkat
modul; relasinya memakai referensi string malas
(`akunting/models/hutang.py:78` → `'warehouse.PenerimaanBarang'`).

### ⚠ V3 — `staff_user` (lapis 1) mengimpor `core` (lapis 1)

`staff_user/models.py:34` `from core.models import TimeStampedModel`.
Komentar `settings.py:76` bilang lapis 1 "tidak mengimpor app lokal lain".
Arahnya satu arah (`core` tidak pernah mengimpor `staff_user`; ia memakai
`settings.AUTH_USER_MODEL`), jadi tidak berbahaya — tapi deskripsi lapisnya
tidak akurat. Yang sama berlaku untuk `core/views.py:14` yang mengimpor
`staff_user.permissions`.

### ⚠ V4 — `produksi/services.py:24` mengimpor `inventory.models` langsung

`hitung_kapasitas()` (`produksi/services.py:58-64`) melakukan query
`Stok.objects.filter(...)` sendiri, bukan lewat fungsi di `inventory.services`.
Arahnya turun (4→3), jadi tidak menimbulkan siklus, tapi mem-bypass lapis service.

---

## 4. Panggilan lintas app: lewat `services.py` atau tembak model langsung?

| Pemanggil | Sasaran | Jalur | Sifat |
|---|---|---|---|
| `warehouse.terima_barang()` `warehouse/services.py:192` | `inventory.services.terima_raw()` | ✅ **service** | tulis |
| `warehouse._posting_penerimaan()` `:215` | `akunting.services.posting()` | ✅ **service** | tulis |
| `akunting.draft_faktur()` `:507` | `warehouse.services.total_potongan()` | ✅ **service** | baca |
| `akunting.terbitkan_faktur()` `:590` | `warehouse.services.total_potongan()` | ✅ **service** | baca |
| `keuangan.catat_pengeluaran()` `keuangan/services.py:52` | `akunting.services.posting()` | ✅ **service** | tulis |
| `produksi.mulai_sesi()` `produksi/services.py:150` | `inventory.services.pakai_dari_pool()` | ✅ **service** | tulis |
| `produksi.selesaikan_sesi()` `:191` | `inventory.services.hasil_ke_pool()` | ✅ **service** | tulis |
| `warehouse.terima_barang()` `warehouse/services.py:88` | `akunting.models.PurchaseOrder` | ❌ **model langsung** | **BACA + LOCK** |
| `warehouse.terima_barang()` `:124-125` | `akunting.models.PurchaseOrder.status` | ❌ **model langsung** | **TULIS** — mengubah status PO milik app lain |
| `warehouse._simpan_item()` `:139,174-175` | `akunting.models.PurchaseOrderItem.qty_diterima` | ❌ **model langsung** | **TULIS** — memutakhirkan cache milik app lain |
| `warehouse._buka_kembali_po()` `:397-400` | `akunting.models.PurchaseOrder.status` | ❌ **model langsung** | **TULIS** |
| `warehouse.POSiapTerimaViewSet` `warehouse/views.py:57` | `akunting.models.PurchaseOrder.objects.terbuka()` | ❌ **model langsung** | baca (queryset custom manager app lain) |
| `warehouse/serializers.py:36-51` | `akunting.models.PurchaseOrder`, `PurchaseOrderItem` | ❌ **model langsung** | serialisasi model app lain |
| `akunting.draft_faktur()` `:501` | `warehouse.models.PenerimaanBarang` | ❌ **model langsung** | baca |
| `akunting.terbitkan_faktur()` `:551` | `warehouse.models.PenerimaanBarang` | ❌ **model langsung** | **BACA + LOCK** |
| `akunting.hitung_nilai_penerimaan()` `:485` | `penerimaan.item` (`warehouse.PenerimaanItem`) | ❌ **model langsung** | baca |
| `akunting.lampirkan_dokumen()` `:426` | `dokumen.models.Lampiran` | ❌ **model langsung** | tulis (fungsi mati, §6) |
| `akunting.buat_po()` `:302` | `master.models.Suplier` | ❌ **model langsung** | baca (master data, wajar) |
| `produksi.hitung_kapasitas()` `:60` | `inventory.models.Stok` | ❌ **model langsung** | baca |
| `work_order.staff()` `work_order/views.py:40` | `staff_user.models.Profil.objects.aktif()` | ❌ **model langsung** | baca |

**Ringkasan:** 7 panggilan lewat lapis service (semuanya jalur tulis penting),
**13 akses model langsung lintas app** — 4 di antaranya **menulis** ke tabel app
lain. Yang paling berat: `warehouse` memiliki wewenang penuh atas
`akunting_purchase_order` dan `akunting_purchase_order_item`; tidak ada fungsi
`akunting.services.catat_realisasi_penerimaan()` yang menjadi satu-satunya pintu.

---

## 5. Signal

**TIDAK ADA SATU PUN.**

Diverifikasi: `grep -rn "signals|receiver|post_save|pre_save|post_delete|pre_delete|m2m_changed|def ready"`
atas seluruh `*.py` non-migration → **0 hasil**. Tidak ada berkas `signals.py`
di app mana pun, dan ke-14 `apps.py` hanya berisi `AppConfig` polos tanpa
`ready()`.

Konsekuensi arsitektural: setiap efek samping harus dipanggil eksplisit dari
`services.py`. Itu membuat alur bisa dibaca lurus, tapi juga berarti **tidak ada
jaring pengaman** — kalau satu jalur lupa memanggil `posting()` atau
`terima_raw()`, tidak ada apa pun yang menangkapnya.

Contoh nyata dari akibat itu: `PengeluaranKas` bisa di-`PUT`/`DELETE` lewat
ModelViewSet default (`keuangan/views.py:10`) dan tidak ada signal yang akan
menyesuaikan `MutasiKas` maupun jurnal (lihat FASE 1 §B).

---

## 6. Import melingkar & workaround

### 6a. Siklus tingkat modul: **TIDAK ADA**

Django berhasil `setup()` tanpa `ImportError` (diverifikasi — `manage.py
spectacular` dan `makemigrations --check` keduanya exit 0). Yang mencegahnya:

1. Relasi lintas app memakai **referensi string malas** di semua FK
   (`'warehouse.PenerimaanBarang'`, `'akunting.PurchaseOrder'`,
   `'core.Entitas'`, `'master.Produk'`, `'staff_user.Profil'`, `'inventory.Tangki'`,
   `'dokumen.Lampiran'`, `'akunting.Akun'`, `'keuangan.MutasiKas'`) — tidak ada
   satu pun `from <app>.models import X` di berkas `models.py` app lain, kecuali
   pewarisan dari `core.models`.
2. Impor lintas app di `services.py` ditaruh di dalam fungsi (lihat 6b).

### 6b. Import di dalam fungsi — pemutus siklus SESUNGGUHNYA

| Lokasi | Impor | Alasan |
|---|---|---|
| `akunting/services.py:498` | `from warehouse.models import PenerimaanBarang` | **wajib** — `warehouse/views.py:19` & `serializers.py:19` sudah mengimpor `akunting.models` di tingkat modul |
| `akunting/services.py:499` | `from warehouse.services import total_potongan` | **wajib** — `warehouse/services.py:213` mengimpor `akunting.services` |
| `akunting/services.py:546,547` | idem | **wajib** |
| `warehouse/services.py:83,137,395` | `from akunting.models import …` | **wajib** — sisi lain dari siklus yang sama |
| `warehouse/services.py:213` | `from akunting.services import posting` | **wajib** |
| `staff_user/models.py:205` | `from .permissions import modul_untuk_role` | **wajib** — `staff_user/permissions.py:22` mengimpor `from .models import Role` → siklus **intra-app** models ↔ permissions |
| `staff_user/models.py:209` | `from .permissions import role_boleh_modul` | **wajib** — idem |

### 6c. Import di dalam fungsi yang **TIDAK** memutus siklus apa pun

Ini murni kebiasaan, bukan kebutuhan — dan menyamarkan mana yang benar-benar
pemutus siklus:

| Lokasi | Impor | Catatan |
|---|---|---|
| `akunting/services.py:57` | `from core.models import Entitas` | `core.models` sudah diimpor di `:23` |
| `akunting/services.py:295` | `from master.models import Suplier` | lapis 2, aman di tingkat modul |
| `akunting/services.py:297,340,365,386,420,438,549,653` | `from .models import …` | intra-app; `.models` sudah diimpor di `:26-29` |
| `akunting/services.py:418` | `from dokumen.models import Lampiran` | lapis 2, aman |
| `akunting/services.py:417` | `from django.contrib.contenttypes.models import ContentType` | Django, aman |
| `akunting/services.py:648-651` | `from datetime import timedelta`, `from django.db.models import Q as Qf, Sum` | stdlib/Django, aman |
| `akunting/views.py:164-165` | `from core.models import Entitas`, `from django.utils import timezone` | aman |
| `akunting/views.py:303,310` | `from django.utils import timezone` | aman |
| `akunting/views.py:345` | `import uuid` | aman |
| `staff_user/models.py:220` | `from core.models import Entitas` | `core.models` sudah diimpor `:34` |
| `warehouse/services.py:188` | `from inventory.services import terima_raw` | lapis 3, aman di tingkat modul |
| `warehouse/services.py:449` | `from django.db.models import Sum` | aman |
| `inventory/services.py:564` | `from django.db import connection` | aman |
| `produksi/services.py` — tidak ada | — | konsisten memakai impor tingkat modul |

---

## 7. Graf migrasi (dependensi antar app di level skema)

Siklus app-level **akunting ↔ warehouse** nyata di level model dan diselesaikan
dengan pola pemecahan migrasi Django yang benar:

```
core/0001_initial            (deps: —)
    ↓
staff_user/0001_initial      (deps: auth/0012, core/0001)
    ↓
core/0002_initial            (deps: core/0001, +AUTH_USER)   ← dipecah karena
    ↓                                                          DiauditModel → user
core/0003_seed_entitas
    ↓
akunting/0001_initial        (deps: —, +AUTH_USER)
    ↓
akunting/0002_initial        (deps: akunting/0001, core/0002, dokumen/0001)
    ↓
warehouse/0001_initial       (deps: akunting/0002, core/0002, dokumen/0001, master/0001)
    ↓
akunting/0003_initial        (deps: akunting/0002, core/0002, master/0001, WAREHOUSE/0001)
    ↓                          ↑ inilah pemecah siklus: FakturPembelian.penerimaan
akunting/0004_trigger_jurnal_seimbang
    ↓
akunting/0005_seed_coa
    ↓
warehouse/0002_… → warehouse/0003_…
```

App lain bergantung turun saja: `inventory/0001` ← core+master ·
`produksi/0001` ← core+inventory+master · `keuangan/0001` ← akunting/0002+core+master ·
`keuangan/0002` ← core/0003+keuangan/0001 · `work_order/0001` ← hanya AUTH_USER.

`audit/0001_initial` bergantung pada `contenttypes/0002` dan `core/0003_seed_entitas`
— **tapi tidak akan pernah dieksekusi** karena `audit` tidak ada di
`INSTALLED_APPS` (`settings.py:75-96`), jadi Django tidak memuat berkas
migrasinya sama sekali.

---

## 8. Berkas yatim (tidak diimport siapa pun)

Django menemukan sendiri `models.py`, `admin.py`, `apps.py`, `urls.py` (lewat
string di `include()`), `tests.py`, dan `settings.py` — berkas itu tidak
dihitung yatim. `staff_user/authentication.py` juga tidak yatim: dirujuk lewat
string di `settings.py:157`.

### 8a. Kode mati sesungguhnya

| Berkas | Ukuran | Status |
|---|---|---|
| **seluruh direktori `audit/`** | 117+83+53+22+22+11+1 baris | App **tidak ada di `INSTALLED_APPS`** (`settings.py:75-96`) dan `audit.urls` tidak di-`include` (`pracindo_erp/urls.py:7-27`). `audit/services.py` (`catat`, `catat_perubahan_status`, `riwayat_objek`) **tidak dipanggil satu berkas pun**. `audit/permissions.py` hanya berisi docstring 1 baris. Tabel `audit_jejak_aktivitas` tidak akan pernah dibuat. |
| `akunting/services.py:406-433` `lampirkan_dokumen()` | 28 baris | Tidak dipanggil siapa pun; tidak ada endpoint. Ini satu-satunya kode yang menulis `dokumen.Lampiran` — artinya **tidak ada jalur unggah lampiran sama sekali** di seluruh sistem, padahal 4 model punya FK ke sana. |
| `inventory/services.py:364-394` `lunasi_posisi()` | 31 baris | Penyelesaian tunai antar entitas (SZA) — tidak dipanggil, tidak ada endpoint. |
| `inventory/services.py:559-577` `verifikasi_rantai_saldo()` | 19 baris | Pemeriksa invariant (3) dengan raw SQL — tidak dipanggil, tidak ada endpoint (`VerifikasiView` hanya memanggil 3 fungsi lain). |
| `akunting/posting_rules.py:83-90` `KLAIM_HUTANG`/`KLAIM_PIUTANG` | 8 baris | Aturan jurnal untuk penyelesaian SZA — tidak pernah jadi argumen `posting()`. |
| `akunting/posting_rules.py:60-80` `RETUR_BELI`, `PENJUALAN`, `TERIMA_PIUTANG` | 21 baris | Terdefinisi, tanpa pemanggil. |
| `staff_user/permissions.py:167-186` `AksesEntitas`, `BacaSaja` | 20 baris | Dua permission class yang **tidak dipasang di view mana pun** (grep = 0). |
| `staff_user/serializers.py:15-24` `ProfilRingkasSerializer` | 10 baris | Tidak dirujuk view mana pun. |
| `master/views.py:30-33` `SatuanViewSet`, `:68-72` `PelangganViewSet` | 9 baris | Tidak didaftarkan di router (`master/urls.py:10-13`). |
| `master/serializers.py:7-16` `KategoriSerializer`, `SatuanSerializer` | 10 baris | `SatuanSerializer` hanya dipakai `SatuanViewSet` yang mati; `KategoriSerializer` tidak dirujuk sama sekali. |
| `master/serializers.py:63-68` `PelangganSerializer` | 6 baris | idem |
| `akunting/models/pembelian.py:134-153` `PurchaseOrder.kirim()`, `.batalkan()` | 20 baris | Duplikat dari `akunting/services.py:362` dan `:378`; view memanggil versi service, bukan versi model. |
| `akunting/models/akun.py:89-130` `SaldoAkunBulanan` | model utuh | Tidak ada kode yang menulis maupun membacanya (grep: hanya `models/akun.py`, `models/__init__.py`, `admin.py`). |
| `keuangan/models.py:128-179` `RencanaBayar` | model utuh | Tidak ada service, tidak ada endpoint (grep: hanya `models.py` + `admin.py`). |
| `produksi/models.py:49-51` `Resep.susut_wajar` | field | Divalidasi `CheckConstraint`, tidak pernah dibaca kode mana pun. |
| `warehouse/models.py:184-188` `PenerimaanItem.selisih_po` | property | Dirancang untuk mendeteksi `KURANG_KIRIM`, tidak dipakai `_periksa_selisih()`. |

### 8b. Berkas kosong 0 byte (scaffold `scaffold.ps1` yang tidak pernah diisi)

`core/permissions.py` · `master/permissions.py` · `master/services.py` ·
`dokumen/permissions.py` · `dokumen/serializers.py` · `dokumen/services.py` ·
`inventory/permissions.py` · `keuangan/permissions.py` ·
`warehouse/permissions.py` · `produksi/permissions.py` ·
`work_order/permissions.py` · `work_order/services.py` ·
`pajak/{permissions,serializers,services}.py` ·
`sales_order/{permissions,serializers,services}.py` ·
`logistik/{permissions,serializers,services}.py`
= **21 berkas kosong**.

Ditambah 4 `views.py` scaffold (`dokumen`, `pajak`, `sales_order`, `logistik`)
yang hanya berisi `from django.shortcuts import render`, dan 14 `tests.py`
scaffold — **tidak ada satu pun test di seluruh repo**.

> `akunting/permissions.py` **tidak ada sama sekali** — satu-satunya app dengan
> endpoint yang tidak punya berkas itu, meski scaffold-nya seragam di app lain.

### 8c. Duplikasi

| Lokasi | Masalah |
|---|---|
| `master/urls.py:4` dan `:6` | `ProdukViewSet` diimpor **dua kali**: `from master.views import ProdukViewSet` (absolut) lalu `from .views import ProdukViewSet, SuplierViewSet` (relatif) |
| `staff_user/urls.py:18` & `:20` | `/daftar/` dan `/register/` menunjuk view yang sama |
| `akunting/views.py` `_galat()` `:35` | Fungsi identik disalin di 5 berkas: `core/views.py:23`, `staff_user/views.py:26`, `inventory/views.py:39`, `warehouse/views.py:33`, `akunting/views.py:35`. Versi `produksi/views.py:11` **berbeda** (memakai `e.message`, bukan `e.message_dict`) |
| `keuangan/views.py:36` | Pola penanganan galat ke-3 lagi (`except Exception` telanjang) |

---

## 9. Ringkasan graf ketergantungan

| App | Mengimpor (modul) | Mengimpor (fungsi) | Diimpor oleh | Fan-in | Fan-out |
|---|---|---|---|---|---|
| `core` | — | — | 11 app | **11** | 0 |
| `staff_user` | core | core | akunting, core, inventory, master, produksi, warehouse, work_order, audit | 8 | 1 |
| `master` | core | — | akunting(F) | 1 | 1 |
| `dokumen` | core | — | akunting(F) | 1 | 1 |
| `inventory` | core | — | produksi, warehouse(F) | 2 | 1 |
| `akunting` | core, staff_user | core, master, dokumen, warehouse | keuangan, warehouse | 2 | 6 |
| `keuangan` | core, **akunting** | — | — | 0 | 2 |
| `warehouse` | core, staff_user, **akunting** | akunting, inventory | akunting(F) | 1 | 4 |
| `produksi` | core, staff_user, inventory | — | — | 0 | 3 |
| `work_order` | staff_user | — | — | 0 | 1 |
| `pajak`, `sales_order`, `logistik` | — | — | — | 0 | 0 |
| `audit` | staff_user, (core lewat FK string) | — | **— (tidak terpasang)** | 0 | 1 |

`core` adalah pusat gravitasi dengan fan-in 11 dan fan-out 0 — persis yang
dijanjikan docstring `core/models.py:4-6`, dan itu ditegakkan dengan benar.
Titik lemahnya ada di lapis 4, tempat `akunting` dan `warehouse` saling terikat
dua arah.
