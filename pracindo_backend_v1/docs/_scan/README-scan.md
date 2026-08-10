# SCAN ARSITEKTUR BACKEND — pracindo_backend_v1

Django 5.2.10 · DRF · PostgreSQL · Python 3.12.10
Branch `fix/migrasi-tertunda` · scan 2026-08-05 · **read-only, tidak ada kode yang diubah**

---

## Peta besar sistem

**Empat entitas pembukuan** (PT, CV, Agus, Marsini) berbagi satu bagan akun dan
dua **grup bahan** (pool `PT` sendiri, pool `BERSAMA` untuk tiga sisanya).
Dua sumbu itu sengaja dipisah: entitas menjawab *siapa berhutang*, grup bahan
menjawab *bahan siapa bercampur di tanki*.

```
                    ┌─────────── core ───────────┐        lapis 1
                    │ Entitas · GrupBahan        │        fan-in 11, fan-out 0
                    │ CounterDokumen (penomoran) │
                    │ PeriodeAkuntansi (kunci)   │
                    └────────────▲───────────────┘
   staff_user (AUTH_USER_MODEL, RBAC berbasis dict AKSES_MODUL)
        ▲
   master · dokumen                                        lapis 2
        ▲
   inventory  ── mesin stok 3 lapis + buku klaim SZA       lapis 3
        ▲
   akunting · keuangan · warehouse · produksi · work_order lapis 4
   (pajak · sales_order · logistik = stub kosong)
```

### Dua pipeline utama

**1. Pembelian → hutang → kas**
```
akunting.buat_po()          PO DRAFT → kirim → TERKIRIM      (bukan kejadian ekonomi)
       ↓
warehouse.terima_barang()   11 tabel, 1 transaksi atomik:
                            stok RAW naik · SaldoEntitas · PO.qty_diterima ·
                            laporan selisih otomatis ·
                            JURNAL Dr Persediaan / Cr GRNI          ← liabilitas LAHIR di sini
       ↓
akunting.terbitkan_faktur() Dr GRNI / Cr Hutang  (+ FAKTUR_LEBIH/KURANG ke 5900)
       ↓
akunting.alokasi_pembayaran() FIFO per jatuh tempo, sisa → UangMuka
                            Dr Hutang / Cr Kas
```

**2. Kepemilikan proporsional SZA (tiga lapis stok)**
```
RAW   pemilik melekat (SaldoEntitas: qty + nilai perolehan)
  │  setor_ke_pool()  fisik lepas, nilai keluar PROPORSIONAL (rata-rata tertimbang),
  │                   hak jadi MutasiKlaim (+qty × tarif ekuivalen)
  ▼
POOL  TANPA pemilik. Hak ada di buku klaim.
  │  produksi: pakai_dari_pool() → hasil_ke_pool()
  ▼
JADI  klaim_hasil(): hak berkurang (−), fisik dapat pemilik lagi
      PosisiKlaim.nilai_bersih < 0  ⇒  entitas itu berhutang ke grup
```
Kuncinya: **tarif ekuivalen disimpan di setiap baris `MutasiKlaim`**, sehingga
perubahan tarif berlaku prospektif dan sejarah tidak ditulis ulang. Itu yang
membuat posisi N-produk × M-entitas runtuh jadi M angka rupiah-ekuivalen.

### Angka pokok

| | |
|---|---|
| App terpasang | 13 lokal + 5 pihak ketiga (`audit` **tidak** terpasang) |
| Model terdaftar | **44** (+1 mati di `audit`) · 46 constraint · 24 index · **1 trigger DB** |
| Endpoint | **151** kombinasi method+path (verifikasi resolver = OpenAPI) |
| Baris Python | 9.928 non-migration + 2.049 migration |
| Signal · task queue · throttle | **0 · 0 · 0** |
| Test | **0** |
| Auth | `ExpiringTokenAuthentication` (12 jam, satu sesi/pengguna) |
| Permission default | `IsAuthenticated`; 17 view memakai `AksesModul` berbasis dict |

---

