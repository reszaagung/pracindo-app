# FASE 3 — ALGORITMA

Semua logika non-CRUD di repo. Yang murni `serializer.save()` tidak masuk.
17 algoritma, dikelompokkan per domain.

Ringkasan cepat:

| # | Algoritma | Lokasi | atomic | lock | idempoten |
|---|---|---|---|---|---|
| 1 | Penomoran dokumen | `core/models.py:181` | ❌ (bergantung pemanggil) | ✅ `select_for_update` | ✅ monoton |
| 2 | Penguncian periode | `core/services.py:22` | ✅ | ✅ | ✅ |
| 3 | Resolusi AksesModul (RBAC) | `staff_user/permissions.py:59` | — | — | ✅ murni |
| 4 | Autentikasi token kedaluwarsa | `staff_user/authentication.py:32` | ❌ | ❌ | ⚠ menulis (DELETE) |
| 5 | Aktivasi + penetapan peran | `staff_user/services.py:44` | ✅ | ✅ | ❌ menolak ulang |
| 6 | Generate kode master | `master/utils.py:3` | ❌ | ❌ | ❌ **balapan** |
| 7 | Posting double-entry | `akunting/services.py:39` | ✅ | ✅ (via counter) | ✅ `idempotency_key` |
| 8 | Jurnal balik | `akunting/services.py:114` | ✅ | ✅ | ✅ (via `dibalik_oleh` + key) |
| 9 | Terima barang (GRN) | `warehouse/services.py:51` | ✅ | ✅ | ⚠ sebagian |
| 10 | Deteksi selisih otomatis | `warehouse/services.py:231` | ✅ (induk) | — | ❌ |
| 11 | Penyelesaian selisih | `warehouse/services.py:335` | ✅ | ✅ | ⚠ |
| 12 | Terbitkan faktur + GRNI clearing | `akunting/services.py:531` | ✅ | ✅ | ⚠ |
| 13 | Alokasi pembayaran FIFO | `akunting/services.py:186` | ✅ | ✅ | ❌ **key acak** |
| 14 | Aging hutang | `akunting/services.py:643` | — | — | ✅ murni |
| 15 | Mesin stok tiga lapis (SZA) | `inventory/services.py:169-444` | ✅ | ✅ | ✅ |
| 16 | Kapasitas & sesi produksi | `produksi/services.py:36-223` | ✅ | ✅ | ✅ (via key) |
| 17 | Pengeluaran kas kecil | `keuangan/services.py:9` | ✅ | ✅ | ❌ **key acak** |

---

## 1. Penomoran dokumen atomik — `CounterDokumen.berikutnya()`

**Lokasi** `core/models.py:181-201` (+ `format_nomor` `:167`, `preview` `:203`).

**Trigger** — dipanggil dari 6 tempat, semuanya di dalam `save()` model atau service:
`PurchaseOrder.save()` `akunting/models/pembelian.py:122` ·
`FakturPembelian.save()` `akunting/models/hutang.py:162` ·
`PenerimaanBarang.save()` `warehouse/models.py:90` ·
`LaporanSelisih.save()` `warehouse/models.py:336` ·
`SesiProduksi.save()` `produksi/models.py:204` ·
`akunting.services.posting()` `akunting/services.py:62` dan
`jurnal_balik()` `:128`.

**Input & prasyarat**
- `entitas` (instance `Entitas`), `jenis` (string bebas, tanpa `choices`), `tanggal` (date)
- **WAJIB dipanggil di dalam `transaction.atomic`** (docstring `:183`) — kalau tidak,
  `select_for_update()` melempar `TransactionManagementError`.

**Pseudocode**
```
periode ← tanggal.strftime('%Y%m')
counter ← SELECT ... FOR UPDATE, get_or_create(entitas, jenis, periode)
counter.urutan += 1
SAVE counter (update_fields=['urutan'])
lebar ← LEBAR.get(jenis, 3)            # JURNAL = 4, sisanya 3
romawi ← BULAN_ROMAWI[tanggal.month-1]
RETURN f"{jenis}/{entitas.kode}/{tanggal.year}/{romawi}/{urutan:0{lebar}d}"
```

**Invariant**
- Nomor tidak pernah terpakai dua kali per `(entitas, jenis, periode)`.
- `urutan` hanya bertambah — dokumen yang dibatalkan tidak mengembalikan nomor.

**Edge case**
- Rollback transaksi mengembalikan `urutan` (docstring `:190`) → **nomor bisa
  bolong** kalau ada transaksi gagal setelah penomoran. Klaim di docstring
  "tidak ada nomor yang terlewat" berlaku untuk *duplikat*, bukan *gap*.
- `urutan > 999` untuk jenis 3-digit → format melebar jadi 4 digit
  (`f"{1000:03d}"` = `"1000"`); tidak crash, tapi lebar nomor berubah.
- `jenis` tidak punya `choices` (`core/models.py:137`) → salah ketik menciptakan
  seri counter baru diam-diam.

**Transaksi & locking** — `select_for_update()` mengunci baris counter untuk
sisa transaksi. Lock terpisah per `(entitas, jenis, periode)` → PT dan CV tidak
saling tunggu. ⚠ Karena lock dipegang sampai COMMIT, transaksi panjang seperti
`terima_barang()` (11 tabel) menahan counter GRN entitas itu selama seluruh
proses.

**Idempotensi** — TIDAK idempoten by design: dua panggilan = dua nomor.
Idempotensi dijaga di lapis atas lewat `idempotency_key`.

**Kompleksitas** O(1). Tidak ada N+1.

---

## 2. Penguncian periode akuntansi

**Lokasi** `core/services.py:22` (`pastikan_periode_terbuka`), `:44`
(`tutup_periode`), `:63` (`buka_periode`).

**Trigger** — `pastikan_periode_terbuka` dipanggil dari 7 titik:
`akunting.posting()` `:55` · `akunting.buat_po()` `:306` ·
`akunting.terbitkan_faktur()` `:574` · `warehouse.terima_barang()` `:95` ·
`inventory.terima_raw()` `:190` · `inventory.setor_ke_pool()` `:225` ·
`inventory.klaim_hasil()` `:332` · `inventory.sesuaikan_stok()` `:430` (bersyarat).
Endpoint: `GET /api/v1/core/periode/status/`.

**Pseudocode `pastikan_periode_terbuka`**
```
tertutup ← EXISTS(PeriodeAkuntansi WHERE entitas=? AND tahun=? AND bulan=? AND ditutup=True)
IF tertutup: RAISE PeriodeTertutup
RETURN None
```

**Invariant** — tidak ada jurnal/stok bertanggal periode yang `ditutup=True`.

**Edge case**
- **Periode yang barisnya belum ada dianggap TERBUKA** (`core/services.py:26-28`).
  Penguncian bersifat opt-in — sengaja, tapi berarti tidak ada perlindungan
  otomatis untuk periode lampau.
- ⚠ **`pakai_dari_pool()` dan `hasil_ke_pool()` TIDAK memanggilnya**
  (`inventory/services.py:263-302`) → seluruh alur produksi
  (`mulai_sesi`/`selesaikan_sesi`) bisa menggerakkan stok POOL ke periode yang
  sudah ditutup.
- ⚠ Pemeriksaan dilakukan **sebelum** menulis, tanpa lock. Periode yang ditutup
  tepat di antara pemeriksaan dan COMMIT tidak terdeteksi (jendela sempit).

**Transaksi & locking** — `tutup_periode`/`buka_periode` `@transaction.atomic`
+ `select_for_update`. `pastikan_periode_terbuka` hanya `EXISTS`, tanpa lock.

**Idempotensi** — `tutup_periode` idempoten (`:53-54` return awal kalau sudah
tertutup). `buka_periode` **tidak** — setiap panggilan menambah satu baris jejak
ke `alasan_buka` (`:79`), TextField yang tumbuh tanpa batas.

**Kompleksitas** O(1), memakai `ix_periode_lookup`.

---

## 3. Resolusi AksesModul (RBAC)

**Lokasi** `staff_user/permissions.py:24` (`AKSES_MODUL`), `:59`
(`role_boleh_modul`), `:67` (`modul_untuk_role`), `:90` (class `AksesModul`),
`:115` (`PunyaRole`), `:152` (`DiriSendiriAtauSupervisor`), `:167` (`AksesEntitas`).
Method model pendamping: `Profil.punya_role` `staff_user/models.py:196`,
`bisa_akses_modul` `:208`, `bisa_akses_entitas` `:212`, `entitas_terlihat` `:219`.

**Trigger** — setiap request DRF yang view-nya memakai `AksesModul` (17 view),
plus `GET /api/v1/auth/portal/` (`staff_user/views.py:122`) yang mengembalikan
peta modul ke frontend.

**Pseudocode `AksesModul.has_permission`**
```
u ← request.user
IF NOT (u AND u.is_authenticated AND u.bisa_login):  RETURN False
modul ← getattr(view, 'modul', None)
IF NOT modul: RETURN False                     # gagal TERTUTUP
RETURN u.bisa_akses_modul(modul)
   └─ role_boleh_modul(role, modul, is_superuser):
        IF is_superuser: True
        IF role == SUPERVISOR: True            # SUPERVISOR lolos SEMUA modul
        RETURN role in AKSES_MODUL.get(modul, [])
```
`bisa_login` = `is_active AND status_kerja != KELUAR` (`models.py:186`).

**Invariant**
- View tanpa atribut `modul` **selalu ditolak** — gagal tertutup, bukan terbuka.
- Peta akses hidup di satu dict, bukan tersebar sebagai `if` di view.

