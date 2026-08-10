# FASE 2 — PETA DATA

**44 model konkret terdaftar** di app registry Django (diverifikasi lewat
`apps.get_app_config(...).get_models()`), + 2 abstract base, + 1 model di app
`audit` yang **tidak terdaftar** karena app-nya tidak di `INSTALLED_APPS`.
Migrasi dibaca **hanya** untuk merekonstruksi constraint / index / trigger DB.

Jumlah per app: core 4 · staff_user 4 · master 5 · dokumen 1 · inventory 7 ·
akunting 9 · keuangan 4 · warehouse 4 · produksi 4 · work_order 2 ·
pajak/sales_order/logistik 0.
Di luar itu ada 2 tabel M2M implisit (`master_produk_suplier` dari
`master/models.py:108`, `staff_user_profil_entitas_diizinkan` dari
`staff_user/models.py:137`) plus tabel bawaan Django (auth, contenttypes,
sessions, admin, authtoken).

Verifikasi sinkronisasi model↔migrasi:
```
python manage.py makemigrations --check --dry-run  →  "No changes detected" (exit 0)
```
Artinya seluruh constraint & index yang tertulis di `Meta` di bawah ini
benar-benar ada di skema database (termasuk 3 migrasi yang belum di-commit).

Presisi decimal terpusat di `core/constants.py:1-10`:
`QTY = (14,3)` · `HARGA = (14,2)` · `NILAI = (18,2)`.

---

## 0. Abstract base — `core/models.py`

| Base | Field | Rujukan |
|---|---|---|
| `TimeStampedModel` | `dibuat_pada` `DateTimeField(auto_now_add)` · `diubah_pada` `DateTimeField(auto_now)` | `core/models.py:21-28` |
| `DiauditModel(TimeStampedModel)` | + `dibuat_oleh` FK→`AUTH_USER_MODEL`, **`on_delete=PROTECT`**, `related_name='+'`, `editable=False` | `core/models.py:31-40` |

---

## 1. App `core`

### `GrupBahan` — tabel `core_grup_bahan` — `core/models.py:47`
| Field | Tipe | null/blank | default | unique | catatan |
|---|---|---|---|---|---|
| `kode` | CharField(16) | — | — | ✅ | |
| `nama` | CharField(120) | — | — | — | |
| + TimeStampedModel | | | | | |

`Meta`: `ordering=['kode']`. **Tidak ada constraint/index tambahan.**
`__str__` `:63`. Tidak ada save()/delete() override.

### `Entitas` — tabel `core_entitas` — `core/models.py:72`
| Field | Tipe | null/blank | default | unique | choices |
|---|---|---|---|---|---|
| `kode` | CharField(8) | — | — | ✅ | — |
| `nama` | CharField(120) | — | — | — | — |
| `jenis` | CharField(12) | — | — | — | `JenisEntitas` (`:67`) |
| `npwp` | CharField(20) | blank | — | — | — |
| `grup_bahan` | FK→`GrupBahan` | — | — | — | **PROTECT**, `related_name='entitas'` |
| `aktif` | BooleanField | — | `True` | — | — |

`Meta`: `ordering=['kode']`. Tidak ada constraint/index tambahan.
`@property pkp` `:99` (= `bool(npwp)`).
**`delete()` di-override `:104` → selalu raise `ValidationError`.**

### `CounterDokumen` — tabel `core_counter_dokumen` — `core/models.py:114`
| Field | Tipe | default | catatan |
|---|---|---|---|
| `entitas` | FK→`Entitas` | — | **PROTECT**, tanpa `related_name` (→ `counterdokumen_set`) |
| `jenis` | CharField(16) | — | **tanpa `choices`** — nilai bebas (`PO`/`GRN`/`FAKTUR`/`JURNAL`/`BAS`/`SESI` hanya di komentar `:137`) |
| `periode` | CharField(6) | — | `YYYYMM` |
| `urutan` | PositiveIntegerField | `0` | |

`Meta` `:151-160`: `UniqueConstraint(entitas, jenis, periode)` = `uq_counter_dokumen`;
`ordering=['entitas','jenis','-periode']`.
Class attr `BULAN_ROMAWI` `:141`, `LEBAR` `:147`.
Classmethod `format_nomor` `:167`, `berikutnya` `:181` (`select_for_update` + `get_or_create`),
`preview` `:203` (tanpa lock).
Tidak mewarisi `TimeStampedModel` — model ini `models.Model` polos.

### `PeriodeAkuntansi` — tabel `core_periode_akuntansi` — `core/models.py:223`
| Field | Tipe | null/blank | default | catatan |
|---|---|---|---|---|
| `entitas` | FK→`Entitas` | — | — | **PROTECT**, `related_name='periode'` |
| `tahun` | PositiveSmallIntegerField | — | — | |
| `bulan` | PositiveSmallIntegerField | — | — | |
| `ditutup` | BooleanField | — | `False` | `db_index=True` |
| `ditutup_pada` | DateTimeField | ✅/✅ | — | `editable=False` |
| `ditutup_oleh` | FK→user | ✅/✅ | — | **PROTECT**, `related_name='+'`, `editable=False` |
| `alasan_buka` | TextField | blank | — | jejak append (`core/services.py:79`) |

`Meta` `:247-266`:
- `UniqueConstraint(entitas, tahun, bulan)` = `uq_periode_entitas`
- `CheckConstraint(1 ≤ bulan ≤ 12)` = `ck_periode_bulan_valid`
- `Index(entitas, tahun, bulan, ditutup)` = `ix_periode_lookup`

---

## 2. App `staff_user`

### `Jabatan` — tabel `staff_user_jabatan` — `staff_user/models.py:68`
`kode` CharField(16) unique · `nama` CharField(120) · `departemen` CharField(12)
choices `Departemen` default `UMUM` · `level` PositiveSmallIntegerField default 5 ·
`aktif` Boolean default True · + TimeStampedModel.
`Meta`: `ordering=['level','nama']`. Tanpa constraint/index tambahan.

### `Profil(AbstractUser)` — tabel `staff_user_profil` — `staff_user/models.py:104`
**`AUTH_USER_MODEL`** (`settings.py:100`).

| Field | Tipe | null/blank | default | unique | catatan |
|---|---|---|---|---|---|
| *(warisan AbstractUser)* | `username`,`password`,`email`,`first_name`,`last_name`,`is_active`,`is_staff`,`is_superuser`,`last_login`,`date_joined`,`groups`,`user_permissions` | | `is_active=True` | `username` ✅ | |
| `nip` | CharField(24) | ✅/✅ | — | ✅ | |
| `role` | CharField(12) | — | `STAFF` | — | choices `Role` `:41`, `db_index=True` |
| `jabatan` | FK→`Jabatan` | ✅/✅ | — | — | **PROTECT**, `related_name='pemegang'` |
| `foto` | ImageField | ✅/✅ | — | — | `upload_to='profil/%Y/%m/'` |
| `nomor_hp` | CharField(20) | blank | — | — | |
| `atasan` | FK→`self` | ✅/✅ | — | — | **PROTECT**, `related_name='bawahan'` |
| `entitas_default` | FK→`core.Entitas` | ✅/✅ | — | — | **PROTECT**, `related_name='pengguna_default'` |
| `entitas_diizinkan` | **M2M**→`core.Entitas` | blank | — | — | `related_name='pengguna_diizinkan'`; **kosong = boleh semua** |
| `status_kerja` | CharField(8) | — | `AKTIF` | — | choices `StatusKerja`, `db_index=True` |
| `tanggal_masuk` / `tanggal_keluar` | DateField | ✅/✅ | — | — | |
| `disetujui_oleh` | FK→`self` | ✅/✅ | — | — | **PROTECT**, `related_name='akun_disetujui'`, `editable=False` |
| `disetujui_pada`, `ditolak_pada` | DateTimeField | ✅/✅ | — | — | `editable=False` |
| `alasan_tolak` | TextField | blank | — | — | |