## Berkas keluaran

| Berkas | Isi |
|---|---|
| `00-inventory.md` | Settings, INSTALLED_APPS, middleware, DRF config, DB, inventaris berkas per app, hasil cross-check drf-spectacular |
| `01-api-map.md` | 151 endpoint: method · path · view:baris · serializer in/out · permission · queryset · filter · paginasi · status · efek samping. Plus 5 tabel penanda wajib (AllowAny, write tanpa izin, multi-tabel tanpa atomic, serializer tanpa validasi) dan bagian CROSS-CHECK |
| `api-map.json` | 107 entri endpoint terstruktur + daftar view/serializer/model yang tidak terjangkau |
| `openapi.yaml` | Schema mentah dari `manage.py spectacular` (187 KB, 32 warning / 48 error) |
| `02-data-model.md` | 44 model: field, null/blank, default, unique, choices, FK/M2M/O2O + related_name + on_delete, Meta constraints, index, manager, property, `save()` override, trigger DB. Penanda FK-tanpa-index, CASCADE di data akuntansi, field uang non-Decimal |
| `03-algorithms.md` | 17 algoritma non-CRUD, masing-masing dengan trigger, prasyarat, pseudocode, invariant, edge case, perilaku transaksi & locking, idempotensi, kompleksitas & N+1 |
| `04-dependencies.md` | Graf import antar app (modul vs dalam-fungsi), pelanggaran aturan lapis, panggilan lintas app (service vs model langsung), siklus & workaround, graf migrasi, berkas yatim |
| `05-findings.md` | 64 temuan berperingkat: **8 CRITICAL · 17 HIGH · 24 MEDIUM · 15 LOW**, plus daftar praktik yang sudah benar agar tidak dirusak saat perbaikan |
| `README-scan.md` | Dokumen ini |

---

## 5 hal yang paling perlu diperbaiki

### 1. Modul `keuangan` tidak punya kontrol akses sama sekali — dan bisa merusak buku besar
`keuangan/views.py:10` tidak menetapkan `permission_classes` maupun `modul`,
sehingga jatuh ke `IsAuthenticated`. **Setiap pengguna yang login, termasuk role
`STAFF`, bisa mengeluarkan kas kecil, memotong saldo rekening, dan memposting
jurnal.** Lebih buruk: `PUT`/`PATCH`/`DELETE` tidak di-override, jadi `nominal`
sebuah pengeluaran bisa diubah — atau barisnya dihapus — **tanpa** menyentuh
`MutasiKas`, saldo rekening, maupun jurnal. Karena tidak ada signal di seluruh
sistem (FASE 4 §5), tidak ada apa pun yang menangkap divergensi itu.
→ *05-findings.md C1, C2*

### 2. Idempotensi dimatikan tepat di dua jalur uang
Infrastrukturnya sudah benar — kolom `idempotency_key` `UNIQUE` ada di
`MutasiStok`, `MutasiKlaim`, `MutasiKas`, dan `JurnalUmum`. Tapi dua pemanggil
membuang kuncinya: `PembayaranView` membangkitkan `f'bayar:{uuid4()}'` baru
setiap request (`akunting/views.py:348`) dan `catat_pengeluaran` menyisipkan
`uuid4()` ke dalam kunci (`keuangan/services.py:46`). Klik ganda atau retry
jaringan = **pembayaran hutang dobel**. `KartuHutang.referensi` juga tidak
`unique`, jadi DB pun tidak menangkapnya. Bandingkan dengan
`produksi/services.py:156` yang memakai kunci deterministik — pola yang benar
sudah ada di repo yang sama.
→ *05-findings.md C3, C4, H16*