**Edge case & pelanggaran yang ditemukan**
1. `PunyaRole` **tidak** meloloskan SUPERVISOR (hanya `is_superuser` atau role
   yang persis cocok, `models.py:198`). Akibatnya
   `GudangProduksi = PunyaRole.dengan(GUDANG, PRODUKSI)` (`inventory/views.py:36`)
   **memblokir role SUPERVISOR** dari `setor-ke-pool` dan `klaim-hasil` —
   berlawanan dengan `AksesModul` yang selalu meloloskan SUPERVISOR.
2. `HanyaSupervisor` (`permissions.py:137`) hanya `roles=(SUPERVISOR,)` — jadi
   ADMIN tidak bisa melakukan opname/verifikasi/tutup periode. Konsisten,
   tapi berarti dua model kewenangan hidup berdampingan.
3. `keuangan` dan `work_order` tidak memakai sistem ini sama sekali —
   `keuangan/views.py:10` tanpa `permission_classes`, `work_order/views.py:14`
   `IsAuthenticated`. Modul `keuangan` dan `work_order` ada di `AKSES_MODUL`
   (`permissions.py:28,35`) dan dikirim ke frontend lewat `/auth/portal/`,
   tapi **backend-nya tidak menegakkan apa pun**.
4. `AksesEntitas` (`permissions.py:167`) **tidak dipasang di satu view pun**
   (grep = 0). Pembatasan entitas dilakukan ad-hoc lewat `filter_entitas()`
   (`akunting/views.py:44`) dan panggilan manual `bisa_akses_entitas()` di 2 view.
5. `DiriSendiriAtauSupervisor` hanya punya `has_object_permission` — tidak
   melindungi `create`/`list`.
6. `BacaSaja` (`permissions.py:182`) juga tidak dipakai di mana pun.
7. `modul` di `core/views.py:29,38` (`'master'`) dan `audit/views.py:24` inert
   karena view-nya memakai `HanyaSupervisor`, bukan `AksesModul`.

**Transaksi & locking** — tidak ada.
**Idempotensi** — fungsi murni.
**Kompleksitas** — `bisa_akses_entitas()` (`models.py:212-217`) melakukan
`izin.exists()` lalu `izin.filter(...).exists()` → **2 query per pemanggilan**,
tidak di-cache. `filter_entitas()` (`akunting/views.py:47`) melakukan
`u.entitas_diizinkan.exists()` lalu `u.entitas_diizinkan.all()` sebagai subquery
→ 1 query ekstra per request list.

---

## 4. Autentikasi token kedaluwarsa

**Lokasi** `staff_user/authentication.py:24-50`.
**Trigger** — setiap request ber-`Authorization: Token …` (default global,
`settings.py:156`).

**Pseudocode**
```
token ← SELECT ... JOIN user WHERE key = ?        # select_related('user')
IF NOT FOUND:            RAISE AuthenticationFailed('Token tidak dikenali.')
IF NOT user.is_active:   RAISE AuthenticationFailed('Akun sudah dinonaktifkan.')
IF NOT user.bisa_login:  DELETE token; RAISE('Akun sudah tidak berlaku.')
IF now - token.created > TOKEN_EXPIRE_HOURS:  DELETE token; RAISE('Sesi berakhir')
RETURN (user, token)
```

**Invariant** — token yang lolos selalu milik akun aktif dan belum lewat umur.

**Edge case**
- `token.created` **tidak pernah diperbarui** — umur dihitung dari penerbitan,
  bukan aktivitas terakhir. Sesi 12 jam adalah batas keras (sliding window tidak ada).
- `terbitkan_token()` (`services.py:224`) menghapus token lama setiap login →
  **satu sesi per pengguna**; login di perangkat kedua melempar perangkat pertama.
- **Penulisan DB di jalur autentikasi**: `token.delete()` di baris `:43` dan `:47`
  terjadi di dalam request GET biasa. Aman, tapi berarti GET bisa menulis.
- Tidak ada penanganan `MultipleObjectsReturned` (tidak mungkin — `key` adalah PK).

**Transaksi & locking** — tidak ada; `delete()` autocommit.
**Idempotensi** — pembacaan idempoten; penghapusan idempoten secara efektif.
**Kompleksitas** O(1) dengan `select_related`.

---

## 5. Aktivasi akun + penetapan peran

**Lokasi** `staff_user/services.py:44-83`.
**Trigger** `POST /api/v1/auth/profil/{id}/aktifkan/` (`staff_user/views.py:179`).

**Pseudocode**
```
IF NOT oleh.supervisor: RAISE
profil ← SELECT ... FOR UPDATE WHERE pk = profil_id
IF profil.is_active: RAISE 'sudah aktif'
IF role == SUPERVISOR AND NOT oleh.is_superuser: RAISE
IF nip AND EXISTS(other profil with nip): RAISE
set role, is_active=True, jabatan, nip, entitas_default, atasan,
    tanggal_masuk (default hari ini), status_kerja=AKTIF,
    disetujui_oleh, disetujui_pada, ditolak_pada=None, alasan_tolak=''
SAVE profil                        # save() penuh, bukan update_fields
IF entitas_diizinkan_ids: profil.entitas_diizinkan.set(ids)
```

**Invariant** — persetujuan dan penetapan peran terjadi bersamaan; tidak ada
jendela "aktif tapi masih STAFF".

**Edge case**
- Cek NIP unik dilakukan di Python (`:64`) **selain** `unique=True` di kolom —
  balapan tetap ditangkap DB sebagai `IntegrityError` (500, bukan 400).
- `jabatan_id`, `entitas_default_id`, `atasan_id` tidak divalidasi keberadaannya
  → `IntegrityError` 500 untuk id palsu.
- `atasan_id == profil_id` tidak dicek di sini; `clean()` (`models.py:227`)
  mengeceknya tapi `clean()` tidak dipanggil oleh service.

**Transaksi & locking** `@transaction.atomic` + `select_for_update` ✅.
**Idempotensi** — TIDAK: panggilan kedua raise `'Akun ini sudah aktif.'`.
**Kompleksitas** O(1) + 1 query untuk cek NIP.

---

## 6. Generate kode master berurutan

**Lokasi** `master/utils.py:3-24`.
**Trigger** — `save()` dari `Kategori` `master/models.py:32`, `Suplier` `:91`,
`Produk` `:121`, `Pelanggan` `:165`. Lewat API:
`POST /api/v1/master/produk/`, `POST /api/v1/master/suplier/`.

**Pseudocode**
```
last ← Model.objects.filter(kode__startswith=f"{prefix}-").order_by('kode').last()
IF last:
    TRY:  n ← int(last.kode.split('-')[1]) + 1
    EXCEPT (IndexError, ValueError): n ← 1
ELSE: n ← 1
RETURN f"{prefix}-{n:0{padding}d}"
```

**Invariant yang DIHARAPKAN** — kode unik dan berurutan per prefix.

**Edge case & pelanggaran**
1. **Tidak ada lock dan tidak ada transaksi.** Dua request bersamaan membaca
   `last` yang sama → dua kode identik → `IntegrityError` pada `unique=True`
   (500 untuk salah satu pengguna). Bandingkan dengan `CounterDokumen` yang
   memakai `select_for_update` untuk masalah yang persis sama.
2. **`order_by('kode')` adalah urutan LEKSIKOGRAFIS.** Dengan `padding=4`,
   setelah `BP-9999` datang `BP-10000`, dan `'BP-10000' < 'BP-9999'` secara
   string → `.last()` tetap mengembalikan `BP-9999` selamanya → kode duplikat
   permanen. Untuk `Kategori` (`padding=3`) batasnya `KAT-999`.
3. **`except: n ← 1`** — satu baris rusak (mis. kode diketik manual `BP-A`)
   membuat generator mengembalikan `BP-0001` yang sudah dipakai.
4. Migrasi `master/0003` mengubah `kode` jadi `blank=True` untuk 4 model
   (`master/migrations/0003_...py:12-32`) supaya serializer lolos — artinya
   klien **boleh mengirim `kode` sendiri** dan melewati generator sepenuhnya
   (`ProdukSerializer.fields` memuat `kode`, `master/serializers.py:27`).

**Transaksi & locking** — tidak ada keduanya.
**Idempotensi** — tidak relevan (dipanggil di dalam `save()`), tapi **tidak
deterministik di bawah konkurensi**.
**Kompleksitas** O(1) query (index `kode` unik dipakai), tapi `LIKE 'BP-%'`
pada B-tree tetap efisien untuk prefix.

---

## 7. Posting double-entry — `akunting.services.posting()`

**Lokasi** `akunting/services.py:39-111`. Peta akun `akunting/posting_rules.py:19-91`.

**Trigger** — 4 pemanggil:
`warehouse._posting_penerimaan()` `warehouse/services.py:215` (`AUDIT_GUDANG`) ·
`akunting.terbitkan_faktur()` `:616,625` (`FAKTUR_MASUK`, `FAKTUR_LEBIH`/`FAKTUR_KURANG`) ·
`akunting.alokasi_pembayaran()` `:233` (`BAYAR_HUTANG`) ·
`keuangan.catat_pengeluaran()` `keuangan/services.py:52` (`BEBAN_KAS`).

**Input & prasyarat**
- `kejadian` harus ada di `ATURAN` (11 kunci)
- `nilai` = dict `{nama_field: Decimal}` sesuai field yang dirujuk aturan
- `idem_key` unik per kejadian bisnis
- Akun dalam aturan harus sudah ada (seed COA `akunting/migrations/0005`)
- Periode harus terbuka