`objects = ProfilManager()` — custom manager `:91` (subclass `UserManager`) dengan
`aktif()`, `menunggu_persetujuan()`, `berperan(*roles)`.
`Meta` `:157-172`: `CheckConstraint(tanggal_keluar ≥ tanggal_masuk atau salah satunya NULL)` =
`ck_profil_tanggal_urut`; `Index(role, is_active)` = `ix_profil_role_aktif`.
Properties: `nama_lengkap` `:178`, `supervisor` `:182`, `bisa_login` `:186`,
`menunggu_persetujuan` `:190`. Method: `punya_role` `:196`, `modul_terbuka` `:200`,
`bisa_akses_modul` `:208`, `bisa_akses_entitas` `:212`, `entitas_terlihat` `:219`.
`clean()` `:227`. **`delete()` di-override `:235` → selalu raise.**

> `modul_terbuka()`/`bisa_akses_modul()` mengimpor `.permissions` **di dalam
> fungsi** (`:205`, `:209`) — penanda pencegahan circular import.

### `DataKepegawaian` — tabel `staff_user_data_kepegawaian` — `staff_user/models.py:258`
`profil` **O2O**→`Profil` **PROTECT** `related_name='kepegawaian'` ·
`nik_ktp`(16) · `npwp`(20) · `tempat_lahir`(80) · `tanggal_lahir` Date ·
`jenis_kelamin`(1) choices · `alamat` Text · `status_pajak`(4) choices ·
`bank`(40) · `no_rekening`(40) · `nama_rekening`(120) ·
`kontak_darurat_nama`(120) / `_hubungan`(40) / `_hp`(20) — semuanya `blank=True`.
`Meta`: tanpa constraint/index tambahan. `@property usia` `:298`.

### `RiwayatAkses` — tabel `staff_user_riwayat_akses` — `staff_user/models.py:308`
`profil` FK→`Profil` null/blank **PROTECT** `related_name='riwayat_akses'` ·
`username_dicoba`(150) · `waktu` DateTime `auto_now_add` `db_index=True` ·
`berhasil` Boolean `db_index=True` · `alasan_gagal`(80) blank ·
`ip` GenericIPAddressField null/blank · `user_agent`(255) blank.
`Meta` `:328-336`: `Index(username_dicoba, -waktu)` = `ix_akses_username`;
`Index(berhasil, -waktu)` = `ix_akses_hasil`.
**`save()` `:342` menolak update (append-only); `delete()` `:347` selalu raise.**

---

## 3. App `master`

Semua model mewarisi `TimeStampedModel` dan **semua** meng-override `delete()`
agar selalu raise (`master/models.py:37,54,96,136,170`).

### `Kategori` — `master_kategori` — `master/models.py:19`
`kode` CharField(16) unique **blank=True** · `nama`(120) · `aktif` Boolean default True.
`save()` `:32` → `generate_kode_urut(prefix='KAT', padding=3)`.

### `Satuan` — `master_satuan` — `master/models.py:41`
`kode` CharField(8) unique (**tanpa blank**) · `nama`(40) · `aktif` default True.
Tidak ada auto-generate kode.

### `Suplier` — `master_suplier` — `master/models.py:65`
`kode`(16) unique blank · `nama`(200) · `npwp`(20) blank · `alamat` Text blank ·
`kontak_nama`(120) · `kontak_hp`(20) · `email` EmailField blank ·
`termin_hari_default` PositiveSmallIntegerField default 0 · `aktif` default True.
`Meta`: `ordering=['nama']`. `@property pkp` `:87`. `save()` `:91` → `SUP-####`.

### `Produk` — `master_produk` — `master/models.py:100`
| Field | Tipe | catatan |
|---|---|---|
| `kode` | CharField(24) unique blank | prefix dinamis per `jenis`: `BP`/`BJ`/`KM`/`PRD` (`save()` `:121`) |
| `nama` | CharField(200) | |
| `jenis` | CharField(12) choices `JenisProduk` `:58` | `db_index=True` |
| `kategori` | FK→`Kategori` null/blank | **PROTECT**, `related_name='produk'` |
| `satuan` | FK→`Satuan` | **PROTECT**, `related_name='produk'` — **wajib**, padahal `Satuan` tidak punya endpoint |
| `lokasi_simpan` | CharField(100) blank | |
| `suplier` | **M2M**→`Suplier` blank | `related_name='produk_disuplai'` |
| `disimpan_di_tanki` | Boolean default False | |
| `aktif` | Boolean default True | |

`Meta` `:112-116`: `Index(jenis, aktif)` = `ix_produk_jenis_aktif`.

### `Pelanggan` — `master_pelanggan` — `master/models.py:140`
`kode`(16) unique blank (`CUST-####`) · `nama`(200) · `npwp`(20) · `alamat` ·
`kontak_nama`(120) · `kontak_hp`(20) · `termin_hari_default` default 0 ·
`plafon_kredit` **DecimalField(18,2)** default 0, `MinValueValidator(0)` ·
`aktif` default True. `Meta`: `ordering=['nama']`.

> `plafon_kredit` memakai angka literal `18,2` (`:151-154`), bukan
> `NILAI_DIGITS/NILAI_PLACES` dari `core/constants.py` — melanggar aturan yang
> ditulis di `core/constants.py:1`.

---

## 4. App `dokumen`

### `Lampiran(DiauditModel)` — `dokumen_lampiran` — `dokumen/models.py:35`
| Field | Tipe | catatan |
|---|---|---|
| `jenis` | CharField(16) choices `JenisLampiran` `:20` | `db_index=True` |
| `berkas` | FileField | `upload_to=path_lampiran` `:29` (pakai `timezone.now()`, bukan `dibuat_pada`) |
| `nama_asli` | CharField(255) blank | diisi di `save()` `:72` |
| `ukuran_byte` | PositiveIntegerField default 0 | `editable=False`, diisi di `save()` |
| `keterangan` | CharField(255) blank | |
| `content_type` | FK→`ContentType` null/blank | **PROTECT** |
| `object_id` | PositiveBigIntegerField null/blank | |
| `pemilik` | **GenericForeignKey**(`content_type`,`object_id`) | |
| `digantikan_oleh` | **O2O**→`self` null/blank | **PROTECT**, `related_name='menggantikan'` |

`Meta` `:56-63`: `Index(content_type, object_id)` = `ix_lampiran_pemilik`;
`Index(jenis, -dibuat_pada)` = `ix_lampiran_jenis`.
`@property masih_berlaku` `:68`. **`delete()` `:82` selalu raise.**

---

## 5. App `inventory`

### `Tangki(TimeStampedModel)` — `inventory_tangki` — `inventory/models.py:46`
`kode`(16) unique · `nama`(120) · `grup_bahan` FK→`core.GrupBahan` **PROTECT**
`related_name='tangki'` · `kapasitas_kg` Decimal(14,3) · `isi_kg` Decimal(14,3)
default 0 `editable=False` · `produk_terisi` FK→`master.Produk` null/blank
**PROTECT** `related_name='+'` `editable=False` · `aktif` default True.
`Meta` `:66-77`:
- `CheckConstraint(kapasitas_kg > 0)` = `ck_tangki_kapasitas`
- `CheckConstraint(0 ≤ isi_kg ≤ kapasitas_kg)` = `ck_tangki_isi_dalam_kapasitas`