### 3. Invariant SZA rusak setiap kali satu sesi produksi selesai
`pakai_dari_pool()` dan `hasil_ke_pool()` (`inventory/services.py:263-302`)
menggerakkan stok POOL **tanpa menulis satu baris pun ke `MutasiKlaim`**.
Karena nilai ekuivalen bahan yang dipakai ≠ nilai ekuivalen produk jadi yang
masuk, invariant `SUM(PosisiKlaim.nilai_bersih) = nilai sisa POOL` — yang oleh
`inventory/models.py:13-17` disebut *"invariant utama"* — menyimpang permanen.
Angka siapa berhutang ke siapa antar PT/CV/Agus/Marsini jadi tidak bisa
dipercaya, dan `verifikasi_pool_bersih()` akan selalu melapor selisih tanpa ada
mekanisme koreksi. Ditambah: `lunasi_posisi()` yang dirancang untuk penyelesaian
tunai antar entitas **tidak dipanggil siapa pun** dan tidak punya endpoint.
→ *05-findings.md C6, L13*

### 4. Buku besar dan subledger bocor di tiga titik
- **GRNI**: potongan klaim tidak pernah dibersihkan dari akun 2190 — saldonya
  menggantung selamanya (`akunting/services.py:589-632`).
- **Hutang usaha**: `alokasi_pembayaran()` memposting `Dr 2100` sebesar nominal
  **penuh**, termasuk kelebihan bayar yang menjadi uang muka
  (`akunting/services.py:233`) — hutang didebet lebih besar dari yang berkurang.
- **Persediaan**: opname mengubah `Stok.qty` dan `SaldoEntitas.nilai` **tanpa
  jurnal apa pun** (`inventory/services.py:401`).
- Ditambah: pembayaran suplier tidak pernah menyentuh `MutasiKas`/`RekeningBank`
  — kas berkurang di buku besar tapi tidak di buku bank.
Empat invariant ini tidak dijaga constraint DB mana pun; hanya invariant
keseimbangan jurnal yang punya trigger.
→ *05-findings.md H3, C5, H4, H5*

### 5. Jejak audit yang sudah dibangun lengkap tidak dipasang
App `audit` punya model 117 baris, service 83 baris, viewset, serializer, admin,
dan migrasi — tapi **tidak ada di `INSTALLED_APPS`** (`settings.py:75-96`),
`audit.urls` tidak di-`include`, dan `audit.services.catat()` tidak dipanggil
satu berkas pun. Tabel `audit_jejak_aktivitas` tidak akan pernah dibuat.
Akibatnya tidak ada jejak sama sekali untuk perubahan status yang tidak
menghasilkan jurnal — siapa membatalkan PO, siapa menutup periode, siapa
mengubah role — persis yang docstring `audit/models.py:13-18` sebut sebagai
*"yang paling sering ditanyakan saat ada masalah"*.
Terkait: modul `work_order` juga tidak berfungsi karena
`getattr(request.user, 'profil_staff_id', None)` merujuk atribut yang tidak
ada pada `Profil` — papan tugas selalu kosong dan `approve` selalu 403.
→ *05-findings.md H11, H1, H2*

---

## Catatan metode

- Sumber kebenaran = kode. Yang tidak bisa diverifikasi ditandai `UNKNOWN`
  (tidak ada dalam scan ini — semua klaim terverifikasi).
- Setiap klaim menyertakan rujukan `path/file.py:baris`.
- Verifikasi tambahan yang dijalankan (semuanya read-only, tanpa menyentuh DB write):
  - `python manage.py spectacular --file docs/_scan/openapi.yaml` → exit 0
  - `python manage.py makemigrations --check --dry-run` → **"No changes detected"**
    (model dan migrasi sinkron, termasuk 3 migrasi yang belum di-commit)
  - Penelusuran `django.urls.get_resolver()` untuk mengenumerasi seluruh rute
  - Parsing AST atas 110 berkas `*.py` untuk graf import dan deteksi berkas yatim
  - `apps.get_app_config(...).get_models()` untuk menghitung model terdaftar
- `*/migrations/*` dibaca **hanya** untuk merekonstruksi constraint, index, dan
  trigger DB — bukan untuk analisis logika.
- `*.md`, `*.txt`, `.git/`, `venv/`, `__pycache__/`, `staticfiles/`, `media/`,
  `requirements*.txt` dikecualikan sesuai instruksi.