**Pseudocode**
```
lama ← JurnalUmum WHERE idempotency_key = idem_key
IF lama: RETURN lama                                  # idempoten
IF kejadian NOT IN ATURAN: RAISE
pastikan_periode_terbuka(entitas_id, tanggal)
entitas ← Entitas.get(entitas_id)                     # .get() tanpa guard
jurnal ← INSERT JurnalUmum(nomor=CounterDokumen.berikutnya(...), ...)
akun ← {a.kode: a FOR a IN Akun WHERE kode IN kode_dipakai}   # 1 query
IF ada kode yang hilang: RAISE
baris, total_d, total_k ← [], 0, 0
FOR (kode, sisi, field) IN ATURAN[kejadian]:
    IF field NOT IN nilai: RAISE
    n ← Decimal(nilai[field]).quantize(0.01)
    IF n == 0: CONTINUE                               # baris nol dilewati
    IF n < 0:  RAISE 'arah lewat sisi D/K, bukan tanda'
    baris.append(JurnalDetail(debit=n if D else 0, kredit=n if K else 0))
    akumulasi total_d / total_k
IF baris kosong: RAISE
IF total_d != total_k: RAISE                          # penjaga ke-1 (Python)
bulk_create(baris)                                    # penjaga ke-2: TRIGGER DB saat COMMIT
RETURN jurnal
```

**Invariant**
1. `SUM(debit) = SUM(kredit)` per jurnal — dijaga **dua lapis**: cek Python
   `:104` dan `CONSTRAINT TRIGGER trg_jurnal_seimbang` (DEFERRED, dicek saat
   COMMIT — `akunting/migrations/0004:46`).
2. Satu `idem_key` = satu jurnal, dijamin `UNIQUE` di kolom `idempotency_key`.
3. Nilai selalu non-negatif; arah dinyatakan lewat sisi D/K.

**Edge case**
- `bulk_create` **melewati `JurnalDetail.clean()`** (`jurnal.py:152`) → posting
  ke akun header (`boleh_diposting=False`) **tidak diblokir**. Aturan di
  `posting_rules.py` kebetulan hanya memakai akun leaf, tapi tidak ada penjaga
  kalau seseorang menambah entri baru yang salah.
- Aturan `PENJUALAN` (`posting_rules.py:65`) punya 4 baris; kalau `hpp=0`
  sementara `nilai_jual>0`, baris HPP dan Persediaan dilewati (`n==0 → continue`)
  → jurnal tetap seimbang. Aman.
- Kalau **semua** nilai nol → raise, bukan jurnal kosong.
- `Entitas.objects.get(pk=entitas_id)` `:58` tanpa guard → `DoesNotExist` = 500.
- Aturan `KLAIM_HUTANG`/`KLAIM_PIUTANG` (`posting_rules.py:83-90`) **tidak
  pernah dipanggil siapa pun** — mekanisme jurnal untuk penyelesaian antar
  entitas SZA sudah didefinisikan tapi belum tersambung.
- Jenis kejadian `SELISIH_HARGA`, `RETUR_BELI`, `PENJUALAN`, `TERIMA_PIUTANG`,
  `PENYUSUTAN`, `PRODUKSI` ada di enum `JenisKejadian` (`jurnal.py:27-38`) tapi
  `RETUR_BELI`/`PENJUALAN`/`TERIMA_PIUTANG` hanya ada di `ATURAN` tanpa pemanggil,
  dan `PENYUSUTAN`/`PRODUKSI`/`SELISIH_HARGA` **tidak ada di `ATURAN` sama sekali**
  → memanggilnya akan raise di `:52`.
- ⚠ `kejadian` yang disimpan di kolom: untuk `FAKTUR_LEBIH`/`FAKTUR_KURANG`,
  string itu **bukan anggota `JenisKejadian.choices`** — `CharField(max_length=16)`
  menerimanya (Django tidak menegakkan `choices` di DB), tapi
  `get_kejadian_display()` akan mengembalikan string mentah dan filter
  `?kejadian=` di frontend tidak akan menemukannya sebagai pilihan.

**Transaksi & locking** `@transaction.atomic`. Lock tidak diambil pada jurnal
(tidak perlu — INSERT saja), tapi `CounterDokumen.berikutnya()` mengambil
`select_for_update` pada baris counter `JURNAL` entitas itu.

**Idempotensi** ✅ **penuh** — cek `idempotency_key` di awal + `UNIQUE` di DB.
Panggilan kedua mengembalikan jurnal yang sama tanpa efek samping.

**Kompleksitas** O(jumlah baris aturan) ≤ 4. Query: 1 SELECT idem + 1 EXISTS
periode + 1 SELECT entitas + 1 counter (FOR UPDATE) + 1 INSERT jurnal +
1 SELECT akun + 1 bulk INSERT = **7 query**. Tidak ada N+1.
⚠ Trigger `FOR EACH ROW` menjalankan `SUM()` atas `akunting_jurnal_detail`
sebanyak jumlah baris saat COMMIT — untuk 4 baris berarti 4 agregasi.

---

## 8. Jurnal balik

**Lokasi** `akunting/services.py:114-145`.
**Trigger** `POST /api/v1/akunting/jurnal/{id}/balik/` (`akunting/views.py:91`,
`PunyaRole(SUPERVISOR)`).

**Pseudocode**
```
asal ← SELECT ... FOR UPDATE WHERE pk = jurnal_id
IF asal.dibalik_oleh_id: RAISE 'sudah pernah dibalik'
pastikan_periode_terbuka(asal.entitas_id, tanggal)
balik ← INSERT JurnalUmum(kejadian='KOREKSI', referensi=asal.nomor,
                          idempotency_key=f'balik:{asal.id}',
                          nomor=CounterDokumen.berikutnya(...))
bulk_create([JurnalDetail(akun=b.akun, debit=b.kredit, kredit=b.debit)
             FOR b IN asal.baris.all()])              # D dan K DITUKAR
asal.dibalik_oleh ← balik; SAVE(update_fields=['dibalik_oleh'])
```

**Invariant** — jurnal asli tidak pernah disentuh isinya; hanya kolom
`dibalik_oleh` yang berubah. Jurnal balik otomatis seimbang karena hanya
menukar sisi.

**Edge case**
- Dobel-proteksi: `dibalik_oleh` adalah `OneToOneField` (unik) **dan**
  `idempotency_key='balik:{id}'` unik → dua percobaan balik menghasilkan
  `IntegrityError` yang jadi 500 (bukan 400) kalau lolos cek `:121` karena race.
- **Tidak ada cek `bisa_akses_entitas`** — Supervisor selalu lintas entitas
  (konsisten dengan `role_boleh_modul`).
- Jurnal balik dari jurnal balik dimungkinkan (`balik` sendiri punya
  `dibalik_oleh=None`) — key-nya `balik:{id_balik}`, jadi tidak bentrok.
- `asal.baris.all()` dieksekusi tanpa `select_related('akun')` tapi hanya
  `akun_id` yang dipakai `:137` → tidak ada N+1.

**Transaksi & locking** `@transaction.atomic` + `select_for_update` pada jurnal asal ✅.
**Idempotensi** ✅ efektif (dijaga `dibalik_oleh` + unique key).
**Kompleksitas** O(jumlah baris jurnal asal).

---

## 9. Terima barang (GRN) — algoritma terbesar

**Lokasi** `warehouse/services.py:51-132` + helper `_simpan_item` `:135`,
`_naikkan_stok` `:179`, `_posting_penerimaan` `:206`, `_periksa_selisih` `:231`.
**Trigger** `POST /api/v1/warehouse/penerimaan/` (`warehouse/views.py:87`).

**Input & prasyarat**
- `po_id` berstatus `TERKIRIM` atau `SEBAGIAN`
- `baris`: list dict `{po_item_id, jenis_kemasan, jumlah_koli, isi_per_koli,
  qty_diterima, qty_ditolak, alasan_tolak}` — **tanpa harga, tanpa grup_bahan,
  tanpa tangki**; semuanya diturunkan server
- surat jalan belum pernah dipakai untuk PO ini
- periode terbuka
- dokumen surat jalan sudah diunggah lebih dulu (`dokumen_id`)

**Pseudocode**
```
IF baris kosong: RAISE
po ← SELECT ... FOR UPDATE (select_related entitas, entitas__grup_bahan)
IF po.status == SELESAI: RAISE
IF po.status IN (DRAFT, BATAL): RAISE
pastikan_periode_terbuka(po.entitas_id, tanggal)
IF EXISTS(PenerimaanBarang WHERE po AND no_surat_jalan): RAISE

penerimaan ← INSERT PenerimaanBarang(...)      # save() → CounterDokumen 'GRN'
nilai_terima ← 0 ; laporan ← []
FOR b IN baris:
    item ← _simpan_item(penerimaan, b, po)
    nilai_terima += _naikkan_stok(penerimaan, item, po)
    laporan += _periksa_selisih(penerimaan, item, user)
IF nilai_terima <= 0: RAISE 'seluruh barang ditolak'

po.refresh_from_db()
po.status ← SELESAI IF po.semua_item_lengkap() ELSE SEBAGIAN
SAVE po(update_fields=['status'])
IF laporan: penerimaan.ada_selisih ← True; SAVE
_posting_penerimaan(penerimaan, nilai_terima, tanggal, user)   # Dr Persediaan / Cr GRNI
RETURN penerimaan, laporan
```

`_simpan_item` (`:135`)
```
po_item ← SELECT ... FOR UPDATE WHERE pk AND purchase_order = po
validasi: qty ≥ 0, tidak dua-duanya nol, alasan_tolak wajib bila ada tolakan
IF qty_terima > po_item.sisa_qty: RAISE           # yang ditolak TIDAK dihitung
item ← PenerimaanItem(...); item.full_clean(exclude=['qty_deklarasi']); item.save()
po_item.qty_diterima ← F('qty_diterima') + qty_terima ; SAVE(update_fields)
```