Properties `ruang_kosong_kg` `:82`, `persen_terisi` `:86`.

### `Stok(TimeStampedModel)` — `inventory_stok` — `inventory/models.py:93`
`produk` FK→`master.Produk` **PROTECT** `related_name='stok'` ·
`grup_bahan` FK→`core.GrupBahan` **PROTECT** `related_name='stok'` ·
`lapis` CharField(4) choices `Lapis` `db_index=True` ·
`tangki` FK→`Tangki` null/blank **PROTECT** `related_name='stok'` ·
`qty` Decimal(14,3) default 0 `editable=False` ·
`urutan_terakhir` BigIntegerField default 0 `editable=False`.
`Meta` `:110-127`:
- `UniqueConstraint(produk,grup_bahan,lapis,tangki)` **condition `tangki NOT NULL`** = `uq_stok_tangki`
- `UniqueConstraint(produk,grup_bahan,lapis)` **condition `tangki IS NULL`** = `uq_stok_rak`
- `CheckConstraint(qty ≥ 0)` = `ck_stok_nonneg`
- `Index(grup_bahan, lapis)` = `ix_stok_grup_lapis`

`@property berpemilik` `:132` (True untuk RAW/JADI).

### `MutasiStok(models.Model)` — `inventory_mutasi_stok` — `inventory/models.py:150`
`stok` FK→`Stok` **PROTECT** `related_name='mutasi'` · `urutan` BigIntegerField ·
`tanggal` DateTimeField `db_index=True` · `jenis` CharField(8) choices
`JenisMutasiStok` `:138` · `masuk`/`keluar` Decimal(14,3) default 0 ·
`saldo_akhir` Decimal(14,3) · `referensi`(64) blank ·
**`idempotency_key` CharField(96) UNIQUE** · `dibuat_pada` auto_now_add.
`Meta` `:168-180`:
- `UniqueConstraint(stok, urutan)` = `uq_mutasi_stok_urutan`
- `CheckConstraint(masuk ≥ 0 AND keluar ≥ 0)` = `ck_mutasi_stok_nonneg`
- `CheckConstraint(masuk = 0 OR keluar = 0)` = `ck_mutasi_stok_satu_sisi`
- `Index(stok, -urutan)` = `ix_mutasi_stok_urut`

**`save()` `:186` menolak update; `delete()` `:191` selalu raise.**

### `SaldoEntitas(TimeStampedModel)` — `inventory_saldo_entitas` — `inventory/models.py:195`
`stok` FK→`Stok` **PROTECT** `related_name='kepemilikan'` ·
`entitas` FK→`core.Entitas` **PROTECT** `related_name='saldo_bahan'` ·
`qty` Decimal(14,3) default 0 `editable=False` ·
`nilai` Decimal(18,2) default 0 `editable=False`.
`Meta` `:212-221`:
- `UniqueConstraint(stok, entitas)` = `uq_saldo_entitas`
- `CheckConstraint(qty ≥ 0)` = `ck_saldo_entitas_nonneg`

`clean()` `:226` menolak lapis POOL — **tapi `clean()` tidak pernah dipanggil
oleh `_geser_pemilik()`** (`inventory/services.py:115`); penjaganya adalah
pemeriksaan Python eksplisit di baris `:117`. **Tidak ada CheckConstraint DB
yang setara** — `nilai` juga tidak dibatasi ≥ 0.

### `NilaiEkuivalen(TimeStampedModel)` — `inventory_nilai_ekuivalen` — `inventory/models.py:237`
`produk` FK→`master.Produk` **PROTECT** `related_name='nilai_ekuivalen'` ·
`nilai_per_satuan` Decimal(18,2) `MinValueValidator(0.01)` ·
`berlaku_sejak` DateField · `catatan`(255) blank.
`Meta` `:257-264`: `UniqueConstraint(produk, berlaku_sejak)` = `uq_ekuivalen_produk_tanggal`.
Classmethod `tarif(produk_id, tanggal)` `:269` — raise `ValidationError` kalau belum ada.

### `MutasiKlaim(models.Model)` — `inventory_mutasi_klaim` — `inventory/models.py:289`
`entitas` FK→`core.Entitas` **PROTECT** `related_name='klaim'` ·
`grup_bahan` FK→`core.GrupBahan` **PROTECT** `related_name='klaim'` ·
`tanggal` DateField `db_index=True` · `jenis` CharField(8) choices `JenisKlaim` `:282` ·
`produk` FK→`master.Produk` null/blank **PROTECT** `related_name='klaim'` ·
`qty` Decimal(14,3) default 0 · `tarif` Decimal(18,2) default 0 ·
**`nilai` Decimal(18,2) — BERTANDA (boleh negatif)** ·
`referensi`(64) blank · **`idempotency_key`(96) UNIQUE** · `dibuat_pada` auto_now_add.
`Meta` `:319-326`: `Index(grup_bahan, entitas, tanggal)` = `ix_klaim_grup_ent`.
**Tidak ada CheckConstraint sama sekali.**
**`save()` `:331` menolak update; `delete()` `:336` selalu raise.**

### `PosisiKlaim(TimeStampedModel)` — `inventory_posisi_klaim` — `inventory/models.py:340`
`entitas` FK→`core.Entitas` **PROTECT** `related_name='posisi_klaim'` ·
`grup_bahan` FK→`core.GrupBahan` **PROTECT** `related_name='posisi_klaim'` ·
`total_setor`, `total_ambil`, `nilai_bersih` Decimal(18,2) default 0 `editable=False`.
`Meta` `:363-370`: `UniqueConstraint(entitas, grup_bahan)` = `uq_posisi_klaim`.
`@property berhutang` `:376`. **Cache — sumber kebenarannya `MutasiKlaim`.**

---

## 6. App `akunting`

### `Akun(TimeStampedModel)` — `akunting_akun` — `akunting/models/akun.py:43`
`kode` CharField(8) unique · `nama`(120) · `tipe` CharField(12) choices
`TipeAkun` `:19` `db_index=True` · `parent` FK→`self` null/blank **PROTECT**
`related_name='anak'` · `boleh_diposting` Boolean default True ·
`aktif` Boolean default True.
`objects = AkunQuerySet.as_manager()` — **custom manager** `:31` dengan
`bisa_diposting()`, `neraca()`, `laba_rugi()`.
`Meta` `:59-65`: `Index(tipe, kode)` = `ix_akun_tipe_kode`.
Properties `saldo_normal` `:70`, `pengali` `:74`. `clean()` `:79`.
Seed 21 akun di `akunting/migrations/0005_seed_coa.py:16-43`.

### `SaldoAkunBulanan(models.Model)` — `akunting_saldo_akun_bulanan` — `akun.py:89`
`akun` FK→`Akun` **PROTECT** `related_name='saldo_bulanan'` ·
`entitas` FK→`core.Entitas` **PROTECT** (tanpa related_name) ·
`tahun`/`bulan` PositiveSmallIntegerField ·
`saldo_awal`,`total_debit`,`total_kredit`,`saldo_akhir` Decimal(18,2) default 0.
`Meta` `:112-127`:
- `UniqueConstraint(akun, entitas, tahun, bulan)` = `uq_saldo_akun_periode`
- `CheckConstraint(1 ≤ bulan ≤ 12)` = `ck_saldo_bulan_valid`
- `Index(entitas, tahun, bulan)` = `ix_saldo_ent_periode`

> **Tidak ada satu baris kode pun yang menulis ke tabel ini** — grep
> `SaldoAkunBulanan` di luar `models/akun.py` dan `__init__.py` = 0 hasil.
> Checkpoint bulanan yang dijanjikan docstring `:90-95` belum diimplementasi.

### `JurnalUmum(DiauditModel)` — `akunting_jurnal_umum` — `akunting/models/jurnal.py:53`
| Field | Tipe | catatan |
|---|---|---|
| `entitas` | FK→`core.Entitas` | **PROTECT**, `related_name='jurnal'` |
| `nomor` | CharField(32) `editable=False` | dari `CounterDokumen` |
| `tanggal` | DateField `db_index=True` | |
| `kejadian` | CharField(16) choices `JenisKejadian` `:27` `db_index=True` | |
| `referensi` | CharField(64) blank | |
| `keterangan` | CharField(255) blank | |
| `idempotency_key` | CharField(96) **UNIQUE** `editable=False` | |
| `dibalik_oleh` | **O2O**→`self` null/blank | **PROTECT**, `related_name='membalik'`, `editable=False` |

`objects = JurnalUmumQuerySet.as_manager()` — **custom manager** `:41`.
`Meta` `:72-84`:
- `UniqueConstraint(entitas, nomor)` = `uq_jurnal_nomor_per_entitas`
- `Index(entitas, tanggal)` = `ix_jurnal_ent_tgl`
- `Index(referensi)` = `ix_jurnal_referensi`

Properties `total_debit` `:89`, `total_kredit` `:94`, `seimbang` `:97`,
`sudah_dibalik` `:101` — ketiganya **query agregat per instance → N+1 kalau
dipakai di list** (dan `JurnalUmumSerializer` `akunting/serializers.py:48-53`
memang memakai ketiganya).
**`delete()` `:105` selalu raise.**

### `JurnalDetail(models.Model)` — `akunting_jurnal_detail` — `jurnal.py:111`
`jurnal` FK→`JurnalUmum` **PROTECT** `related_name='baris'` ·
`akun` FK→`Akun` **PROTECT** `related_name='baris_jurnal'` ·
`debit`/`kredit` Decimal(18,2) default 0 · `keterangan`(255) blank.
`Meta` `:127-146`:
- `CheckConstraint(debit ≥ 0 AND kredit ≥ 0)` = `ck_jd_nilai_nonneg`
- `CheckConstraint(debit = 0 OR kredit = 0)` = `ck_jd_satu_sisi`
- `CheckConstraint(NOT(debit = 0 AND kredit = 0))` = `ck_jd_tidak_nol_dua_duanya`
- `Index(akun, jurnal)` = `ix_jd_akun_jurnal`

`clean()` `:152` menolak akun header — **dilewati oleh `bulk_create` di
`posting()` (`akunting/services.py:110`) dan `jurnal_balik()` (`:136`)**.
**`delete()` `:158` selalu raise.**

#### ⚠ TRIGGER DATABASE — satu-satunya di seluruh proyek
`akunting/migrations/0004_trigger_jurnal_seimbang.py:23-50`

```sql
CREATE OR REPLACE FUNCTION cek_jurnal_seimbang() RETURNS TRIGGER ...
  SELECT COALESCE(SUM(debit) - SUM(kredit), 0) INTO selisih
    FROM akunting_jurnal_detail WHERE jurnal_id = jid;
  IF selisih <> 0 THEN RAISE EXCEPTION ... ERRCODE = 'check_violation'; END IF;

CREATE CONSTRAINT TRIGGER trg_jurnal_seimbang
  AFTER INSERT OR UPDATE OR DELETE ON akunting_jurnal_detail
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION cek_jurnal_seimbang();
```

`DEFERRABLE INITIALLY DEFERRED` → diperiksa saat **COMMIT**, sehingga baris
debit boleh tersimpan sebelum kreditnya. `reverse_sql` tersedia (`:52-55`).
Ini penjaga invariant D=K yang tidak bisa dilewati `bulk_create`/shell.

**Catatan biaya**: trigger `FOR EACH ROW` — satu jurnal 4 baris → 4 kali
`SUM()` atas seluruh baris jurnal itu saat COMMIT.

### `PurchaseOrder(DiauditModel)` — `akunting_purchase_order` — `akunting/models/pembelian.py:63`
`entitas` FK→`core.Entitas` **PROTECT** `related_name='purchase_order'` ·
`suplier` FK→`master.Suplier` **PROTECT** `related_name='purchase_order'` ·
`no_po`(32) `editable=False` · `tanggal` DateField default `timezone.localdate` ·
`status`(10) choices `StatusPO` `:29` default `DRAFT` `db_index=True` ·
`tanggal_kirim_diminta` DateField null/blank · `catatan` TextField blank.
`objects = PurchaseOrderQuerySet.as_manager()` — **custom manager** `:37`
(`untuk_entitas`, `terbuka`, `dengan_total`, `untuk_gudang`).
`Meta` `:83-95`:
- `UniqueConstraint(entitas, no_po)` = `uq_po_nomor_per_entitas`
- `Index(entitas, status, -tanggal)` = `ix_po_ent_status`
- `Index(suplier, status)` = `ix_po_sup_status`

`@property total_nilai` `:102` (agregat, N+1 di list — makanya ada
`.dengan_total()`), `boleh_diubah` `:107`; method `semua_item_lengkap()` `:111`,
`ada_penerimaan()` `:115`.
**`save()` `:120` memanggil `CounterDokumen.berikutnya()`** — ini melakukan
`select_for_update`, jadi **`PurchaseOrder.save()` WAJIB berada di dalam
`transaction.atomic`**. Dipanggil dari `services.buat_po()` yang atomic ✅.
`clean()` `:125`. `delete()` `:129` hanya mengizinkan status DRAFT.
`kirim()` `:134` dan `batalkan()` `:145` — **duplikat dari
`services.kirim_po()`/`batalkan_po()`**, dua jalur untuk transisi state yang sama.

### `PurchaseOrderItem(models.Model)` — `akunting_purchase_order_item` — `pembelian.py:156`
`purchase_order` FK→`PurchaseOrder` **`on_delete=CASCADE`** `related_name='item'`
⚠ *(lihat penanda di bawah)* ·
`produk` FK→`master.Produk` **PROTECT** (tanpa related_name) ·
`nama_item`(200) snapshot · `satuan`(8) default `'kg'` ·
`qty_pesan` Decimal(14,3) `MinValueValidator(0.001)` ·
`qty_diterima` Decimal(14,3) default 0 `editable=False` (**cache** dari
`warehouse.PenerimaanItem`) · `harga_per_kg` Decimal(14,2) `MinValueValidator(0)` ·
`amount` Decimal(18,2) default 0 `editable=False` (turunan).
`Meta` `:187-203`:
- `CheckConstraint(qty_pesan > 0)` = `ck_poitem_qty_positif`
- `CheckConstraint(harga_per_kg ≥ 0)` = `ck_poitem_harga_nonneg`
- `CheckConstraint(0 ≤ qty_diterima ≤ qty_pesan)` = `ck_poitem_terima_dalam_batas`
- `UniqueConstraint(purchase_order, produk)` = `uq_poitem_produk`
- `Index(purchase_order)` = `ix_poitem_po` *(redundan — FK sudah berindeks)*

Properties `sisa_qty` `:208`, `sudah_lengkap` `:212`.
**`save()` `:216` selalu menghitung ulang `amount`** dan memaksa `amount`
masuk ke `update_fields` `:225-226`.

> **`_simpan_item()` (`warehouse/services.py:174`) memakai `F('qty_diterima') + qty`
> lalu `save(update_fields=['qty_diterima'])`.** Karena `save()` menghitung
> `self.amount = self.qty_pesan * self.harga_per_kg` di baris `:220` dan
> `update_fields` ditambah `'amount'`, `amount` ikut ditulis ulang setiap
> penerimaan — nilainya sama, jadi tidak merusak, tapi kolom `qty_diterima`
> menjadi objek `CombinedExpression` di memori setelah save (tidak di-refresh).