`_naikkan_stok` (`:179`)
```
nilai ← (item.qty_diterima * item.po_item.harga_per_kg).quantize(0.01)   # DI SERVER
inventory.terima_raw(produk_id=…, grup_bahan_id=po.entitas.grup_bahan_id,
                     entitas_id=po.entitas_id, qty=…, nilai=nilai,
                     idem_key=f'grn:{penerimaan.id}:item:{item.id}',
                     tangki_id=None)
RETURN nilai
```

**Invariant**
1. Stok naik **dan** jurnal GRNI terposting dalam transaksi yang sama — tidak
   pernah ada "stok naik tapi hutang belum tercatat".
2. `qty_diterima ≤ qty_pesan` per item — dijaga cek Python `:154` **dan**
   `CheckConstraint ck_poitem_terima_dalam_batas`.
3. Gudang tidak pernah melihat/mengirim angka rupiah.
4. Grup bahan selalu = `po.entitas.grup_bahan` — gudang tidak bisa salah pilih pool.

**Edge case**
- `F('qty_diterima') + qty` (`:174`) benar untuk balapan, tapi setelah `save()`
  atribut Python-nya jadi `CombinedExpression`; `po.semua_item_lengkap()` `:124`
  membaca ulang dari DB lewat query (`filter(qty_diterima__lt=F('qty_pesan'))`)
  → aman. `po.refresh_from_db()` `:123` diperlukan dan ada ✅.
- **`PurchaseOrderItem.save()` menghitung ulang `amount`** (`pembelian.py:220`)
  meski `update_fields=['qty_diterima']` — karena `save()` memaksa `'amount'`
  masuk ke `update_fields` `:225-226`. Nilainya sama, jadi tidak merusak.
- Toleransi berat `TOLERANSI_BERAT = 0.005` (`warehouse/services.py:44`) —
  **konstanta modul, tidak bisa dikonfigurasi per suplier/produk**.
- Kalau seluruh baris ditolak → raise **setelah** `PenerimaanBarang` dibuat dan
  counter GRN dinaikkan; rollback mengembalikan keduanya, tapi **nomor GRN
  hilang permanen** (gap).
- `item.full_clean(exclude=['qty_deklarasi'])` `:171` — memvalidasi `clean()`
  model, termasuk aturan kemasan non-curah wajib koli+isi.
- Tidak ada pemeriksaan bahwa `dokumen_id` benar-benar ada → `IntegrityError` 500.

**Transaksi & locking** `@transaction.atomic` membungkus **11 tabel** ✅.
Lock: `PurchaseOrder` (FOR UPDATE), setiap `PurchaseOrderItem` (FOR UPDATE),
`Stok`/`SaldoEntitas`/`Tangki` lewat `inventory.terima_raw()`, `CounterDokumen`
×2 (GRN + JURNAL) dan ×N (BAS untuk tiap laporan selisih).
⚠ **Urutan pengambilan lock**: PO → PO item → Stok → SaldoEntitas → counter.
Dua GRN untuk PO berbeda tapi produk sama akan mengunci `Stok` yang sama dari
urutan berbeda → **potensi deadlock** yang hanya diselesaikan Postgres dengan
membunuh salah satu transaksi.

**Idempotensi** ⚠ **sebagian**:
- `inventory.terima_raw()` idempoten lewat `idem_key='grn:{id}:item:{id}'`, tapi
  id-nya baru ada setelah baris dibuat → **kunci berbeda tiap percobaan**.
- `posting()` memakai `idem_key='grn:{penerimaan.id}'` — sama masalahnya.
- Penjaga sesungguhnya adalah `UniqueConstraint(purchase_order, no_surat_jalan)`
  (`warehouse/models.py:66`): retry dengan surat jalan yang sama ditolak `:97-102`.
  Jadi **idempoten pada tingkat surat jalan, bukan pada tingkat request**.

**Kompleksitas & N+1**
- O(N) untuk N baris, tapi setiap baris memicu ~8 query
  (`_simpan_item` 3, `_naikkan_stok` ~5 lewat `terima_raw`).
- `_periksa_selisih` memanggil `buat_laporan` yang melakukan `save()` +
  `filter().update()` + `CounterDokumen` = 3 query per laporan.
- `item.po_item.harga_per_kg` `:190` — `po_item` sudah di-memori dari
  `_simpan_item`, tidak ada query tambahan ✅.
- **Total untuk GRN 10 baris dengan 3 selisih: ± 100 query dalam satu transaksi**,
  semua sambil memegang lock PO.

---

## 10. Deteksi selisih otomatis

**Lokasi** `warehouse/services.py:231-269` (`_periksa_selisih`), `:272`
(`buat_laporan`), `:300` (`laporan_manual`).
**Trigger** — dipanggil di dalam `terima_barang()` `:115`; jalur manual lewat
`POST /api/v1/warehouse/laporan-selisih/`.

**Pseudocode `_periksa_selisih`**
```
hasil ← []
# (1) selisih berat — hanya untuk kiriman berkemasan
IF item.qty_deklarasi:                      # koli × isi
    beda   ← item.selisih_berat             # (diterima + ditolak) − deklarasi
    ambang ← (item.qty_deklarasi * 0.005).quantize(0.001)
    IF abs(beda) > ambang:
        hasil += buat_laporan(jenis=BERAT_KURANG, qty_selisih=beda, uraian=…)
# (2) barang ditolak karena mutu
IF item.qty_ditolak > 0:
    hasil += buat_laporan(jenis=RUSAK, qty_selisih=-item.qty_ditolak, uraian=…)
RETURN hasil
```

`buat_laporan` (`:272`)
```
harga ← item.po_item.harga_per_kg
nilai ← (abs(qty_selisih) * harga).quantize(0.01)
lap ← LaporanSelisih(...); lap.save()                    # → CounterDokumen 'BAS'
LaporanSelisih.objects.filter(pk=lap.pk).update(nilai_selisih=nilai)   # bypass editable=False
lap.nilai_selisih ← nilai                                # sinkron di memori
```

**Invariant** — setiap ketidaksesuaian fisik menghasilkan berita acara; gudang
tidak pernah mengisi nilai rupiahnya.

**Edge case**
- Jenis `KURANG_KIRIM` dan `LEBIH_KIRIM` didefinisikan (`warehouse/models.py:219-220`)
  tapi **`_periksa_selisih` tidak pernah menerbitkannya** — properti
  `selisih_po` (`models.py:184`) yang dirancang untuk itu tidak dipakai siapa pun.
  Kekurangan kiriman koli hanya tertangkap kalau kebetulan juga menyebabkan
  selisih berat.
- Pengiriman **curah** (`qty_deklarasi = 0`) melewati pemeriksaan (1) sepenuhnya —
  tidak ada kontrol berat sama sekali untuk curah.
- `selisih_berat` (`models.py:168`) mengembalikan `0` kalau `qty_deklarasi`
  falsy → cabang (1) memang tidak jalan. Konsisten.
- `qty_selisih` boleh negatif (`RUSAK` memakai `-qty_ditolak`), tapi
  `nilai_selisih` selalu `abs()` → **tanda hilang** di sisi rupiah.
- `update()` untuk menembus `editable=False` (`:295`) adalah jalur di luar
  `save()` — kalau `LaporanSelisih` nanti punya validasi save(), jalur ini
  melewatinya.

**Transaksi & locking** — `buat_laporan` dan `laporan_manual` `@transaction.atomic`;
saat dipanggil dari `terima_barang()` keduanya bergabung ke transaksi induk
(nested atomic = savepoint). Tidak ada lock.
**Idempotensi** ❌ — memanggil dua kali menerbitkan dua berita acara.
Dilindungi hanya karena `terima_barang()` sendiri tidak bisa diulang.
**Kompleksitas** O(1) per item, 3 query per laporan.

---

## 11. Penyelesaian laporan selisih

**Lokasi** `warehouse/services.py:325` (`ajukan_ke_suplier`), `:335`
(`selesaikan_laporan`), `:393` (`_buka_kembali_po`), `:403` (`tutup_laporan`).
**Trigger** — `POST …/laporan-selisih/{id}/ajukan|selesaikan|tutup/`.

**Mesin status**
```
DIBUKA ──ajukan──▶ DIAJUKAN ──┐
   │                          ├──selesaikan──▶ DISELESAIKAN
   └──selesaikan──────────────┘
   └──tutup──────────────────────────────────▶ DITUTUP
DISEPAKATI: didefinisikan (models.py:230) tapi TIDAK ADA transisi menujunya
```

**Pseudocode `selesaikan_laporan`**
```
lap ← SELECT ... FOR UPDATE
IF lap.status == DISELESAIKAN: RAISE
IF resolusi == POTONG:
    nilai_klaim ← nilai_klaim ?? lap.nilai_selisih
    IF nilai_klaim <= 0: RAISE
    IF nilai_klaim > lap.nilai_selisih: RAISE
ELSE:
    nilai_klaim ← 0
IF resolusi == RETUR: RAISE 'belum didukung'
set resolusi, nilai_klaim, catatan, status=DISELESAIKAN,
    diselesaikan_pada, diselesaikan_oleh ; SAVE(update_fields=…)
IF resolusi == SUSULAN: _buka_kembali_po(lap)
```

`_buka_kembali_po` (`:393`)
```
po ← lap.penerimaan.purchase_order
IF po.status == SELESAI AND NOT po.semua_item_lengkap():
    po.status ← SEBAGIAN ; SAVE(update_fields=['status'])
```

**Invariant**
- `0 < nilai_klaim ≤ nilai_selisih` untuk resolusi POTONG (Python `:363` +
  `CheckConstraint(nilai_klaim ≥ 0)` di DB).
- Fungsi ini **tidak memposting jurnal** — koreksi nilai baru terjadi saat
  faktur dicocokkan lewat akun `SELISIH_BELI` (docstring `:350`).