### `FakturPembelian(DiauditModel)` — `akunting_faktur_pembelian` — `akunting/models/hutang.py:65`
| Field | Tipe | catatan |
|---|---|---|
| `entitas` | FK→`core.Entitas` | **PROTECT**, `related_name='faktur_pembelian'` |
| `suplier` | FK→`master.Suplier` | **PROTECT**, `related_name='faktur_pembelian'` |
| `jenis` | CharField(8) choices `JenisFaktur` default `BARANG` | |
| `penerimaan` | FK→`warehouse.PenerimaanBarang` null/blank | **PROTECT**, `related_name='faktur'` |
| `no_internal` | CharField(32) `editable=False` | `CounterDokumen` |
| `nomor_faktur` | CharField(64) | nomor dari suplier |
| `tanggal_faktur` | DateField | |
| `termin_hari` | PositiveSmallIntegerField default 0 | |
| `tanggal_jatuh_tempo` | DateField `db_index=True` `editable=False` | dihitung di `save()` `:165` |
| `total_tagihan` | Decimal(18,2) `MinValueValidator(0)` | |
| `total_dibayar` | Decimal(18,2) default 0 `editable=False` | cache |
| `sisa_hutang` | Decimal(18,2) default 0 `editable=False` | cache |
| `status` | CharField(12) choices `StatusFaktur` default `BELUM_BAYAR` `db_index=True` | |
| `dokumen` | FK→`dokumen.Lampiran` null/blank | **PROTECT**, `related_name='+'` |
| `catatan` | TextField blank | |

`objects = FakturPembelianQuerySet.as_manager()` — **custom manager** `:49`.
`Meta` `:114-145`:
- `UniqueConstraint(suplier, nomor_faktur)` = `uq_faktur_suplier_nomor`
- `UniqueConstraint(entitas, no_internal)` = `uq_faktur_no_internal`
- `CheckConstraint(sisa_hutang ≥ 0)` = `ck_faktur_sisa_nonneg`
- `CheckConstraint(0 ≤ total_dibayar ≤ total_tagihan)` = `ck_faktur_dibayar_dalam_batas`
- `CheckConstraint(jenis='JASA' OR penerimaan IS NOT NULL)` = `ck_faktur_barang_wajib_penerimaan`
- `Index(suplier, status, tanggal_jatuh_tempo)` = `ix_faktur_sup_status_tempo`
- `Index(entitas, status)` = `ix_faktur_ent_status`

Properties `terlambat` `:150`, `umur_hari` `:155`.
**`save()` `:160`** — memanggil `CounterDokumen.berikutnya()` (butuh atomic),
menghitung ulang `tanggal_jatuh_tempo`, dan **menyetel `sisa_hutang = total_tagihan`
hanya saat `_state.adding`** `:168`. `clean()` `:172`. **`delete()` `:182` raise.**

> ⚠ **Tidak ada constraint DB yang menegakkan `sisa_hutang = total_tagihan − total_dibayar`.**
> Cache ini hanya dijaga oleh `post_pembayaran()` (`akunting/services.py:178-182`).

### `KartuHutang(models.Model)` — `akunting_kartu_hutang` — `hutang.py:186`
`faktur` FK→`FakturPembelian` **PROTECT** `related_name='mutasi'` ·
`tanggal` DateField `db_index=True` · `jenis`(8) choices `JenisMutasiHutang` ·
`debit`/`kredit` Decimal(18,2) default 0 · `referensi`(64) blank ·
`dibuat_pada` auto_now_add.
`Meta` `:206-220`:
- `CheckConstraint(debit ≥ 0 AND kredit ≥ 0)` = `ck_kh_nonneg`
- `CheckConstraint(debit = 0 OR kredit = 0)` = `ck_kh_satu_sisi`
- `Index(faktur, tanggal)` = `ix_kh_faktur_tgl`

**`save()` `:226` menolak update; `delete()` `:231` raise.**
> **`referensi` TIDAK unique**, padahal `post_pembayaran()` memakainya sebagai
> kunci idempotensi (`akunting/services.py:160`). Cek "sudah ada?" itu tidak
> punya penjaga di level DB.

### `UangMukaSuplier(TimeStampedModel)` — `akunting_uang_muka_suplier` — `hutang.py:235`
`entitas` FK→`core.Entitas` **PROTECT** (tanpa related_name) ·
`suplier` FK→`master.Suplier` **PROTECT** `related_name='uang_muka'` ·
`tanggal` DateField · `nominal` Decimal(18,2) `MinValueValidator(0.01)` ·
`sisa` Decimal(18,2) `editable=False` · `referensi`(64) blank.
`Meta` `:257-269`:
- `CheckConstraint(0 ≤ sisa ≤ nominal)` = `ck_um_sisa_dalam_batas`
- `Index(suplier, entitas)` = `ix_um_sup_ent`

`save()` `:274` menyetel `sisa = nominal` saat pembuatan.
> **Tidak ada kode yang pernah mengurangi `sisa`** — grep `UangMukaSuplier`
> di luar model hanya menemukan `objects.create()` (`akunting/services.py:228`)
> dan pembacaan di `UangMukaViewSet`. Uang muka masuk tapi tidak pernah keluar.

---

## 7. App `keuangan`

### `RekeningBank(TimeStampedModel)` — `keuangan_rekening_bank` — `keuangan/models.py:32`
`entitas` FK→`core.Entitas` **PROTECT** `related_name='rekening'` ·
`jenis`(10) choices `JenisRekening` `:26` · `nama_bank`(80) blank ·
`nomor_rekening`(40) blank · `nama_pemilik`(120) blank ·
`akun` FK→`akunting.Akun` **PROTECT** `related_name='rekening'` ·
`saldo` Decimal(18,2) default 0 `editable=False` ·
`urutan_terakhir` BigIntegerField default 0 `editable=False` · `aktif` default True.
`Meta` `:51-61`: `UniqueConstraint(entitas, nomor_rekening)` **condition
`NOT nomor_rekening=''`** = `uq_rekening_nomor`.
> **Tidak ada `CheckConstraint(saldo ≥ 0)`** dan **tidak ada unique pada
> `(entitas, jenis)`** — dua rekening `KAS_KECIL` untuk satu entitas mungkin,
> padahal `catat_pengeluaran()` memakai `.filter(...).first()`
> (`keuangan/services.py:22-24`) yang akan memilih salah satunya secara acak.

### `MutasiKas(models.Model)` — `keuangan_mutasi_kas` — `keuangan/models.py:69`
`rekening` FK→`RekeningBank` **PROTECT** `related_name='mutasi'` ·
`urutan` BigIntegerField · `tanggal` DateTimeField default `timezone.now` `db_index=True` ·
`debit`/`kredit` Decimal(18,2) default 0 · `saldo_akhir` Decimal(18,2) ·
`keterangan`(255) blank · `referensi`(64) blank ·
**`idempotency_key`(96) UNIQUE** · `dibuat_pada` auto_now_add.
`Meta` `:92-105`:
- `UniqueConstraint(rekening, urutan)` = `uq_mutasi_kas_urutan`
- `CheckConstraint(debit ≥ 0 AND kredit ≥ 0)` = `ck_mutasi_kas_nonneg`
- `CheckConstraint(debit = 0 OR kredit = 0)` = `ck_mutasi_kas_satu_sisi`
- `Index(rekening, -urutan)` = `ix_mutasi_kas_urut`