**Edge case & pelanggaran**
- ⚠ **`resolusi` tidak divalidasi sebagai choice** (`SelesaikanSelisihSerializer.resolusi`
  = `CharField(max_length=8)`, `warehouse/serializers.py:196`). Nilai seperti
  `"POTONGG"` lolos, gagal cocok dengan `Resolusi.POTONG_TAGIHAN` di `:357`,
  jatuh ke cabang `else` → **`nilai_klaim` dipaksa 0 dan laporan ditutup sebagai
  DISELESAIKAN tanpa klaim**, diam-diam.
- `_buka_kembali_po` mengambil PO **tanpa `select_for_update`** — race dengan
  `terima_barang()` yang juga mengubah `po.status`.
- `tutup_laporan` (`:403`) menyetel `resolusi = TERIMA_APA_ADANYA` tanpa
  memeriksa apakah sudah `DITUTUP` sebelumnya → bisa dipanggil berulang,
  menimpa `diselesaikan_pada`/`_oleh`.
- Status `DISEPAKATI` mati.

**Transaksi & locking** `@transaction.atomic` + `select_for_update` pada laporan ✅,
tapi **tidak** pada PO.
**Idempotensi** ⚠ — `selesaikan` menolak pengulangan, `tutup` tidak.
**Kompleksitas** O(1); `_buka_kembali_po` menambah 1 query `EXISTS`.

---

## 12. Terbitkan faktur + pembersihan GRNI

**Lokasi** `akunting/services.py:531-640`; pembantu `hitung_nilai_penerimaan`
`:476`, `draft_faktur` `:490`, `warehouse.total_potongan` `warehouse/services.py:442`.
**Trigger** `POST /api/v1/akunting/faktur/dari-penerimaan/{penerimaan_id}/`.

**Pseudocode**
```
p ← PenerimaanBarang SELECT ... FOR UPDATE (select_related PO→suplier, PO→entitas)
IF p.faktur.exists(): RAISE 'sudah difaktur'
terbuka ← p.laporan_selisih.exclude(status IN [DISELESAIKAN, DITUTUP]).nomor
IF terbuka AND NOT abaikan_klaim_terbuka: RAISE
pastikan_periode_terbuka(po.entitas_id, tanggal_faktur)
IF EXISTS(FakturPembelian WHERE suplier AND nomor_faktur): RAISE
total_tagihan ← Decimal(total_tagihan).quantize(0.01)
IF total_tagihan <= 0: RAISE

# DIHITUNG ULANG DI BAWAH LOCK — payload tidak dipercaya
nilai_terima ← Σ(item.qty_diterima × item.po_item.harga_per_kg)   # hitung_nilai_penerimaan
potongan    ← Σ(LaporanSelisih.nilai_klaim WHERE resolusi=POTONG AND status=DISELESAIKAN)
nilai_wajar ← nilai_terima − potongan

termin ← termin_hari ?? suplier.termin_hari_default
faktur ← INSERT FakturPembelian(...)     # save(): no_internal + jatuh_tempo + sisa=total
INSERT KartuHutang(jenis=FAKTUR, kredit=total_tagihan, referensi=no_internal)
posting('FAKTUR_MASUK', nilai={'nilai_faktur': total_tagihan},
        idem_key=f'faktur:{faktur.id}')                    # Dr GRNI / Cr Hutang

selisih ← total_tagihan − nilai_wajar
IF selisih != 0:
    posting('FAKTUR_LEBIH' IF selisih > 0 ELSE 'FAKTUR_KURANG',
            nilai={'selisih': abs(selisih)},
            idem_key=f'faktur:{faktur.id}:selisih')
RETURN faktur, rincian
```

Aturan jurnal terkait (`posting_rules.py:40-53`):
```
FAKTUR_MASUK   : Dr 2190 GRNI          / Cr 2100 Hutang Usaha
FAKTUR_LEBIH   : Dr 5900 Selisih Beli  / Cr 2190 GRNI      (faktur > penerimaan)
FAKTUR_KURANG  : Dr 2190 GRNI          / Cr 5900 Selisih Beli
```

**Invariant**
1. Satu penerimaan = satu faktur (`p.faktur.exists()` `:555`).
2. Nomor faktur unik per suplier (Python `:576` + `uq_faktur_suplier_nomor`).
3. Saldo GRNI kembali nol untuk penerimaan itu: `AUDIT_GUDANG` mengkredit GRNI
   sebesar `nilai_terima`, `FAKTUR_MASUK` mendebet `total_tagihan`, dan
   `FAKTUR_LEBIH/KURANG` menutup selisihnya terhadap `nilai_wajar`.
   ⚠ **Ini hanya benar bila `potongan = 0`.** Kalau ada potongan klaim,
   GRNI dari penerimaan = `nilai_terima`, sedangkan yang dibersihkan =
   `total_tagihan + (nilai_wajar − total_tagihan)` = `nilai_wajar` =
   `nilai_terima − potongan`. **Sisa `potongan` menggantung di GRNI selamanya** —
   tidak ada jurnal yang membebankan potongan klaim ke akun mana pun.
4. `sisa_hutang = total_tagihan` saat penerbitan (`hutang.py:168`).

**Edge case**
- `abaikan_klaim_terbuka` hanya boleh Supervisor — dicek **di view**
  (`akunting/views.py:283`), bukan di service. Pemanggilan service langsung
  dari shell melewati pemeriksaan itu.
- `p.faktur.exists()` di-cek sebelum insert, tapi tidak ada `UniqueConstraint`
  pada `FakturPembelian.penerimaan` → dua request paralel bisa lolos kalau
  `select_for_update` pada `PenerimaanBarang` tidak menahannya. Faktanya
  **menahan** (`:551`), jadi aman.
- `hitung_nilai_penerimaan` (`:476`) melakukan
  `penerimaan.item.select_related('po_item')` lalu loop → **1 query, tanpa N+1** ✅.
- `dokumen_id` tidak divalidasi → `IntegrityError` 500.
- `total_tagihan` dari klien tidak dibatasi terhadap `nilai_wajar` — faktur
  boleh berapa pun; selisihnya masuk beban. Sengaja, tapi tanpa batas atas.

**Transaksi & locking** `@transaction.atomic` + `select_for_update` pada
`PenerimaanBarang` ✅. Counter FAKTUR dan JURNAL ikut terkunci.
**Idempotensi** ⚠ — `posting()` idempoten lewat `faktur:{id}`, tapi `id` baru
lahir di dalam transaksi, jadi retry menghasilkan faktur baru; yang menahan
adalah `uq_faktur_suplier_nomor` (retry dengan nomor faktur sama → 400).
**Kompleksitas** ~12 query. Tidak ada N+1.

---

## 13. Alokasi pembayaran FIFO

**Lokasi** `akunting/services.py:186-239` (`alokasi_pembayaran`), `:152`
(`post_pembayaran`).
**Trigger** `POST /api/v1/akunting/pembayaran/` (`akunting/views.py:328`,
`modul='keuangan'`).

**Pseudocode**
```
sisa ← Decimal(nominal).quantize(0.01)
IF sisa <= 0: RAISE
faktur_terbuka ← FakturPembelian SELECT ... FOR UPDATE
                 WHERE suplier AND entitas AND status IN (BELUM_BAYAR, SEBAGIAN)
                 ORDER BY tanggal_jatuh_tempo, id          # DETERMINISTIK
alokasi ← []
FOR f IN faktur_terbuka:
    IF sisa <= 0: BREAK
    porsi ← min(sisa, f.sisa_hutang)
    post_pembayaran(faktur_id=f.id, nominal=porsi, idem_key=f'{idem_key}:f{f.id}')
    alokasi.append({faktur, porsi}) ; sisa -= porsi
IF sisa > 0:
    uang_muka ← INSERT UangMukaSuplier(nominal=sisa, sisa=sisa)
posting('BAYAR_HUTANG', nilai={'nominal': nominal_penuh},
        idem_key=f'{idem_key}:jurnal')                     # Dr Hutang / Cr Kas
RETURN alokasi, uang_muka
```

`post_pembayaran` (`:152`)
```
ada ← KartuHutang WHERE referensi = idem_key ; IF ada: RETURN ada
faktur ← SELECT ... FOR UPDATE
IF nominal <= 0: RAISE
IF nominal > faktur.sisa_hutang: RAISE
INSERT KartuHutang(jenis=BAYAR, debit=nominal, referensi=idem_key)
faktur.total_dibayar += nominal ; faktur.sisa_hutang -= nominal
faktur.status ← LUNAS IF sisa == 0 ELSE SEBAGIAN
SAVE(update_fields=['total_dibayar','sisa_hutang','status'])
```

**Invariant**
1. `sisa_hutang` tidak pernah negatif — dijaga Python `:169` **dan**
   `CheckConstraint ck_faktur_sisa_nonneg`.
2. `total_dibayar ≤ total_tagihan` — `ck_faktur_dibayar_dalam_batas`.
3. `SUM(KartuHutang.debit) = FakturPembelian.total_dibayar` — **tidak dijaga DB**,
   hanya oleh urutan operasi di `post_pembayaran`.
4. Jurnal `BAYAR_HUTANG` diposting sebesar **nominal penuh**, termasuk bagian
   yang jadi uang muka. ⚠ Artinya `Dr 2100 Hutang Usaha` didebet lebih besar
   dari hutang yang benar-benar berkurang — **kelebihan bayar salah akun**;
   seharusnya masuk akun uang muka/piutang, bukan mengurangi hutang usaha.

**Edge case**
- `order_by('tanggal_jatuh_tempo', 'id')` **wajib deterministik** supaya dua
  transaksi tidak mengunci himpunan beririsan dengan urutan berbeda
  (docstring `:194-198`) ✅ — ini benar dan penting.
- `idem_key` diturunkan per faktur (`:221`) agar satu pembayaran yang pecah ke
  3 faktur tidak bentrok ✅.
- ⚠ **`KartuHutang.referensi` tidak `unique`** (`hutang.py:203`) — cek
  idempotensi di `:160` hanya `SELECT`, tidak punya penjaga DB. Dua request
  paralel dengan `idem_key` sama bisa lolos berdua.
- ⚠ **View menghasilkan `idem_key = f'bayar:{uuid4()}'` baru setiap request**
  (`akunting/views.py:348`) → seluruh mekanisme idempotensi **mati untuk jalur
  API**. Klik ganda / retry = pembayaran dobel.
- `f.sisa_hutang` dibaca dari instance hasil `select_for_update` di loop luar,
  lalu `post_pembayaran` melakukan `select_for_update` lagi pada baris yang sama
  → lock sudah dipegang, tidak deadlock, tapi 1 query redundan per faktur.
- Kalau tidak ada faktur terbuka sama sekali, seluruh nominal jadi uang muka
  dan jurnal tetap `Dr Hutang / Cr Kas` — mendebet hutang yang tidak ada.
- **Tidak ada `MutasiKas`** — pembayaran ke suplier tidak menyentuh
  `keuangan_mutasi_kas` maupun `RekeningBank.saldo` sama sekali. Kas berkurang
  di buku besar tapi tidak di buku bank.

**Transaksi & locking** `@transaction.atomic` + `select_for_update` pada seluruh
faktur terbuka sekaligus, urutan deterministik ✅.
**Idempotensi** ❌ untuk jalur API (kunci acak). Secara service, ✅ kalau
pemanggil memberi `idem_key` stabil.
**Kompleksitas** O(N faktur terbuka); ~4 query per faktur + 7 untuk posting.
`select_for_update` atas seluruh faktur terbuka suplier itu **menahan semua
faktur** selama transaksi berlangsung.

---

## 14. Aging hutang

**Lokasi** `akunting/services.py:643-674`.
**Trigger** `GET /api/v1/akunting/faktur/aging/`.

**Pseudocode**
```
per ← per ?? localdate()
rentang(a,b) ≡ Q(tanggal_jatuh_tempo__range=(per − b hari, per − a hari))
FakturPembelian
  .filter(entitas, status IN (BELUM_BAYAR, SEBAGIAN))
  .values('suplier_id', 'suplier__nama')
  .annotate(belum_tempo = Sum(sisa_hutang, filter=tanggal_jatuh_tempo > per),
            umur_1_30   = Sum(sisa_hutang, filter=rentang(0,30)),
            umur_31_60  = Sum(sisa_hutang, filter=rentang(31,60)),
            umur_60plus = Sum(sisa_hutang, filter=tanggal_jatuh_tempo < per−60),
            total       = Sum(sisa_hutang))
  .order_by('-total')
```

**Invariant** — satu query agregat, bukan loop per suplier (docstring `:645`) ✅.

**Edge case**
- **Ember tumpang tindih dan bolong.** `umur_1_30` = `[per−30, per−0]`,
  `umur_31_60` = `[per−60, per−31]`, `umur_60plus` = `< per−60`.
  Faktur jatuh tempo **tepat** `per − 60` masuk `umur_31_60`, dan yang
  `< per − 60` masuk `umur_60plus` — tidak ada celah di sini. Tapi
  `belum_tempo` = `> per` sementara `umur_1_30` mencakup `= per` → konsisten.
  Nama ember `umur_1_30` menyesatkan: rentangnya sebenarnya 0–30 hari.
- `entitas_id` datang dari query param tanpa validasi tipe → string non-numerik
  menyebabkan `ValueError` 500.
- Kolom hasil bisa `None` (bukan 0) kalau tidak ada faktur di ember itu —
  frontend harus menangani null.

**Transaksi & locking** — tidak ada (read-only).
**Idempotensi** ✅ murni.
**Kompleksitas** **1 query**, memakai `ix_faktur_ent_status`. Tidak ada N+1 ✅.

---

## 15. Mesin stok tiga lapis & kepemilikan proporsional (SZA)

**Lokasi** `inventory/services.py` — helper `_stok` `:54`, `_catat` `:63`,
`_geser_tangki` `:83`, `_geser_pemilik` `:115`, `_catat_klaim` `:133`;
operasi `terima_raw` `:169`, `setor_ke_pool` `:204`, `pakai_dari_pool` `:263`,
`hasil_ke_pool` `:284`, `klaim_hasil` `:309`, `lunasi_posisi` `:364`,
`sesuaikan_stok` `:401`.

**Model mental**
```
RAW  (pemilik melekat: SaldoEntitas)
  │ setor_ke_pool: fisik lepas, hak jadi KLAIM (+)
  ▼
POOL (TANPA pemilik; hak ada di MutasiKlaim/PosisiKlaim)
  │ pakai_dari_pool (−)      ← produksi
  │ hasil_ke_pool   (+)      ← produksi
  │ klaim_hasil: hak berkurang (−), fisik dapat pemilik lagi
  ▼
JADI (pemilik melekat: SaldoEntitas)
```

### 15a. Helper `_catat()` — rantai saldo berjalan (`:63-80`)
```
saldo_baru ← stok.qty + masuk − keluar
IF saldo_baru < 0: RAISE 'stok tidak cukup'
stok.urutan_terakhir += 1
INSERT MutasiStok(urutan=stok.urutan_terakhir, saldo_akhir=saldo_baru,
                  idempotency_key=idem_key)
stok.qty ← saldo_baru ; SAVE(update_fields=['qty','urutan_terakhir'])
```
**Invariant (3)**: `saldo_akhir[n] = saldo_akhir[n−1] + masuk − keluar`.
Dijaga oleh `uq_mutasi_stok_urutan` + `ck_stok_nonneg` + urutan operasi.
Prasyarat: `stok` harus sudah di-lock (`_stok()` memakai
`select_for_update().get_or_create()` `:56`).

### 15b. Helper `_geser_pemilik()` (`:115-130`)
```
IF stok.lapis == POOL: RAISE 'POOL tidak boleh punya pemilik'
saldo ← SaldoEntitas SELECT ... FOR UPDATE get_or_create(stok, entitas)
IF saldo.qty + d_qty < 0: RAISE
saldo.qty += d_qty ; saldo.nilai += d_nilai ; SAVE
```
⚠ `d_nilai` **tidak dibatasi** — `saldo.nilai` boleh jadi negatif; tidak ada
`CheckConstraint(nilai ≥ 0)` di `inventory/models.py:216-221`.

### 15c. Helper `_catat_klaim()` — inti perhitungan SZA (`:133-162`)
```
tarif ← NilaiEkuivalen.tarif(produk_id, tanggal)      # RAISE kalau belum ada
nilai ← (qty × tarif).quantize(0.01, ROUND_HALF_UP) × arah    # arah = +1 | −1
INSERT MutasiKlaim(qty, tarif, nilai, idempotency_key)        # tarif DISIMPAN
posisi ← PosisiKlaim SELECT ... FOR UPDATE get_or_create(entitas, grup)
IF arah > 0: posisi.total_setor += abs(nilai)
ELSE:        posisi.total_ambil += abs(nilai)
posisi.nilai_bersih += nilai
SAVE(update_fields=['total_setor','total_ambil','nilai_bersih'])
```
Tarif yang dipakai **disimpan di baris** → perubahan tarif berlaku prospektif,
sejarah tidak ditulis ulang. Ini yang membuat posisi multi-produk runtuh jadi
satu angka rupiah-ekuivalen per entitas.

### 15d. `setor_ke_pool()` (`:204-256`) — RAW → POOL, hak bertambah
```
IF MutasiStok WHERE key = f'{idem_key}:out' EXISTS: RETURN (ada, None,None,None)
qty ← Decimal(qty).quantize(0.001) ; IF qty <= 0: RAISE
pastikan_periode_terbuka(entitas_id, tanggal)

raw   ← _stok(produk, grup, RAW, tangki_raw)           # FOR UPDATE
saldo ← SaldoEntitas.get(stok=raw, entitas) FOR UPDATE  # .get() → DoesNotExist bila belum ada
IF qty > saldo.qty: RAISE

# NILAI PEROLEHAN KELUAR PROPORSIONAL — rata-rata tertimbang
harga        ← saldo.nilai / saldo.qty   (0 bila qty = 0)
nilai_keluar ← (qty × harga).quantize(0.01, ROUND_HALF_UP)
nilai_keluar ← min(nilai_keluar, saldo.nilai)          # penjaga pembulatan

_geser_tangki(tangki_raw, −qty)
m_out ← _catat(raw,  SETOR, 0, qty, key=f'{idem_key}:out')
_geser_pemilik(raw, entitas, −qty, −nilai_keluar)

pool  ← _stok(produk, grup, POOL, tangki_pool)
_geser_tangki(tangki_pool, +qty, produk)
m_in  ← _catat(pool, SETOR, qty, 0, key=f'{idem_key}:in')

baris, posisi ← _catat_klaim(entitas, grup, SETOR, produk, qty,
                             key=f'{idem_key}:klaim', arah=+1)
```

### 15e. `klaim_hasil()` (`:309-357`) — POOL → JADI, hak berkurang
```
IF MutasiStok WHERE key = f'{idem_key}:out' EXISTS: RETURN awal
qty > 0, periode terbuka
pool ← _stok(produk, grup, POOL, tangki_pool)  ; IF qty > pool.qty: RAISE
_geser_tangki(tangki_pool, −qty)
m_out ← _catat(pool, KLAIM, 0, qty, key=':out')
jadi  ← _stok(produk, grup, JADI, None)                 # selalu rak, bukan tangki
m_in  ← _catat(jadi, KLAIM, qty, 0, key=':in')
IF nilai_perolehan IS NULL:
    nilai_perolehan ← (qty × NilaiEkuivalen.tarif(produk, tanggal)).quantize(0.01)
_geser_pemilik(jadi, entitas, +qty, nilai_perolehan)
baris, posisi ← _catat_klaim(..., arah=−1)
```