**`save()` `:111` menolak update; `delete()` `:116` raise.**
> ⚠ **Konvensi tanda tidak konsisten.** `__str__` `:107` merender
> `debit` sebagai `-` dan `kredit` sebagai `+`, tapi `catat_pengeluaran()`
> mencatat uang KELUAR di kolom **`kredit`** (`keuangan/services.py:42`)
> sambil **mengurangi** `rekening.saldo` (`:34`). Satu-satunya penulis tabel
> ini memakai konvensi yang berlawanan dengan `__str__` model.

### `RencanaBayar(DiauditModel)` — `keuangan_rencana_bayar` — `keuangan/models.py:128`
`entitas` FK→`core.Entitas` **PROTECT** · `suplier` FK→`master.Suplier`
**PROTECT** `related_name='rencana_bayar'` · `rekening` FK→`RekeningBank`
**PROTECT** `related_name='rencana_bayar'` · `tanggal_rencana` DateField ·
`nominal` Decimal(18,2) `MinValueValidator(0.01)` · `status`(12) choices
`StatusRencana` `:120` default `DRAFT` `db_index=True` ·
`disetujui_oleh` / `dieksekusi_oleh` FK→`staff_user.Profil` null/blank **PROTECT** ·
`mutasi` **O2O**→`MutasiKas` null/blank **PROTECT** `related_name='rencana'` ·
`catatan` TextField blank.
`Meta` `:163-169`: `Index(status, tanggal_rencana)` = `ix_rencana_status`.
`clean()` `:174` memastikan rekening milik entitas yang sama.
> **Model mati** — tidak ada endpoint, tidak ada service yang menyentuhnya.

### `PengeluaranKas(TimeStampedModel)` — `keuangan_pengeluaran_kas` — `keuangan/models.py:181`
`entitas` FK→`core.Entitas` **PROTECT** (tanpa related_name) ·
`kategori` CharField(50) **tanpa choices** · `keterangan` CharField(255) ·
`pemohon` CharField(120) **teks bebas, bukan FK ke Profil** ·
`nominal` **DecimalField(18,2)** — angka literal, bukan konstanta ·
`bukti_nota` FileField null/blank `upload_to='keuangan/nota/'` ·
`mutasi` **O2O**→`MutasiKas` null/blank **PROTECT** `related_name='pengeluaran'`.
`Meta` `:195-197`: `ordering=['-id']`. **Tidak ada constraint maupun index tambahan.**
Tidak ada `save()`/`delete()` override.
> ⚠ Satu-satunya model transaksional yang **tidak** mewarisi `DiauditModel` —
> tidak ada `dibuat_oleh`. Siapa yang mengeluarkan uang tidak tercatat di
> tabel ini (parameter `user` di `catat_pengeluaran()` hanya diteruskan ke jurnal).
> Juga tidak ada `CheckConstraint(nominal > 0)`.

---

## 8. App `warehouse`

### `PenerimaanBarang(DiauditModel)` — `warehouse_penerimaan_barang` — `warehouse/models.py:44`
`purchase_order` FK→`akunting.PurchaseOrder` **PROTECT** `related_name='penerimaan'` ·
`nomor`(32) `editable=False` · `tanggal` DateField default `localdate` `db_index=True` ·
`no_surat_jalan`(64) · `dokumen` FK→`dokumen.Lampiran` null/blank **PROTECT**
`related_name='+'` · `ada_selisih` Boolean default False `editable=False` `db_index=True` ·
`catatan` TextField blank.
`Meta` `:61-74`:
- `UniqueConstraint(purchase_order, no_surat_jalan)` = `uq_penerimaan_surat_jalan`
- `Index(tanggal)` = `ix_penerimaan_tanggal` *(redundan — `db_index=True` sudah ada)*
- `Index(ada_selisih)` = `ix_penerimaan_selisih` *(redundan — idem)*

`@property entitas` `:79` (**diturunkan dari PO, tidak disimpan**) ·
`total_koli` `:84` (iterasi item → N+1 kalau tanpa prefetch).
`save()` `:88` → `CounterDokumen.berikutnya()` (butuh atomic).
**`delete()` `:95` raise.**

### `PenerimaanItem(models.Model)` — `warehouse_penerimaan_item` — `warehouse/models.py:102`
`penerimaan` FK→`PenerimaanBarang` **PROTECT** `related_name='item'` ·
`po_item` FK→`akunting.PurchaseOrderItem` **PROTECT** `related_name='realisasi'` ·
`jenis_kemasan`(8) choices `JenisKemasan` default `CURAH` ·
`jumlah_koli` PositiveIntegerField null/blank ·
`isi_per_koli` Decimal(14,3) null/blank ·
`qty_deklarasi` Decimal(14,3) default 0 `editable=False` (turunan) ·
`qty_diterima` Decimal(14,3) `MinValueValidator(0)` ·
`qty_ditolak` Decimal(14,3) default 0 · `alasan_tolak`(255) blank.
`Meta` `:142-161`:
- `CheckConstraint(qty_diterima ≥ 0 AND qty_ditolak ≥ 0)` = `ck_penerimaan_item_nonneg`
- `CheckConstraint(NOT(qty_diterima=0 AND qty_ditolak=0))` = `ck_penerimaan_item_tidak_nol`
- `CheckConstraint(isi_per_koli IS NULL OR isi_per_koli > 0)` = `ck_penerimaan_isi_positif`
- `UniqueConstraint(penerimaan, po_item)` = `uq_penerimaan_item`

Properties `selisih_berat` `:168`, `persen_selisih_berat` `:178`,
`selisih_po` `:184`, `ada_selisih` `:190`.
`save()` `:194` menghitung ulang `qty_deklarasi`. `clean()` `:203`.

### `LaporanSelisih(DiauditModel)` — `warehouse_laporan_selisih` — `warehouse/models.py:243`
`nomor`(32) `editable=False` · `penerimaan` FK→`PenerimaanBarang` **PROTECT**
`related_name='laporan_selisih'` · `penerimaan_item` FK→`PenerimaanItem`
null/blank **PROTECT** `related_name='laporan_selisih'` ·
`tanggal` DateField default `localdate` `db_index=True` ·
`jenis`(14) choices `JenisSelisih` `:218` `db_index=True` ·
`status`(14) choices `StatusSelisih` `:227` default `DIBUKA` `db_index=True` ·
`qty_selisih` Decimal(14,3) default 0 (**boleh negatif**) ·
`nilai_selisih` Decimal(18,2) default 0 `editable=False` ·
`uraian` TextField · `foto` FK→`dokumen.Lampiran` null/blank **PROTECT** ·
`resolusi`(8) choices `Resolusi` `:235` blank ·
`nilai_klaim` Decimal(18,2) default 0 ·
`catatan_resolusi` TextField blank · `diselesaikan_pada` DateTime null/blank
`editable=False` · `diselesaikan_oleh` FK→`staff_user.Profil` null/blank
**PROTECT** `related_name='selisih_diselesaikan'` `editable=False`.
`Meta` `:305-317`:
- `UniqueConstraint(nomor)` = `uq_selisih_nomor` *(global, bukan per entitas)*
- `CheckConstraint(nilai_klaim ≥ 0)` = `ck_selisih_klaim_nonneg`
- `Index(status, -tanggal)` = `ix_selisih_status`

Properties `suplier` `:322`, `terbuka` `:326`, `umur_hari` `:330`.
`save()` `:334` → `CounterDokumen` (butuh atomic). **`delete()` `:341` raise.**
> Tidak ada constraint `nilai_klaim ≤ nilai_selisih` di DB; hanya dicek di
> `warehouse/services.py:363`.