### 15f. `sesuaikan_stok()` (opname, `:401-444`)
```
IF sudah ada mutasi dengan key: RETURN
qty_fisik ≥ 0
stok ← _stok(...)  ; delta ← qty_fisik − stok.qty
IF delta == 0: RAISE 'tidak ada selisih'
IF entitas_id: pastikan_periode_terbuka(...)            # HANYA kalau entitas diisi
_geser_tangki(tangki, delta, produk jika delta > 0)
mutasi ← _catat(stok, OPNAME, delta jika naik, −delta jika turun, key)
IF stok.berpemilik AND entitas_id:
    _geser_pemilik(stok, entitas, delta, Decimal(nilai_penyesuaian ?? 0))
```

**Invariant sistem (didokumentasikan `inventory/services.py:16-23`)**
1. `SUM(SaldoEntitas.qty) = Stok.qty` untuk RAW & JADI
2. `SUM(PosisiKlaim.nilai_bersih) = nilai ekuivalen sisa POOL` per grup
3. `saldo_akhir[n] = saldo_akhir[n−1] + masuk − keluar`

**Edge case & titik rapuh**

| # | Masalah | Lokasi |
|---|---|---|
| 1 | **Invariant (2) rusak by design saat produksi.** `pakai_dari_pool` mengurangi POOL dan `hasil_ke_pool` menambahnya, keduanya **tanpa menyentuh `MutasiKlaim`**. Nilai ekuivalen bahan yang dipakai ≠ nilai ekuivalen produk jadi yang dihasilkan → `SUM(PosisiKlaim)` langsung melenceng dari nilai POOL setiap kali sesi selesai. Tidak ada rekonsiliasi yang menutup selisih ini. | `inventory/services.py:263-302` |
| 2 | **`pakai_dari_pool`/`hasil_ke_pool` tidak memeriksa periode akuntansi** | `:263-302` |
| 3 | `setor_ke_pool` memakai `SaldoEntitas.objects.get()` `:229` — kalau entitas belum punya saldo untuk stok itu, `DoesNotExist` **bukan** `ValidationError` → **500**, bukan 400 | `:229-231` |
| 4 | Pembagian `saldo.nilai / saldo.qty` `:236` — dijaga `if saldo.qty else 0`, tapi `qty > 0` sudah dipastikan `:232` ✅ | `:236` |
| 5 | `min(nilai_keluar, saldo.nilai)` `:238` mencegah nilai negatif akibat pembulatan, tapi **menciptakan residu**: setelah qty habis, `saldo.nilai` bisa tersisa beberapa sen dengan `qty = 0` | `:238` |
| 6 | `klaim_hasil` default `nilai_perolehan` dari **nilai ekuivalen** — docstring sendiri menyebut itu "hanya layak sebagai perkiraan, bukan angka akuntansi" `:321`, tapi tetap dipakai sebagai harga pokok `SaldoEntitas.nilai` di lapis JADI | `:348-351` |
| 7 | `sesuaikan_stok` menerima `nilai_penyesuaian` bebas dari payload **tanpa batas** — Supervisor bisa merevaluasi persediaan tanpa jurnal apa pun | `:441` |
| 8 | **Opname tidak memposting jurnal.** Stok berubah, buku besar tidak. `Persediaan` di neraca langsung menyimpang dari `Stok.qty × harga` | seluruh `:401-444` |
| 9 | `_geser_tangki` `:83` — `Tangki.objects.select_for_update().get()` tanpa guard → id palsu = 500 | `:90` |
| 10 | `_stok()` memakai `get_or_create(...)` dengan `select_for_update()`. Untuk baris yang **belum ada**, `SELECT FOR UPDATE` tidak mengunci apa pun → dua transaksi bisa sama-sama INSERT; `uq_stok_rak`/`uq_stok_tangki` menangkapnya sebagai `IntegrityError` (500) | `:54-60` |
| 11 | Pemeriksaan idempotensi `setor_ke_pool`/`klaim_hasil` `RETURN (ada, None, None, None)` — **mengembalikan tuple dengan 3 elemen None**, sehingga view merender `klaim: null, posisi: null` untuk retry yang "berhasil" | `:217-219`, `:324-326` |
| 12 | `lunasi_posisi()` `:364` — jalur penyelesaian tunai antar entitas — **tidak dipanggil siapa pun** dan tidak punya endpoint | `:364-394` |
| 13 | `verifikasi_rantai_saldo()` `:559` memakai **raw SQL** dengan nama tabel hardcode `inventory_mutasi_stok`, dan **tidak dipanggil siapa pun** | `:559-577` |

**Transaksi & locking** — setiap operasi publik `@transaction.atomic`.
Lock: `Stok` (FOR UPDATE via `_stok`), `SaldoEntitas` (FOR UPDATE),
`Tangki` (FOR UPDATE), `PosisiKlaim` (FOR UPDATE).
⚠ **Urutan pengambilan lock tidak konsisten** antar fungsi:
`setor_ke_pool` mengunci RAW-stok → tangki-raw → saldo → POOL-stok → tangki-pool → posisi;
`klaim_hasil` mengunci POOL-stok → tangki-pool → JADI-stok → saldo → posisi.
Dua transaksi yang menyentuh himpunan tangki/stok beririsan dari arah berbeda
bisa deadlock.

**Idempotensi** ✅ **penuh** untuk semua operasi tulis: setiap fungsi memeriksa
`MutasiStok.idempotency_key` (atau `MutasiKlaim` untuk `lunasi_posisi`) di awal,
dan kolomnya `UNIQUE` di DB — jadi bahkan race pun ditangkap.
Suffix `:out`/`:in`/`:klaim` memisahkan sub-operasi dalam satu kunci induk.

**Kompleksitas**
- `setor_ke_pool`: ~14 query. `klaim_hasil`: ~13. `terima_raw`: ~8.
- `isi_pool()` `:471` — loop atas stok POOL, memanggil `NilaiEkuivalen.tarif()`
  **per produk** → **N+1** (1 query per produk di pool).
- `verifikasi_kepemilikan()` `:499` — **N+1 berat**: 1 query agregat
  `SaldoEntitas` **per baris Stok**. Untuk 500 baris stok = 501 query.
- `verifikasi_posisi_cache()` `:540` — **N+1**: 1 agregat `MutasiKlaim` per
  baris `PosisiKlaim`.
- `verifikasi_pool_bersih()` `:522` memanggil `isi_pool()` → mewarisi N+1-nya.
- `GET /api/v1/inventory/verifikasi/` menjalankan **ketiganya sekaligus**
  (`inventory/views.py:244-251`), tanpa paginasi dan tanpa batas waktu.

---

## 16. Kapasitas produksi & siklus sesi

**Lokasi** `produksi/services.py:36` (`hitung_kapasitas`), `:99` (`buat_sesi`),
`:131` (`mulai_sesi`), `:165` (`selesaikan_sesi`), `:207` (`batalkan_sesi`),
`:230` (`ringkasan_sesi`). Resep: `produksi/models.py:74` (`berlaku`), `:87`
(`kebutuhan`).

### 16a. `hitung_kapasitas()` — bahan pembatas
```
resep ← Resep.berlaku(produk_jadi, tanggal)      # aktif, berlaku_sejak ≤ tgl, versi tertinggi
item  ← list(resep.item.select_related('bahan'))
IF item kosong: RAISE
tersedia ← {produk_id: qty}  FROM Stok WHERE grup AND lapis=POOL AND produk IN bahan
FOR i IN item:
    ada      ← tersedia.get(i.bahan_id, 0)
    per_unit ← i.qty / resep.hasil_per_batch
    cukup    ← (ada / per_unit).quantize(0.001, ROUND_DOWN)  bila per_unit else 0
maksimum ← min(cukup)                            # BAHAN PEMBATAS
pembatas ← semua bahan yang cukup_untuk == maksimum
sisa     ← {bahan: tersedia − maksimum × per_unit}
```
**Nilai ekuivalen sengaja TIDAK dipakai di sini** (docstring `:6-10`) — klaim
senilai Rp 50.000 tidak bisa jadi teh kemasan kalau teh celupnya habis. Ini
pemisahan yang benar antara kelayakan fisik dan penyelesaian nilai.

**Edge case**: `ROUND_DOWN` benar (tidak boleh membulatkan ke atas).
`per_unit` bisa 0 hanya kalau `i.qty` 0 — dicegah `ck_resep_item_qty`.
`min()` atas list kosong dijaga `if kapasitas else 0` `:77`.
**Kompleksitas** 2 query (resep item + stok), **tanpa N+1** ✅.

### 16b. Siklus sesi
```
buat_sesi:      DRAFT      — validasi qty_target ≤ kapasitas; buat SesiInput
                             (qty_rencana = qty_aktual = kebutuhan resep).
                             BELUM menyentuh stok.
mulai_sesi:     → BERJALAN — FOR EACH input: timpa qty_aktual bila dikirim,
                             lalu pakai_dari_pool(). Stok POOL benar-benar turun.
selesaikan_sesi:→ SELESAI  — hasil_ke_pool(qty_hasil). qty_hasil ≤ qty_target.
batalkan_sesi:  → BATAL    — HANYA dari DRAFT.
```

**Invariant**
- Satu sesi tidak melintasi grup bahan (`grup_bahan` di header sesi).
- Sesi BERJALAN tidak bisa dibatalkan — bahan sudah keluar dari pool; koreksi
  hanya lewat opname (`:216-219`).
- Susut = `qty_target − qty_hasil`, dicatat apa adanya.