### `Packaging(TimeStampedModel)` — `warehouse_packaging` — `warehouse/models.py:349`
`tanggal` DateField default `localdate` `db_index=True` ·
`produk` FK→`master.Produk` **PROTECT** `related_name='packaging'` ·
`grup_bahan` FK→`core.GrupBahan` **PROTECT** (tanpa related_name) ·
`qty_curah` Decimal(14,3) · `qty_kemasan` PositiveIntegerField ·
`isi_per_kemasan` Decimal(14,3).
`Meta` `:363-370`: `CheckConstraint(qty_curah > 0)` = `ck_packaging_curah`.
`@property susut` `:375`.
> Model murni pencatatan — tidak terhubung ke `Stok`/`MutasiStok` sama sekali.

---

## 9. App `produksi`

### `Resep(TimeStampedModel)` — `produksi_resep` — `produksi/models.py:34`
`produk_jadi` FK→`master.Produk` **PROTECT** `related_name='resep'` ·
`versi` PositiveSmallIntegerField default 1 · `nama`(120) blank ·
`hasil_per_batch` Decimal(14,3) default 1 `MinValueValidator(0.001)` ·
`susut_wajar` **Decimal(5,4)** default 0 · `berlaku_sejak` DateField default
`localdate` · `aktif` Boolean default True.
`Meta` `:56-69`:
- `UniqueConstraint(produk_jadi, versi)` = `uq_resep_versi`
- `CheckConstraint(hasil_per_batch > 0)` = `ck_resep_hasil_positif`
- `CheckConstraint(0 ≤ susut_wajar < 1)` = `ck_resep_susut_wajar`

Classmethod `berlaku()` `:74`; method `kebutuhan()` `:87`.
> `susut_wajar` didefinisikan dan divalidasi tapi **tidak pernah dibaca** oleh
> kode mana pun (grep = 0 di luar model).

### `ResepItem(models.Model)` — `produksi_resep_item` — `produksi/models.py:99`
`resep` FK→`Resep` **`on_delete=CASCADE`** `related_name='item'` ⚠ ·
`bahan` FK→`master.Produk` **PROTECT** `related_name='dipakai_di_resep'` ·
`qty` Decimal(14,3) `MinValueValidator(0.001)`.
`Meta` `:109-117`:
- `UniqueConstraint(resep, bahan)` = `uq_resep_item_bahan`
- `CheckConstraint(qty > 0)` = `ck_resep_item_qty`

`clean()` `:122` melarang produk jadi bahannya sendiri.

### `SesiProduksi(DiauditModel)` — `produksi_sesi` — `produksi/models.py:138`
`grup_bahan` FK→`core.GrupBahan` **PROTECT** `related_name='sesi_produksi'` ·
`nomor`(32) `editable=False` · `tanggal` DateField default `localdate` `db_index=True` ·
`resep` FK→`Resep` **PROTECT** `related_name='sesi'` ·
`qty_target` Decimal(14,3) `MinValueValidator(0.001)` ·
`qty_hasil` Decimal(14,3) default 0 `editable=False` ·
`status`(10) choices `StatusSesi` `:131` default `DRAFT` `db_index=True` ·
`tangki_hasil` FK→`inventory.Tangki` null/blank **PROTECT** `related_name='sesi_hasil'` ·
`catatan` TextField blank.
`Meta` `:170-183`:
- `UniqueConstraint(grup_bahan, nomor)` = `uq_sesi_nomor`
- `CheckConstraint(qty_target > 0)` = `ck_sesi_target_positif`
- `Index(grup_bahan, status, -tanggal)` = `ix_sesi_grup_status`

Properties `susut` `:188`, `rendemen` `:192`.
**`save()` `:197`** — mengambil `entitas` pertama dalam grup
(`grup_bahan.entitas.order_by('kode').first()`) sebagai pemegang counter, lalu
`CounterDokumen.berikutnya()` (butuh atomic).
`delete()` `:207` hanya mengizinkan DRAFT.

### `SesiInput(models.Model)` — `produksi_sesi_input` — `produksi/models.py:213`
`sesi` FK→`SesiProduksi` **PROTECT** `related_name='input'` ·
`bahan` FK→`master.Produk` **PROTECT** `related_name='+'` ·
`qty_rencana` Decimal(14,3) default 0 · `qty_aktual` Decimal(14,3) default 0 ·
`tangki` FK→`inventory.Tangki` null/blank **PROTECT** `related_name='+'`.
`Meta` `:229-235`: `UniqueConstraint(sesi, bahan)` = `uq_sesi_input_bahan`.
`@property selisih` `:240`.

---

## 10. App `work_order`

### `WorkOrder(models.Model)` — `wo_work_order` — `work_order/models.py:5`
`nomor` CharField(50) **unique** `editable=False` · `judul`(255) ·
`deskripsi` TextField blank · `tanggal` DateField default `localdate` ·
`deadline` DateField null/blank · `selesai` Boolean default False ·
`catatan_selesai` TextField blank · `waktu_selesai` DateTime null/blank ·
`diselesaikan_oleh` FK→user null/blank **PROTECT** `related_name='wo_diselesaikan'` ·
`dibuat_oleh` FK→user **PROTECT** `related_name='wo_dibuat'` `editable=False` ·
`dibuat_pada` DateTime `auto_now_add`.
`Meta` `:26-28`: `db_table='wo_work_order'`, `ordering=['-dibuat_pada']`.
**Tidak ada constraint maupun index tambahan.**
`@property terlambat` `:33`.
**`save()` `:40`** — penomoran `WO/YYYY/MM/NNN` dengan
`filter(nomor__startswith=prefix).order_by('nomor').last()` — **tanpa lock dan
urut leksikografis** (lihat penanda).
> Tidak mewarisi `TimeStampedModel`/`DiauditModel`; punya `dibuat_oleh` sendiri.

### `WorkOrderPenugasan(models.Model)` — `wo_penugasan` — `work_order/models.py:53`
`work_order` FK→`WorkOrder` **`on_delete=CASCADE`** `related_name='penugasan'` ⚠ ·
`staff` FK→`staff_user.Profil` **`on_delete=CASCADE`** (tanpa related_name) ⚠.
`Meta` `:58-60`: `unique_together=('work_order','staff')` — bentuk lama, bukan
`UniqueConstraint` seperti model lain.

---

## 11. App `audit` — TIDAK TERPASANG

### `JejakAktivitas(models.Model)` — `audit_jejak_aktivitas` — `audit/models.py:46`
`waktu` DateTime auto_now_add db_index · `oleh` FK→user null/blank **PROTECT**
`related_name='jejak_aktivitas'` · `aksi`(12) choices `JenisAksi` `:30` db_index ·
`content_type` FK→`ContentType` **PROTECT** · `object_id` PositiveBigIntegerField ·
`objek` **GenericForeignKey** · `label_objek`(120) blank ·
`entitas` FK→`core.Entitas` null/blank **PROTECT** `related_name='jejak_aktivitas'` ·
`status_lama`/`status_baru`(32) blank · `alasan` TextField blank ·
`rincian` **JSONField** null/blank · `ip` GenericIPAddressField null/blank.
`Meta` `:87-98`: 4 index (`ix_jejak_objek`, `ix_jejak_oleh`, `ix_jejak_entitas`,
`ix_jejak_aksi`). `@property perpindahan` `:104`.
**`save()` `:111` menolak update; `delete()` `:116` raise.**

> **Tabelnya tidak akan pernah dibuat**: `audit` tidak ada di `INSTALLED_APPS`
> (`settings.py:75-96`), jadi `audit/migrations/0001_initial.py` tidak masuk
> graf migrasi. Model ini juga tidak terdaftar di app registry Django.

---

# PENANDA WAJIB

## A. FK tanpa index