**Edge case**
- ⚠ `selesaikan_sesi` menolak `qty_hasil > qty_target` `:185`. Untuk produksi
  yang **melebihi** target (rendemen > 100%, mungkin pada pencampuran) tidak ada
  jalan keluar selain opname.
- ⚠ `mulai_sesi` mengambil bahan sesuai `qty_aktual` **tanpa memvalidasi ulang
  terhadap kapasitas**. `qty_aktual` bebas dari payload; satu-satunya penjaga
  adalah `_catat()` yang menolak saldo negatif `inventory/services.py:66`.
- ⚠ `qty_aktual` dikirim sebagai dict `{bahan_id: qty}`; bahan yang **tidak ada
  di sesi** diabaikan diam-diam (`:146` hanya menimpa yang cocok), dan bahan
  yang tidak dikirim tetap memakai `qty_rencana`.
- **Nilai bahan yang dipakai hilang dari pembukuan**: `pakai_dari_pool` tidak
  menulis `MutasiKlaim` dan tidak memposting jurnal. Docstring `:169-172`
  menyebut "invariant DEM" (nilai bahan diserap hasil), tapi **tidak ada satu
  baris kode pun yang memindahkan nilai itu** — POOL memang tidak menyimpan nilai.
- `SesiProduksi.save()` memilih entitas pemegang counter dengan
  `grup_bahan.entitas.order_by('kode').first()` `produksi/models.py:201` — untuk
  grup BERSAMA itu `AGUS` (kode terkecil secara alfabet), bukan CV. Nomor sesi
  jadi `SESI/AGUS/2026/VIII/001`.
- `batalkan_sesi` tidak memeriksa apakah sesi sudah BATAL → bisa menambah
  catatan `[BATAL]` berulang. (Cek `!= DRAFT` `:215` sudah menutupnya karena
  BATAL bukan DRAFT ✅.)

**Transaksi & locking** — keempat operasi `@transaction.atomic`.
`select_for_update` pada `SesiProduksi` dan (di `mulai_sesi`) pada `SesiInput` ✅.
⚠ Tapi lihat FASE 1 §C: `SesiInput.objects.filter(...).update(tangki_id=…)`
di `produksi/views.py:70` berjalan **di luar** transaksi mana pun.

**Idempotensi** — `mulai_sesi`/`selesaikan_sesi` dijaga dua lapis: cek status
(`:141`, `:177`) **dan** `idem_key` stabil (`f'sesi:{id}:pakai:{bahan}'`,
`f'sesi:{id}:hasil'`) yang unik di DB ✅. Ini contoh idempotensi yang benar —
berbeda dari `alokasi_pembayaran` yang memakai uuid acak.

**Kompleksitas** — `mulai_sesi`: O(N bahan) × ~6 query dari `pakai_dari_pool`.
`ringkasan_sesi` memakai `prefetch_related('input__bahan')` ✅.

---

## 17. Pengeluaran kas kecil

**Lokasi** `keuangan/services.py:9-63`.
**Trigger** `POST /api/v1/keuangan/pengeluaran/` (`keuangan/views.py:21`).

**Pseudocode**
```
pengeluaran ← INSERT PengeluaranKas(entitas, kategori, keterangan,
                                    pemohon, nominal, bukti_nota)
rekening ← RekeningBank SELECT ... FOR UPDATE
           WHERE entitas AND jenis='KAS_KECIL'  →  .first()
IF NOT rekening: RAISE 'belum dikonfigurasi'
IF rekening.saldo < nominal: RAISE 'saldo tidak cukup'
rekening.urutan_terakhir += 1
rekening.saldo -= nominal
SAVE rekening(update_fields=['urutan_terakhir','saldo'])
referensi ← f"PC-{yymmdd}-{pengeluaran.id}"
mutasi ← INSERT MutasiKas(urutan, kredit=nominal, saldo_akhir=rekening.saldo,
                          idempotency_key=f"pc-{pengeluaran.id}-{uuid4()}")
pengeluaran.mutasi ← mutasi ; SAVE
posting('BEBAN_KAS', nilai={'nominal': nominal},
        idem_key=mutasi.idempotency_key)          # Dr 6100 Beban Umum / Cr 1100 Kas
RETURN pengeluaran
```

**Invariant yang DIHARAPKAN**
- `RekeningBank.saldo = SUM(MutasiKas.kredit) − SUM(MutasiKas.debit)` — **tidak
  dijaga apa pun**; tidak ada verifikator seperti di inventory.
- Setiap pengeluaran punya satu `MutasiKas` dan satu jurnal.

**Edge case & pelanggaran**

| # | Masalah | Lokasi |
|---|---|---|
| 1 | **`nominal` tidak pernah dikonversi ke `Decimal`.** Datang mentah dari `request.data` (`keuangan/views.py:30`). Multipart form → `str` → `rekening.saldo < nominal` melempar `TypeError: '<' not supported between 'Decimal' and 'str'`. JSON float → `rekening.saldo -= nominal` melempar `TypeError` (Decimal − float tidak didukung). Hanya JSON **int** yang bekerja. | `keuangan/services.py:29,34` |
| 2 | **`idempotency_key` mengandung `uuid4()`** → tidak pernah cocok dengan baris lama. Retry/klik-ganda = pengeluaran kedua, mutasi kedua, jurnal kedua. Padahal kolomnya `UNIQUE` — mekanismenya ada, kuncinya yang dibuang. | `:46` |
| 3 | Baris `PengeluaranKas` dibuat **sebelum** saldo diperiksa `:12` vs `:29`. Kalau saldo kurang, rollback membatalkannya — tapi `pengeluaran.id` yang sudah terpakai di sequence hilang, dan file `bukti_nota` **sudah tertulis ke storage** oleh `FileField` → **berkas yatim**. | `:12-19` |
| 4 | **Konvensi debit/kredit terbalik.** Uang keluar dicatat di kolom `kredit` `:42` sambil **mengurangi** saldo, sementara `MutasiKas.__str__` (`keuangan/models.py:108`) merender `kredit` dengan tanda `+`. Tidak ada penulis lain di tabel ini untuk dibandingkan. | `:42` |
| 5 | `.filter(...).first()` untuk rekening KAS_KECIL — **tidak ada unique constraint** `(entitas, jenis)`, jadi dua rekening kas kecil untuk satu entitas akan dipilih secara acak (urutan default `ordering=['entitas__kode','nama_bank']`). | `:22-24` |
| 6 | **`import posting` di kepala file** `:7`, padahal docstring `keuangan/models.py:7-9` menyatakan impor ke akunting harus di dalam fungsi. Ini satu-satunya impor lintas-app tingkat modul di lapis 4 (lihat FASE 4). | `keuangan/services.py:7` |
| 7 | `PengeluaranKas` tidak punya `dibuat_oleh` — parameter `user` hanya diteruskan ke `posting()`. Siapa yang mengeluarkan uang **tidak tercatat di baris pengeluaran**. | `keuangan/models.py:181` |
| 8 | `tanggal` jurnal dipaksa `timezone.localdate()` `:55`, bukan tanggal transaksi — pengeluaran yang diinput mundur akan diposting ke hari ini. | `:55` |
| 9 | Tidak ada `pastikan_periode_terbuka` eksplisit — tapi `posting()` melakukannya `:55`, dan karena tanggalnya selalu hari ini, periode berjalan pasti terbuka. Efektifnya pemeriksaan periode **tidak berfungsi** untuk jalur ini. | — |
| 10 | View menangkap `except Exception` telanjang `keuangan/views.py:35` → `TypeError`, `DoesNotExist`, `IntegrityError` semua jadi HTTP 400 dengan pesan Python mentah. | `keuangan/views.py:35-37` |

**Transaksi & locking** `@transaction.atomic` + `select_for_update` pada
`RekeningBank` ✅ — pemotongan saldo terserialkan per rekening.
**Idempotensi** ❌ (lihat #2).
**Kompleksitas** ~12 query (termasuk 7 dari `posting`). Tidak ada N+1.

---

# RINGKASAN MASALAH LINTAS-ALGORITMA

**Idempotensi** — infrastrukturnya lengkap (kolom `idempotency_key` UNIQUE di
`MutasiStok`, `MutasiKlaim`, `MutasiKas`, `JurnalUmum`), tapi **dua jalur
membuang kuncinya dengan `uuid4()` per request**: `PembayaranView`
(`akunting/views.py:348`) dan `catat_pengeluaran` (`keuangan/services.py:46`).
Keduanya adalah jalur uang. Bandingkan dengan `produksi.mulai_sesi` yang
memakai kunci deterministik `f'sesi:{id}:pakai:{bahan}'` — pola yang benar.

**Locking** — `select_for_update` dipakai konsisten di 14 fungsi, tapi
**urutan** pengambilannya tidak diseragamkan antar fungsi
(`setor_ke_pool` vs `klaim_hasil` vs `terima_barang`), sehingga deadlock
Postgres mungkin terjadi pada beban paralel di grup bahan yang sama.

**Invariant yang tidak dijaga apa pun**
1. `SUM(PosisiKlaim) = nilai POOL` — rusak setiap kali sesi produksi selesai (§15 #1)
2. GRNI kembali nol — bocor sebesar potongan klaim (§12 invariant 3)
3. `RekeningBank.saldo = SUM(MutasiKas)` — tidak ada verifikator (§17)
4. Stok vs nilai persediaan di buku besar — opname tidak menjurnal (§15 #8)

**Periode akuntansi** tidak diperiksa di jalur produksi
(`pakai_dari_pool`/`hasil_ke_pool`) dan efektif tidak berlaku untuk kas kecil.

**N+1 terparah**: `GET /api/v1/inventory/verifikasi/` — tiga fungsi verifikasi
sekaligus, masing-masing satu query per baris (§15).