**TIDAK ADA.** Diverifikasi: `grep db_index=False` di seluruh `*.py` → 0 hasil.
Django memberi `db_index=True` pada setiap `ForeignKey` secara default, dan
`OneToOneField` memakai `unique=True` (juga berindeks). Jadi setiap kolom FK
di 39 model punya indeks.

Yang **berlebihan** (indeks ganda pada kolom yang sama):

| Index | Lokasi | Alasan redundan |
|---|---|---|
| `ix_poitem_po` | `akunting/models/pembelian.py:202` | FK `purchase_order` sudah berindeks |
| `ix_penerimaan_tanggal` | `warehouse/models.py:72` | `tanggal` sudah `db_index=True` `:50` |
| `ix_penerimaan_selisih` | `warehouse/models.py:73` | `ada_selisih` sudah `db_index=True` `:58` |

Yang **kurang** (pola query yang sering dipakai tapi tidak berindeks komposit):

| Query | Lokasi pemakaian | Kolom yang di-scan |
|---|---|---|
| `MutasiStok.filter(idempotency_key=…)` | `inventory/services.py:181,270,291,416` | ✅ ada (unique) |
| `KartuHutang.filter(referensi=idem_key)` | `akunting/services.py:160` | ❌ **`referensi` tanpa index dan tanpa unique** — ini jalur idempotensi pembayaran |
| `PosisiKlaim.filter(grup_bahan_id=…)` | `inventory/services.py:466,530,544` | ✅ tercakup `uq_posisi_klaim(entitas, grup_bahan)`? **tidak** — kolom pertama unique index adalah `entitas`, jadi filter murni `grup_bahan` tidak terbantu |
| `LaporanSelisih.filter(penerimaan_id=…, resolusi=…, status=…)` | `warehouse/services.py:451-454` | hanya FK `penerimaan` yang berindeks |
| `PengeluaranKas.filter(entitas__kode=…)` | `keuangan/views.py:18` | join ke `core_entitas`; `PengeluaranKas` tanpa index tambahan |

## B. `on_delete=CASCADE` pada data akuntansi

4 CASCADE di seluruh proyek (dari 84 relasi; 80 sisanya `PROTECT`):

| Relasi | Lokasi | Risiko |
|---|---|---|
| `PurchaseOrderItem.purchase_order` → `PurchaseOrder` | `akunting/models/pembelian.py:158` | **DATA AKUNTANSI.** `PurchaseOrder.delete()` `:129` hanya mengizinkan status DRAFT, tapi `delete()` model **dilewati** oleh `QuerySet.delete()` (mis. bulk-delete di Django admin atau `PurchaseOrder.objects.filter(...).delete()`). Lewat jalur itu, PO berstatus SELESAI beserta seluruh itemnya bisa lenyap — sementara `PenerimaanItem.po_item` yang `PROTECT` akan memblokirnya **hanya jika** sudah ada penerimaan. PO TERKIRIM tanpa penerimaan tidak terlindungi. |
| `ResepItem.resep` → `Resep` | `produksi/models.py:100` | Resep yang belum dipakai sesi bisa dihapus beserta komposisinya. `SesiProduksi.resep` `PROTECT` melindungi resep yang sudah terpakai. Risiko rendah. |
| `WorkOrderPenugasan.work_order` → `WorkOrder` | `work_order/models.py:54` | `WorkOrder` **tidak** punya `delete()` override dan endpoint `DELETE /api/v1/work-order/{id}/` terbuka untuk semua pengguna login → penugasan ikut terhapus permanen. |
| `WorkOrderPenugasan.staff` → `Profil` | `work_order/models.py:56` | **Melanggar aturan yang ditulis di `staff_user/models.py:22-25`** ("semua model transaksional memakai PROTECT ke user"). `Profil.delete()` memang raise, tapi `Profil.objects.filter(...).delete()` melewatinya. |

## C. Field uang yang bukan Decimal

**TIDAK ADA.** `grep FloatField` → 0 hasil di seluruh repo.
Semua nilai rupiah `DecimalField`, semua kuantitas `DecimalField(14,3)`.

Catatan konsistensi (bukan bug, tapi menyimpang dari aturan di
`core/constants.py:1` "jangan tulis angka literal di model"):

| Model.field | Lokasi | Tertulis | Seharusnya |
|---|---|---|---|
| `Pelanggan.plafon_kredit` | `master/models.py:151` | `max_digits=18, decimal_places=2` | `NILAI_DIGITS, NILAI_PLACES` |
| `PengeluaranKas.nominal` | `keuangan/models.py:186` | `max_digits=18, decimal_places=2` | idem |
| `PenerimaanItem.qty_deklarasi` quantize | `warehouse/models.py:198` | `Decimal('0.001')` literal | konstanta `Q3` |
| `PurchaseOrderItem.amount` quantize | `akunting/models/pembelian.py:220` | `Decimal('0.01')` literal | konstanta `Q2` |

## D. Model tanpa penjaga integritas di level DB

| Invariant | Dijaga di | Tidak dijaga DB |
|---|---|---|
| `SUM(debit) = SUM(kredit)` per jurnal | ✅ **CONSTRAINT TRIGGER** `akunting/migrations/0004:46` | — |
| `sisa_hutang = total_tagihan − total_dibayar` | hanya Python `akunting/services.py:178-182` | ❌ |
| `SUM(SaldoEntitas.qty) = Stok.qty` (RAW/JADI) | hanya `verifikasi_kepemilikan()` `inventory/services.py:499` (manual) | ❌ |
| `SUM(PosisiKlaim.nilai_bersih) = nilai POOL` | hanya `verifikasi_pool_bersih()` `inventory/services.py:522` (manual) | ❌ |
| `PosisiKlaim = SUM(MutasiKlaim.nilai)` | hanya `verifikasi_posisi_cache()` `inventory/services.py:540` (manual) | ❌ |
| `RekeningBank.saldo = SUM(MutasiKas)` | hanya `catat_pengeluaran()` `keuangan/services.py:34` | ❌ (tidak ada verifikator sama sekali) |
| `SaldoEntitas` tidak boleh ada untuk lapis POOL | `clean()` `inventory/models.py:226` (**tidak dipanggil**) + cek Python `inventory/services.py:117` | ❌ |
| `KartuHutang.referensi` unik sebagai idempotency key | tidak ada | ❌ **kolom tidak unique** |

Tiga fungsi `verifikasi_*` didokumentasikan untuk "dijalankan nightly"
(`inventory/services.py:21`) tapi **tidak ada scheduler, cron, management
command, maupun task queue** di repo yang menjalankannya — satu-satunya jalan
adalah `GET /api/v1/inventory/verifikasi/` secara manual oleh Supervisor.

## E. Ringkasan tabel & ukuran skema

| App | Tabel | Constraint eksplisit | Index eksplisit |
|---|---|---|---|
| core | 4 | 3 | 1 |
| staff_user | 4 | 1 | 3 |
| master | 5 | 0 | 1 |
| dokumen | 1 | 0 | 2 |
| inventory | 7 | 9 | 3 |
| akunting | 9 | 14 | 8 |
| keuangan | 4 | 4 | 2 |
| warehouse | 4 | 8 | 3 |
| produksi | 4 | 6 | 1 |
| work_order | 2 | 1 (`unique_together`) | 0 |
| **audit** *(tidak terpasang)* | *(1)* | *(0)* | *(4)* |
| **Total aktif** | **44** | **46** | **24** |

Trigger DB: **1** (`trg_jurnal_seimbang`).
Data migration seed: **2** (`core/0003_seed_entitas.py` — 2 grup + 4 entitas;
`akunting/0005_seed_coa.py` — 21 akun).
