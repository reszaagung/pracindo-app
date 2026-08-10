# FASE 1 — PETA API

Ditelusuri dari `pracindo_erp/urls.py` → `include(<app>.urls)` → `DefaultRouter` →
ViewSet/APIView. Diverifikasi silang dengan resolver Django (`get_resolver()`
walk) dan dengan schema `drf-spectacular`.

## Konvensi yang berlaku untuk SEMUA endpoint

| Aspek | Nilai | Rujukan |
|---|---|---|
| Authentication | `staff_user.authentication.ExpiringTokenAuthentication` — TIDAK ADA satu pun view yang meng-override `authentication_classes` (grep: 0 hasil) | `settings.py:156-158`, `staff_user/authentication.py:24` |
| Permission default | `rest_framework.permissions.IsAuthenticated` — berlaku untuk view yang tidak menetapkan `permission_classes` | `settings.py:159-161` |
| Pagination | `PageNumberPagination`, `PAGE_SIZE=25` — TIDAK ADA `pagination_class` di view mana pun (grep: 0 hasil). Berlaku hanya untuk `list()` bawaan ModelViewSet; `@action` dan `list()` yang di-override mengembalikan array polos **tanpa paginasi**. | `settings.py:167-168` |
| Filter backend | `DjangoFilterBackend`, `SearchFilter` (`?search=`), `OrderingFilter` (`?ordering=`) — aktif di semua GenericAPIView | `settings.py:162-166` |
| Throttle | **TIDAK ADA** | grep `throttle` → 0 |
| Signal / task | **TIDAK ADA** | grep → 0 |

`DefaultRouter` juga membuat, untuk setiap prefix app:
`GET /api/v1/<app>/` (APIRootView) dan varian sufiks format
`…\.(?P<format>[a-z0-9]+)`. Keduanya tidak muncul di schema OpenAPI tapi
benar-benar terdaftar di URLconf.

---

## 1. `staff_user` — prefix `/api/v1/auth/`

| Method | Full path | View class:baris | Serializer in → out | permission_classes | Model / queryset | filter & search | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/api/v1/auth/daftar/` | `DaftarView` `staff_user/views.py:32` | `PendaftaranSerializer` `serializers.py:52` → dict manual | **`AllowAny`** `views.py:33` | `Profil` | — | — | 201 / 400 | `services.daftar()` `services.py:20` `@atomic` → INSERT `staff_user_profil`. role dipaksa STAFF, `is_active=False` |
| POST | `/api/v1/auth/register/` | idem (alias) `urls.py:20` | idem | **`AllowAny`** | idem | — | — | 201 / 400 | idem |
| POST | `/api/v1/auth/login/` | `LoginView` `views.py:60` | `LoginSerializer` `serializers.py:81` → dict `{token, profil, modul}` | **`AllowAny`** `views.py:61` | `Profil`, `Token`, `RiwayatAkses` | — | — | 200 / 401 / 403 | **WRITE walau gagal**: `services.catat_akses()` `services.py:206` INSERT `staff_user_riwayat_akses` (tanpa atomic, tanpa throttle); bila sukses `services.terbitkan_token()` `services.py:224` `@atomic` DELETE+INSERT `authtoken_token` |
| POST | `/api/v1/auth/logout/` | `LogoutView` `views.py:104` | — → — | `SudahLogin` | `Token` | — | — | 204 | DELETE token aktif (`views.py:109`), tanpa atomic (satu baris) |
| GET | `/api/v1/auth/portal/` | `PortalView` `views.py:113` | — → dict `{profil, modul, entitas}` | `SudahLogin` | `Profil`, `Entitas` | — | — | 200 | tidak ada |
| POST | `/api/v1/auth/ganti-password/` | `GantiPasswordView` `views.py:134` | `GantiPasswordSerializer` `serializers.py:107` → `{token, pesan}` | `SudahLogin` | `Profil`, `Token` | — | — | 200 / 400 | `services.ganti_password()` `services.py:167` `@atomic` → UPDATE password + DELETE semua token + INSERT token baru (2 tabel) |
| GET | `/api/v1/auth/profil/` | `ProfilViewSet` `views.py:147` | — → `ProfilSerializer` | `AksesModul` (modul `staff_user` → ADMIN/SUPERVISOR/superuser) | `Profil.objects.select_related(...)` | filterset `role,is_active,status_kerja,jabatan`; search `username,first_name,last_name,nip` | ✅ 25 | 200 | — |
| POST | `/api/v1/auth/profil/` | `views.py:147` (create bawaan) | `ProfilSerializer` `serializers.py:27` | `HanyaAdmin` `views.py:161-162` | `Profil` | — | — | 201 | INSERT `staff_user_profil` **lewat serializer, bukan service** — lihat §7 |
| GET/PUT/PATCH | `/api/v1/auth/profil/{id}/` | `views.py:147` | `ProfilSerializer` | `AksesModul` | `Profil` | — | — | 200 | UPDATE `staff_user_profil`; `role,is_active,nip,last_login,tanggal_keluar` read-only (`serializers.py:48`) |
| DELETE | `/api/v1/auth/profil/{id}/` | `perform_destroy` `views.py:165` | — | `HanyaAdmin` | `Profil` | — | — | **400** (bukan 405) | raise `DRFValidationError` |
| GET | `/api/v1/auth/profil/saya/` | `saya` `views.py:170` | — → `ProfilSerializer` | `SudahLogin` | `request.user` | — | ❌ | 200 | — |
| GET | `/api/v1/auth/profil/menunggu/` | `menunggu` `views.py:174` | — → `ProfilSerializer(many)` | `HanyaSupervisor` | `Profil.objects.menunggu_persetujuan()` `models.py:96` | — | ❌ tanpa paginasi | 200 | — |
| POST | `/api/v1/auth/profil/{id}/aktifkan/` | `aktifkan` `views.py:179` | `AktivasiSerializer` `serializers.py:86` → `ProfilSerializer` | `HanyaSupervisor` `views.py:158-160` | `Profil` | — | — | 200 / 400 | `services.aktifkan()` `services.py:44` `@atomic` `select_for_update` → UPDATE profil + SET M2M `entitas_diizinkan` (2 tabel) |
| POST | `/api/v1/auth/profil/{id}/tolak/` | `tolak` `views.py:197` | `PenolakanSerializer` → `ProfilSerializer` | `HanyaSupervisor` | `Profil` | — | — | 200 / 400 | `services.tolak()` `services.py:86` `@atomic` |
| POST | `/api/v1/auth/profil/{id}/ubah-role/` | `ubah_role` `views.py:208` | `UbahRoleSerializer` → `ProfilSerializer` | `HanyaSupervisor` | `Profil`, `Token` | — | — | 200 / 400 | `services.ubah_role()` `services.py:107` `@atomic` → UPDATE role + DELETE semua token (2 tabel) |
| POST | `/api/v1/auth/profil/{id}/nonaktifkan/` | `nonaktifkan` `views.py:221` | `NonaktifSerializer` → `ProfilSerializer` | `HanyaSupervisor` | `Profil`, `Token` | — | — | 200 / 400 | `services.nonaktifkan()` `services.py:130` `@atomic` (2 tabel) |
| POST | `/api/v1/auth/profil/{id}/aktifkan-kembali/` | `aktifkan_kembali` `views.py:235` | — → `ProfilSerializer` | `HanyaSupervisor` | `Profil` | — | — | 200 / 400 | `services.aktifkan_kembali()` `services.py:150` `@atomic` |
| POST | `/api/v1/auth/profil/{id}/reset-password/` | `reset_password` `views.py:243` | `ResetPasswordSerializer` → `{pesan}` | `HanyaSupervisor` | `Profil`, `Token` | — | — | 200 / 400 | `services.reset_password()` `services.py:188` `@atomic` (2 tabel) |
| GET/POST/PUT/PATCH/DELETE | `/api/v1/auth/jabatan/` `/{id}/` | `JabatanViewSet` `views.py:257` | `JabatanSerializer` | `AksesModul` (ADMIN) | `Jabatan.objects.all()` | filterset `departemen,aktif`; search `kode,nama` | ✅ 25 | 200/201/204 | CRUD penuh 1 tabel |
| GET/POST/PUT/PATCH/DELETE | `/api/v1/auth/kepegawaian/` `/{id}/` | `DataKepegawaianViewSet` `views.py:266` | `DataKepegawaianSerializer` `serializers.py:121` | **`[SudahLogin, DiriSendiriAtauSupervisor]`** `views.py:269` | `DataKepegawaian` — di-filter ke milik sendiri kecuali supervisor `views.py:271-275` | — | ✅ 25 | 200/201/204 | CRUD 1 tabel. `DiriSendiriAtauSupervisor` hanya punya `has_object_permission` (`permissions.py:159`) → **POST tidak dicek objek**; `profil` read-only (`serializers.py:134`) → POST selalu NOT NULL violation |
| GET | `/api/v1/auth/riwayat-akses/` `/{id}/` | `RiwayatAksesViewSet` `views.py:278` | `RiwayatAksesSerializer` | `HanyaSupervisor` | `RiwayatAkses` | filterset `berhasil,profil`; search `username_dicoba,ip` | ✅ 25 | 200 | — |

---

## 2. `master` — prefix `/api/v1/master/`

Basis: `BasisMaster` `master/views.py:16` — `modul='master'`,
`get_permissions()` `views.py:19-22`: GET/HEAD/OPTIONS → `SudahLogin`
(**setiap pengguna aktif, tanpa cek modul**), selain itu `HanyaAdmin`.

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter & search | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/master/produk/` | `ProdukViewSet` `master/views.py:35` | `ProdukSerializer` / `ProdukRingkasSerializer` bila `?ringkas=` (`views.py:43-46`) | `SudahLogin` | `Produk.objects.select_related('satuan').prefetch_related('suplier')` | filterset `jenis,aktif,suplier`; search `kode,nama` | ✅ 25 | 200 | — |
| POST | `/api/v1/master/produk/` | idem | `ProdukSerializer` | `AdminAtauAkunting` `views.py:48-51` | `Produk` | — | — | 201 | INSERT `master_produk` + M2M `suplier`. `Produk.save()` `master/models.py:121` memanggil `generate_kode_urut()` `master/utils.py:3` — **tanpa lock, urut leksikografis** |
| GET/PUT/PATCH | `/api/v1/master/produk/{id}/` | idem | `ProdukSerializer` | GET `SudahLogin` / write `AdminAtauAkunting` | `Produk` | — | — | 200 | UPDATE 1 tabel |
| DELETE | `/api/v1/master/produk/{id}/` | `perform_destroy` `views.py:24` | — | `AdminAtauAkunting` | — | — | — | **400** | raise `DRFValidationError` |
| GET | `/api/v1/master/suplier/` | `SuplierViewSet` `views.py:53` | `SuplierSerializer` / `SuplierRingkasSerializer` bila `?ringkas=` | `SudahLogin` | `Suplier.objects.order_by('nama')` | filterset `aktif`; search `kode,nama,npwp,kontak_nama` | ✅ 25 | 200 | — |
| POST/PUT/PATCH | `/api/v1/master/suplier/` `/{id}/` | idem | `SuplierSerializer` | `AdminAtauAkunting` `views.py:63-66` | `Suplier` | — | — | 201/200 | INSERT/UPDATE 1 tabel + `generate_kode_urut` |
| DELETE | `/api/v1/master/suplier/{id}/` | `perform_destroy` `views.py:24` | — | `AdminAtauAkunting` | — | — | — | **400** | — |

> **View terdefinisi tapi TIDAK terjangkau**: `SatuanViewSet` (`master/views.py:30`)
> dan `PelangganViewSet` (`master/views.py:68`) tidak didaftarkan ke router
> (`master/urls.py:10-13` hanya `produk` dan `suplier`). `KategoriSerializer`
> (`master/serializers.py:7`) tidak dipakai view mana pun. Model `Kategori`,
> `Satuan`, `Pelanggan` hanya bisa disentuh lewat Django admin.

---

## 3. `core` — prefix `/api/v1/core/`

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/core/entitas/` `/{id}/` | `EntitasViewSet` `core/views.py:28` | `EntitasSerializer` | `HanyaSupervisor` `views.py:32` | `Entitas.objects.select_related('grup_bahan')` | filterset `jenis,aktif`; search `kode,nama,npwp` | ✅ 25 | 200 | — |
| GET | `/api/v1/core/grup-bahan/` `/{id}/` | `GrupBahanViewSet` `views.py:37` | `GrupBahanSerializer` | `HanyaSupervisor` `views.py:41` | `GrupBahan` | search `kode,nama` | ✅ 25 | 200 | — |
| GET | `/api/v1/core/periode/` `/{id}/` | `PeriodeAkuntansiViewSet` `views.py:45` | `PeriodeAkuntansiSerializer` | **`SudahLogin`** `views.py:56` | `PeriodeAkuntansi.objects.select_related(...)` | filterset `entitas,tahun,bulan,ditutup` | ✅ 25 | 200 | — |
| GET | `/api/v1/core/periode/status/` | `status` `views.py:58` | query `?entitas=&tanggal=` → dict | **`SudahLogin`** | `PeriodeAkuntansi` | — | ❌ | 200 / 400 | read-only, `services.pastikan_periode_terbuka()` `core/services.py:22` |
| POST | `/api/v1/core/periode/tutup/` | `tutup` `views.py:90` | `TutupPeriodeSerializer` `core/serializers.py:40` → `PeriodeAkuntansiSerializer` | `HanyaSupervisor` `views.py:54-55` | `PeriodeAkuntansi` | — | — | 200 / 400 | `services.tutup_periode()` `core/services.py:44` `@atomic` + `select_for_update` → `get_or_create` + UPDATE (1 tabel) |
| POST | `/api/v1/core/periode/buka/` | `buka` `views.py:106` | `BukaPeriodeSerializer` `core/serializers.py:46` → `PeriodeAkuntansiSerializer` | `HanyaSupervisor` | `PeriodeAkuntansi` | — | — | 200 / 400 | `services.buka_periode()` `core/services.py:63` `@atomic` + `select_for_update`; `.get()` tanpa guard → `DoesNotExist` = 500 |

---

## 4. `inventory` — prefix `/api/v1/inventory/`

`GudangProduksi = PunyaRole.dengan(Role.GUDANG, Role.PRODUKSI)` — `inventory/views.py:36`.
Catatan: `PunyaRole.has_permission` memakai `punya_role()` (`staff_user/models.py:196`)
yang hanya meloloskan `is_superuser` atau role yang persis cocok — **role
SUPERVISOR TIDAK lolos** `GudangProduksi` kecuali dia juga superuser.

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/inventory/stok/` | `StokViewSet` `inventory/views.py:48` | out: `StokGudangSerializer`, atau `StokAkuntingSerializer` bila `?sisi=akunting` DAN user boleh modul akunting (`views.py:66-75`) | `AksesModul` (inventory → GUDANG/PRODUKSI/AKUNTING) | `Stok.objects.select_related(...)`, filter manual `?lapis&?grup&?produk` di `get_queryset` `views.py:52-64` | manual (bukan filterset) | ✅ 25 | 200 | — |
| GET | `/api/v1/inventory/stok/{id}/` | idem | `StokGudangDetailSerializer` / `StokAkuntingDetailSerializer` | `AksesModul` | + `prefetch_related('kepemilikan__entitas')` | — | — | 200 | — |
| GET | `/api/v1/inventory/tangki/` `/{id}/` | `TangkiViewSet` `views.py:82` | `TangkiSerializer` | `AksesModul` | `Tangki.objects.select_related(...)` | filterset `grup_bahan,aktif` | ✅ 25 | 200 | — |
| GET | `/api/v1/inventory/mutasi/` `/{id}/` | `MutasiStokViewSet` `views.py:95` | `MutasiStokSerializer` | `AksesModul` | `MutasiStok.objects.select_related('stok__produk')` | filterset `stok,jenis` | ✅ 25 | 200 | — |
| GET | `/api/v1/inventory/posisi-klaim/` | `PosisiKlaimViewSet.list` `views.py:116` | — → **list dict mentah** dari `services.posisi_grup()` `services.py:451` (serializer diabaikan) | `AksesModul` | `PosisiKlaim` | wajib `?grup=` | ❌ tanpa paginasi | 200 / 400 | — |
| GET | `/api/v1/inventory/posisi-klaim/{id}/` | `views.py:108` | `PosisiKlaimSerializer` | `AksesModul` | `PosisiKlaim` | — | — | 200 | — |
| GET | `/api/v1/inventory/nilai-ekuivalen/` `/{id}/` | `NilaiEkuivalenViewSet` `views.py:128` | `NilaiEkuivalenSerializer` | `AksesModul` | `NilaiEkuivalen` | filterset `produk` | ✅ 25 | 200 | — |
| GET | `/api/v1/inventory/isi-pool/` | `IsiPoolView` `views.py:141` | query `?grup=&tanggal=` → `{produk, total_nilai}` | `AksesModul` | `Stok` (POOL) + `NilaiEkuivalen` | — | ❌ | 200 / 400 | read-only |
| POST | `/api/v1/inventory/setor-ke-pool/` | `SetorKePoolView` `views.py:160` | `SetorKePoolSerializer` `serializers.py:196` → 4 objek | **`GudangProduksi`** (tanpa atribut `modul`) | banyak | — | — | 201 / 400 | `services.setor_ke_pool()` `inventory/services.py:204` **`@atomic`** → `inventory_stok`×2, `inventory_mutasi_stok`×2, `inventory_saldo_entitas`, `inventory_mutasi_klaim`, `inventory_posisi_klaim`, `inventory_tangki`×2 (hingga **9 tabel**) |
| POST | `/api/v1/inventory/klaim-hasil/` | `KlaimHasilView` `views.py:182` | `KlaimHasilSerializer` `serializers.py:208` → 4 objek | **`GudangProduksi`** | banyak | — | — | 201 / 400 | `services.klaim_hasil()` `inventory/services.py:309` **`@atomic`**, 8 tabel |
| POST | `/api/v1/inventory/opname/` | `OpnameView` `views.py:208` | `OpnameSerializer` `serializers.py:221` → `MutasiStokSerializer` | `HanyaSupervisor` | `Stok`,`MutasiStok`,`SaldoEntitas`,`Tangki` | — | — | 201 / 400 | `services.sesuaikan_stok()` `inventory/services.py:401` **`@atomic`**, 4 tabel |
| GET | `/api/v1/inventory/verifikasi/` | `VerifikasiView` `views.py:234` | query `?grup=` → dict 3 bagian | `HanyaSupervisor` | seluruh `Stok`/`PosisiKlaim` | — | ❌ | 200 | read-only, **N+1 berat** (lihat FASE 3) |

> `NilaiEkuivalen` tidak punya endpoint tulis sama sekali. Tarif hanya bisa
> dibuat lewat Django admin (`inventory/admin.py:58`), padahal
> `_catat_klaim()` (`inventory/services.py:142`) gagal keras bila tarif belum ada.

---

## 5. `akunting` — prefix `/api/v1/akunting/`

`BasisAkunting` `akunting/views.py:40` — `modul='akunting'`, `AksesModul`,
plus helper `filter_entitas()` `views.py:44-49` (dipakai HANYA oleh
`PurchaseOrderViewSet.get_queryset`, `outstanding`, dan
`FakturPembelianViewSet.get_queryset`).

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter & search | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/akunting/akun/` `/{id}/` | `AkunViewSet` `views.py:56` | `AkunSerializer` | `AksesModul` (akunting) | `Akun.objects.select_related('parent')` | filterset `tipe,boleh_diposting,aktif`; search `kode,nama` | ✅ 25 | 200 | — |
| GET | `/api/v1/akunting/jurnal/` `/{id}/` | `JurnalUmumViewSet` `views.py:69` | `JurnalUmumSerializer` (nested `baris`) | `AksesModul` | `JurnalUmum` + `prefetch('baris__akun')`, di-filter `entitas_diizinkan` `views.py:87-89` | filterset `entitas,kejadian,tanggal`; search `nomor,referensi,keterangan` | ✅ 25 | 200 | — |
| POST | `/api/v1/akunting/jurnal/{id}/balik/` | `balik` `views.py:91` | `JurnalBalikSerializer` `serializers.py:67` → `JurnalUmumSerializer` | `PunyaRole.dengan(SUPERVISOR)` `views.py:92` | `JurnalUmum`,`JurnalDetail`,`CounterDokumen` | — | — | 201 / 400 | `services.jurnal_balik()` `akunting/services.py:114` **`@atomic`** + `select_for_update` → INSERT jurnal + `bulk_create` detail + UPDATE `dibalik_oleh` + UPDATE counter (**4 tabel**) |
| GET | `/api/v1/akunting/purchase-order/` | `PurchaseOrderViewSet` `views.py:112` | `PurchaseOrderListSerializer` | `AksesModul` | `.dengan_total()` + `filter_entitas` | filterset `entitas,suplier,status,tanggal`; search `no_po,suplier__nama` | ✅ 25 | 200 | — |
| GET | `…/purchase-order/{id}/` | idem | `PurchaseOrderSerializer` (nested item) | `AksesModul` | idem | — | — | 200 | — |
| POST | `/api/v1/akunting/purchase-order/` | `create` `views.py:134` | `BuatPOSerializer` `serializers.py:133` → `PurchaseOrderSerializer` | `AksesModul` + cek `bisa_akses_entitas` `views.py:138` | — | — | — | 201 / 400 / 403 | `services.buat_po()` `akunting/services.py:281` **`@atomic`** → `core_counter_dokumen`, `akunting_purchase_order`, N× `akunting_purchase_order_item` (**3 tabel**) |
| PUT/PATCH | `…/purchase-order/{id}/` | `update` `views.py:148` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| DELETE | `…/purchase-order/{id}/` | `destroy` `views.py:156` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| GET | `…/purchase-order/preview-nomor/` | `preview_nomor` `views.py:162` | query `?entitas=&tanggal=` → `{nomor, catatan}` | `AksesModul` | `Entitas`,`CounterDokumen` | wajib `?entitas` | ❌ | 200 / 400 | read-only (`CounterDokumen.preview` `core/models.py:203` tidak menaikkan counter). `Entitas.objects.get()` tanpa guard + `fromisoformat()` tanpa guard → **500** untuk input salah |
| GET | `…/purchase-order/outstanding/` | `outstanding` `views.py:178` | — → `PurchaseOrderListSerializer(many)` | `AksesModul` | `PurchaseOrder.objects.terbuka()` + `filter_entitas` | — | ❌ tanpa paginasi | 200 | — |
| POST | `…/purchase-order/{id}/ubah-item/` | `ubah_item` `views.py:188` | `UbahItemPOSerializer` `serializers.py:142` → `PurchaseOrderSerializer` | `AksesModul` | — | — | — | 200 / 400 | `services.ubah_item_po()` `akunting/services.py:332` **`@atomic`** + `select_for_update` → DELETE semua item + INSERT ulang (1 tabel) |
| POST | `…/purchase-order/{id}/kirim/` | `kirim` `views.py:198` | — → `PurchaseOrderSerializer` | `AksesModul` | — | — | — | 200 / 400 | `services.kirim_po()` `akunting/services.py:362` **`@atomic`** + `select_for_update` |
| POST | `…/purchase-order/{id}/batalkan/` | `batalkan` `views.py:206` | `BatalPOSerializer` → `PurchaseOrderSerializer` | `AksesModul` | — | — | — | 200 / 400 | `services.batalkan_po()` `akunting/services.py:378` **`@atomic`** |
| GET | `…/purchase-order/{id}/ringkasan/` | `ringkasan` `views.py:217` | — → dict | `AksesModul` | `PurchaseOrder` + prefetch | — | ❌ | 200 | read-only. **`filter_entitas` TIDAK diterapkan** → lintas entitas terbaca; `.get()` tanpa guard → 500 |
| GET | `/api/v1/akunting/faktur/` | `FakturPembelianViewSet` `views.py:226` | `FakturListSerializer` | `AksesModul` | `FakturPembelian` + `filter_entitas` | filterset `entitas,suplier,status,jenis,tanggal_jatuh_tempo`; search `nomor_faktur,no_internal,suplier__nama` | ✅ 25 | 200 | — |
| GET | `…/faktur/{id}/` | idem | `FakturPembelianSerializer` (nested `mutasi`) | `AksesModul` | idem | — | — | 200 | — |
| POST | `/api/v1/akunting/faktur/` | `create` `views.py:244` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| PUT/PATCH/DELETE | `…/faktur/{id}/` | `views.py:251,260` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| GET | `…/faktur/draft-dari-penerimaan/{penerimaan_id}/` | `draft_dari_penerimaan` `views.py:264` | — → dict usulan | `AksesModul` | `PenerimaanBarang`,`LaporanSelisih` | — | ❌ | 200 / 400 | read-only (`services.draft_faktur()` `akunting/services.py:490`). `.get()` tanpa guard → 500 |
| POST | `…/faktur/dari-penerimaan/{penerimaan_id}/` | `dari_penerimaan` `views.py:276` | `TerbitkanFakturSerializer` `serializers.py:195` → `{faktur, rincian}` | `AksesModul` + cek supervisor untuk `abaikan_klaim_terbuka` `views.py:283` | banyak | — | — | 201 / 400 / 403 | `services.terbitkan_faktur()` `akunting/services.py:531` **`@atomic`** + `select_for_update` → `core_counter_dokumen`, `akunting_faktur_pembelian`, `akunting_kartu_hutang`, `akunting_jurnal_umum`×(1–2), `akunting_jurnal_detail` (**6 tabel**) |
| GET | `…/faktur/jatuh-tempo/` | `jatuh_tempo` `views.py:301` | query `?entitas=&sampai=` → `FakturListSerializer(many)` | `AksesModul` | `services.faktur_jatuh_tempo()` `akunting/services.py:242` | wajib `?entitas` | ❌ tanpa paginasi | 200 / 400 | read-only; **tanpa cek `bisa_akses_entitas`** |
| GET | `…/faktur/aging/` | `aging` `views.py:315` | query `?entitas=` → list dict | `AksesModul` | `services.aging_hutang()` `akunting/services.py:643` | wajib `?entitas` | ❌ | 200 / 400 | read-only, satu query agregat |
| POST | `/api/v1/akunting/pembayaran/` | `PembayaranView.create` `views.py:328` (`viewsets.ViewSet`) | `BayarSerializer` `serializers.py:208` → `{alokasi, uang_muka}` | `AksesModul` dengan **`modul='keuangan'`** `views.py:335` + `bisa_akses_entitas` `views.py:342` | banyak | — | — | 201 / 400 / 403 | `services.alokasi_pembayaran()` `akunting/services.py:186` **`@atomic`** + `select_for_update` → N× `akunting_kartu_hutang`, N× UPDATE `akunting_faktur_pembelian`, `akunting_uang_muka_suplier`, `akunting_jurnal_umum`, `akunting_jurnal_detail`, `core_counter_dokumen` (**6 tabel**). `idem_key` = `uuid4()` baru tiap request (`views.py:348`) |
| GET | `/api/v1/akunting/uang-muka/` `/{id}/` | `UangMukaViewSet` `views.py:359` | `UangMukaSerializer` | `AksesModul` (`modul='keuangan'`) | `UangMukaSuplier.objects.select_related(...)` | filterset `entitas,suplier` | ✅ 25 | 200 | — **tanpa `filter_entitas`** |

---

## 6. `keuangan` — prefix `/api/v1/keuangan/`

| Method | Full path | View class:baris | Serializer in/out | permission_classes | Model / queryset | filter | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/keuangan/pengeluaran/` | `PengeluaranViewSet` `keuangan/views.py:10` | `PengeluaranKasSerializer` `serializers.py:4` | **TIDAK ADA → default `IsAuthenticated`** | `PengeluaranKas.objects.select_related('entitas','mutasi')`, filter manual `?entitas=<kode>` `views.py:14-19` | manual | ✅ 25 | 200 | — |
| POST | `/api/v1/keuangan/pengeluaran/` | `create` `views.py:21` | **tanpa serializer** — baca `request.data` mentah `views.py:23-33` | **`IsAuthenticated`** | banyak | — | — | 201 / 400 | `services.catat_pengeluaran()` `keuangan/services.py:9` **`@atomic`** + `select_for_update` → `keuangan_pengeluaran_kas`, UPDATE `keuangan_rekening_bank`, `keuangan_mutasi_kas`, `akunting_jurnal_umum`, `akunting_jurnal_detail`, `core_counter_dokumen` (**6 tabel**) |
| GET | `…/pengeluaran/{id}/` | idem | `PengeluaranKasSerializer` | **`IsAuthenticated`** | — | — | — | 200 | — |
| PUT/PATCH | `…/pengeluaran/{id}/` | **default ModelViewSet, tidak di-override** | `PengeluaranKasSerializer` (writable: `kategori`, `pemohon`, `nominal`, `bukti_nota`) | **`IsAuthenticated`** | `PengeluaranKas` | — | — | 200 | UPDATE `keuangan_pengeluaran_kas` **tanpa menyentuh `MutasiKas`, saldo rekening, maupun jurnal** |
| DELETE | `…/pengeluaran/{id}/` | **default ModelViewSet, tidak di-override** | — | **`IsAuthenticated`** | `PengeluaranKas` | — | — | 204 | DELETE baris pengeluaran; `MutasiKas` + jurnal tetap ada (yatim) |
| GET | `…/pengeluaran/dashboard-summary/` | `dashboard_summary` `views.py:39` | query `?entitas=<kode>` (default `'PT'`) → dict | **`IsAuthenticated`** | `RekeningBank`,`PengeluaranKas` | — | ❌ | 200 | read-only. `total_pemasukan` hardcode `0` `views.py:49` |

> Model `RekeningBank`, `MutasiKas`, `RencanaBayar` (`keuangan/models.py:32,69,128`)
> **tidak punya endpoint API sama sekali** — hanya bisa dikelola lewat Django
> admin (`keuangan/admin.py`).

---

## 7. `warehouse` — prefix `/api/v1/warehouse/`

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter & search | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/warehouse/po-siap-terima/` `/{id}/` | `POSiapTerimaViewSet` `warehouse/views.py:42` | `POGudangSerializer` (**tanpa harga**) | `AksesModul` (warehouse → GUDANG) | `PurchaseOrder.objects.terbuka()` + prefetch item | filterset `suplier,entitas`; search `no_po,suplier__nama` | ✅ 25 | 200 | — |
| GET | `/api/v1/warehouse/penerimaan/` | `PenerimaanViewSet` `views.py:69` | `PenerimaanListSerializer` | `AksesModul` | `PenerimaanBarang` + prefetch | filterset `purchase_order,ada_selisih,tanggal`; search `nomor,no_surat_jalan,purchase_order__no_po` | ✅ 25 | 200 | — |
| GET | `…/penerimaan/{id}/` | idem | `PenerimaanBarangSerializer` (nested item + laporan) | `AksesModul` | idem | — | — | 200 | — |
| POST | `/api/v1/warehouse/penerimaan/` | `create` `views.py:87` | `TerimaBarangSerializer` `serializers.py:156` → `{penerimaan, laporan_selisih, pesan}` | `AksesModul` | banyak | — | — | 201 / 400 | `services.terima_barang()` `warehouse/services.py:51` **`@atomic`** + `select_for_update` → `core_counter_dokumen`, `warehouse_penerimaan_barang`, N× `warehouse_penerimaan_item`, UPDATE `akunting_purchase_order_item`, `inventory_stok`, `inventory_mutasi_stok`, `inventory_saldo_entitas`, `warehouse_laporan_selisih`, UPDATE `akunting_purchase_order`, `akunting_jurnal_umum`, `akunting_jurnal_detail` (**11 tabel dalam satu transaksi**) |
| PUT/PATCH/DELETE | `…/penerimaan/{id}/` | `views.py:120,129` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| GET | `…/penerimaan/{id}/ringkasan/` | `ringkasan` `views.py:135` | — → dict | `AksesModul` | `PenerimaanBarang` + prefetch | — | ❌ | 200 | read-only. `.get()` tanpa guard → 500 |
| GET | `/api/v1/warehouse/laporan-selisih/` `/{id}/` | `LaporanSelisihViewSet` `views.py:144` | `LaporanSelisihGudangSerializer`, atau `LaporanSelisihAkuntingSerializer` bila `?sisi=akunting` DAN boleh modul akunting (`views.py:163-170`) | `AksesModul` (warehouse) | `LaporanSelisih` + select_related | filterset `penerimaan,jenis,status,resolusi`; search `nomor,uraian,penerimaan__nomor` | ✅ 25 | 200 | — |
| POST | `/api/v1/warehouse/laporan-selisih/` | `create` `views.py:172` | `LaporanManualSerializer` `serializers.py:186` → `LaporanSelisihGudangSerializer` | `AksesModul` | — | — | — | 201 / 400 | `services.laporan_manual()` `warehouse/services.py:300` **`@atomic`** → `core_counter_dokumen`, `warehouse_laporan_selisih`, UPDATE `warehouse_penerimaan_barang` (**3 tabel**) |
| PUT/PATCH/DELETE | `…/laporan-selisih/{id}/` | `views.py:183,192` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| GET | `…/laporan-selisih/terbuka/` | `terbuka` `views.py:196` | query `?suplier=&entitas=` → serializer(many) | `AksesModul` | `services.klaim_belum_diselesaikan()` `warehouse/services.py:426` | — | ❌ tanpa paginasi | 200 | — |
| POST | `…/laporan-selisih/{id}/ajukan/` | `ajukan` `views.py:210` | — → `LaporanSelisihGudangSerializer` | `AksesModul` | — | — | — | 200 / 400 | `services.ajukan_ke_suplier()` `warehouse/services.py:325` **`@atomic`** + `select_for_update` |
| POST | `…/laporan-selisih/{id}/selesaikan/` | `selesaikan` `views.py:218` | `SelesaikanSelisihSerializer` `serializers.py:195` → `LaporanSelisihAkuntingSerializer` | `AksesModul` **+ cek `bisa_akses_modul('akunting')`** `views.py:224` | — | — | — | 200 / 400 / 403 | `services.selesaikan_laporan()` `warehouse/services.py:335` **`@atomic`** → UPDATE `warehouse_laporan_selisih` + kemungkinan UPDATE `akunting_purchase_order` (2 tabel) |
| POST | `…/laporan-selisih/{id}/tutup/` | `tutup` `views.py:239` | `TutupSelisihSerializer` → `LaporanSelisihAkuntingSerializer` | `AksesModul` + cek akunting `views.py:241` | — | — | — | 200 / 400 / 403 | `services.tutup_laporan()` `warehouse/services.py:403` **`@atomic`** |
| GET/POST/PUT/PATCH/DELETE | `/api/v1/warehouse/packaging/` `/{id}/` | `PackagingViewSet` `views.py:256` | `PackagingSerializer` `serializers.py:207` | `AksesModul` (warehouse) | `Packaging.objects.select_related(...)` | filterset `produk,grup_bahan,tanggal` | ✅ 25 | 200/201/204 | CRUD polos 1 tabel — **tidak menyentuh stok sama sekali** meski merepresentasikan curah→kemasan |

---

## 8. `produksi` — prefix `/api/v1/produksi/`

| Method | Full path | View class:baris | Serializer in/out | permission | Model / queryset | filter | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/produksi/sesi/` | `SesiViewSet` `produksi/views.py:15` | `SesiListSerializer` `serializers.py:4` | `AksesModul` (produksi) | `SesiProduksi.objects.select_related(...)` | **tidak ada filterset/search** | ✅ 25 | 200 | — |
| GET | `…/sesi/{id}/` | `retrieve` `views.py:28` | — → dict `services.ringkasan_sesi()` (serializer diabaikan) | `AksesModul` | `SesiProduksi` + prefetch | — | — | 200 | — |
| POST | `/api/v1/produksi/sesi/` | `create` `views.py:45` | `BuatSesiSerializer` `serializers.py:37` → `{id, nomor}` | `AksesModul` | — | — | — | 201 / 400 | `services.buat_sesi()` `produksi/services.py:99` **`@atomic`** → `core_counter_dokumen`, `produksi_sesi`, N× `produksi_sesi_input` (**3 tabel**) |
| PUT/PATCH | `…/sesi/{id}/` | `update` `views.py:33` | — | `AksesModul` | — | — | — | **405** (`MethodNotAllowed`) | tidak ada |
| DELETE | `…/sesi/{id}/` | `destroy` `views.py:39` | — | `AksesModul` | — | — | — | **405** | tidak ada |
| POST | `…/sesi/{id}/mulai/` | `mulai` `views.py:57` | `MulaiSesiSerializer` `serializers.py:50` → dict ringkasan | `AksesModul` | — | — | — | 200 / 400 | **`SesiInput.objects.filter(...).update(tangki_id=…)` di `views.py:70` berjalan DI LUAR blok atomic** apa pun, lalu `services.mulai_sesi()` `produksi/services.py:131` **`@atomic`** + `select_for_update` → UPDATE `produksi_sesi_input`, N× (`inventory_stok`, `inventory_mutasi_stok`, `inventory_tangki`), UPDATE `produksi_sesi` |
| POST | `…/sesi/{id}/selesaikan/` | `selesaikan` `views.py:78` | `SelesaikanSesiSerializer` → dict | `AksesModul` | — | — | — | 200 / 400 | `services.selesaikan_sesi()` `produksi/services.py:165` **`@atomic`** → `inventory_stok`, `inventory_mutasi_stok`, `inventory_tangki`, `produksi_sesi` (**4 tabel**) |
| POST | `…/sesi/{id}/batalkan/` | `batalkan` `views.py:89` | `BatalSesiSerializer` → dict | `AksesModul` | — | — | — | 200 / 400 | `services.batalkan_sesi()` `produksi/services.py:207` **`@atomic`** |

> `Resep` dan `ResepItem` (`produksi/models.py:34,99`) tidak punya endpoint apa
> pun, padahal `buat_sesi()` gagal keras bila resep aktif belum ada
> (`Resep.berlaku()` `produksi/models.py:74`). Hanya bisa lewat Django admin.

---

## 9. `work_order` — prefix `/api/v1/work-order/`

Router didaftarkan dengan prefix kosong (`work_order/urls.py:8`), jadi path
list-nya persis `/api/v1/work-order/`.

| Method | Full path | View class:baris | Serializer in/out | permission_classes | Model / queryset | filter | pagination | status | efek samping |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/work-order/` | `WorkOrderViewSet` `work_order/views.py:11` | `WorkOrderSerializer` | **`IsAuthenticated`** `views.py:14` | `WorkOrder.objects.all()` | **tidak ada** | ✅ 25 | 200 | — |
| POST | `/api/v1/work-order/` | `create` bawaan + `perform_create` `views.py:16` | `WorkOrderSerializer` `serializers.py:17` | **`IsAuthenticated`** | `WorkOrder`,`WorkOrderPenugasan` | — | — | 201 | `WorkOrderSerializer.create()` `serializers.py:36` → INSERT `wo_work_order` + N× `wo_penugasan` — **TANPA `transaction.atomic`** |
| GET | `…/work-order/{id}/` | idem | `WorkOrderSerializer` | **`IsAuthenticated`** | — | — | — | 200 | — |
| PUT/PATCH | `…/work-order/{id}/` | default ModelViewSet | `WorkOrderSerializer` | **`IsAuthenticated`** | — | — | — | 200 | UPDATE `wo_work_order`; `staff_ids` diterima tapi **diabaikan diam-diam** (bukan field model, `ModelSerializer.update` hanya `setattr`) |
| DELETE | `…/work-order/{id}/` | default ModelViewSet | — | **`IsAuthenticated`** | — | — | — | 204 | DELETE `wo_work_order` + CASCADE `wo_penugasan` |
| GET | `…/work-order/mading/` | `mading` `views.py:19` | — → `WorkOrderSerializer(many)` | **`IsAuthenticated`** | `WorkOrder` filter `penugasan__staff_id` | — | ❌ | 200 | read-only. `getattr(request.user,'profil_staff_id',None)` `views.py:25` — atribut itu **tidak ada** di `Profil` → selalu `None` → **selalu mengembalikan `[]`** |
| GET | `…/work-order/staff/` | `staff` `views.py:38` | — → `ProfilStaffRingkasSerializer(many)` | **`IsAuthenticated`** | `Profil.objects.aktif()` | — | ❌ | 200 | read-only — daftar seluruh pegawai aktif terbuka untuk setiap pengguna yang login |
| POST | `…/work-order/{id}/approve/` | `approve` `views.py:44` | `request.data['catatan']` mentah → `{detail}` | **`IsAuthenticated`** | `WorkOrder` | — | — | 200 / 400 / 403 | UPDATE `wo_work_order` (`selesai`,`waktu_selesai`,`diselesaikan_oleh`,`catatan_selesai`). `profil_staff_id` sama-sama `None` → cek `views.py:55` **selalu 403** |

---

## 10. App tanpa endpoint

| App | Alasan | Rujukan |
|---|---|---|
| `dokumen` | `urlpatterns = []`; `views.py` masih scaffold | `dokumen/urls.py:5-6`, `dokumen/views.py:1-3` |
| `pajak` | `urlpatterns = []`; tidak ada model | `pajak/urls.py:5-6` |
| `sales_order` | `urlpatterns = []`; tidak ada model | `sales_order/urls.py:5-6` |
| `logistik` | `urlpatterns = []`; tidak ada model | `logistik/urls.py:5-6` |
| `audit` | punya `urls.py` lengkap tapi **tidak di-include** di root, dan app tidak di INSTALLED_APPS | `audit/urls.py:11`, `pracindo_erp/urls.py:7-27`, `settings.py:75-96` |

---

# TANDA WAJIB

## A. Endpoint dengan `permission_classes` kosong / `AllowAny`

| Endpoint | Lokasi | Keterangan |
|---|---|---|
| `POST /api/v1/auth/daftar/` | `staff_user/views.py:33` | `AllowAny` — memang harus publik (pendaftaran). Menulis 1 baris `Profil` per request, **tanpa throttle & tanpa CAPTCHA** |
| `POST /api/v1/auth/register/` | `staff_user/urls.py:20` | alias dari yang sama |
| `POST /api/v1/auth/login/` | `staff_user/views.py:61` | `AllowAny` — harus publik. **Menulis baris `RiwayatAkses` untuk SETIAP percobaan, termasuk yang gagal, tanpa throttle** |
| semua endpoint `keuangan` | `keuangan/views.py:10` | `permission_classes` **tidak diset** → jatuh ke `IsAuthenticated`. Tidak ada `modul`, tidak ada `AksesModul` |
| semua endpoint `work_order` | `work_order/views.py:14` | `IsAuthenticated` eksplisit — semua role, termasuk `STAFF`, punya CRUD penuh |
| `GET /api/v1/master/produk|suplier/` | `master/views.py:20-21` | `SudahLogin` untuk metode aman — sengaja, tapi berarti **tanpa cek modul `master`** |
| `GET /api/v1/core/periode/`, `/status/` | `core/views.py:56` | `SudahLogin` |
| `GET /api/schema/`, `GET /api/docs/` | `pracindo_erp/urls.py:12-13` | tidak di-override → `IsAuthenticated` (default) |

## B. Endpoint WRITE tanpa pemeriksaan izin yang memadai

| Method + path | Lokasi | Masalah |
|---|---|---|
| `POST /api/v1/keuangan/pengeluaran/` | `keuangan/views.py:21` | Hanya `IsAuthenticated`. Setiap pengguna login berperan apa pun bisa mengeluarkan kas, memotong saldo rekening, dan **memposting jurnal `BEBAN_KAS`** |
| `PUT/PATCH /api/v1/keuangan/pengeluaran/{id}/` | tidak di-override | `nominal` bisa diubah **tanpa** menyentuh `MutasiKas`, saldo rekening, maupun jurnal |
| `DELETE /api/v1/keuangan/pengeluaran/{id}/` | tidak di-override | baris pengeluaran hilang, `MutasiKas` + jurnal tetap ada |
| `POST/PUT/PATCH/DELETE /api/v1/work-order/…` | `work_order/views.py:14` | siapa pun yang login bisa membuat, mengubah, dan menghapus tugas milik orang lain |
| `POST /api/v1/auth/kepegawaian/` | `staff_user/views.py:269` | `DiriSendiriAtauSupervisor` hanya punya `has_object_permission` (`staff_user/permissions.py:159`) — tidak berlaku untuk `create` |
| `POST …/faktur/dari-penerimaan/{id}/` | `akunting/views.py:276` | tidak ada `bisa_akses_entitas` (bandingkan `PurchaseOrderViewSet.create` `views.py:138` dan `PembayaranView.create` `views.py:342` yang punya) |
| `POST /api/v1/warehouse/penerimaan/` | `warehouse/views.py:87` | tidak ada `bisa_akses_entitas`; entitas diturunkan dari PO yang dipilih klien |
| `POST /api/v1/inventory/setor-ke-pool/`, `/klaim-hasil/` | `inventory/views.py:161,183` | `GudangProduksi` tanpa cek `bisa_akses_entitas` — `entitas_id` datang langsung dari payload |
| `POST /api/v1/produksi/sesi/…` | `produksi/views.py:16` | `AksesModul` saja; `grup_bahan_id` dari payload tanpa pembatasan |

## C. Endpoint yang menulis >1 tabel TANPA `transaction.atomic`

| Endpoint | Lokasi | Tabel yang tersentuh | Akibat kalau gagal di tengah |
|---|---|---|---|
| `POST /api/v1/work-order/` | `work_order/serializers.py:36-43` | `wo_work_order` + N× `wo_penugasan` | `staff_id` tak sahih → `IntegrityError` setelah `WorkOrder` tersimpan → WO yatim tanpa penugasan |
| `POST /api/v1/produksi/sesi/{id}/mulai/` | `produksi/views.py:70` | `produksi_sesi_input.tangki_id` di-UPDATE **sebelum** `services.mulai_sesi()` dipanggil | kalau `mulai_sesi()` gagal (stok kurang), penugasan tangki tetap tersimpan |
| `POST /api/v1/auth/login/` | `staff_user/views.py:93-95` | `staff_user_riwayat_akses` + `authtoken_token` di dua transaksi terpisah | jejak login bisa ada tanpa token, atau sebaliknya |

Semua endpoint tulis lain sudah dibungkus `@transaction.atomic` di layer
service — diverifikasi satu per satu (lihat kolom "efek samping" di atas).

## D. Serializer yang tidak memvalidasi field kritikal

| Serializer / lokasi | Field | Masalah |
|---|---|---|
| `keuangan/views.py:21-33` | seluruh payload | **Tidak ada serializer sama sekali.** `kategori`, `nama_pengeluaran`, `pemohon`, `nominal` dibaca mentah dari `request.data`; `nominal` tidak pernah dikonversi ke `Decimal` sebelum dibandingkan/dikurangkan dengan `rekening.saldo` (`keuangan/services.py:29,34`) |
| `warehouse/serializers.py:189` | `LaporanManualSerializer.jenis` | `CharField(max_length=14)`, bukan `ChoiceField(JenisSelisih.choices)` — string apa pun masuk ke kolom bercokelat `choices` |
| `warehouse/serializers.py:196` | `SelesaikanSelisihSerializer.resolusi` | `CharField(max_length=8)`, bukan `ChoiceField(Resolusi.choices)` — nilai tak dikenal lolos ke `LaporanSelisih.resolusi`; perbandingan `== Resolusi.POTONG_TAGIHAN` (`warehouse/services.py:357`) diam-diam gagal → `nilai_klaim` dipaksa 0 |
| `work_order/serializers.py:23` | `staff_ids` | `ListField(IntegerField)` tanpa `PrimaryKeyRelatedField` — id yang tidak ada → `IntegrityError` 500 |
| `staff_user/serializers.py:27` | `ProfilSerializer` dipakai untuk `POST /auth/profil/` | tidak punya field `password`; `role` & `is_active` read-only → akun dibuat dengan password tak terpakai dan `is_active` = default `AbstractUser` (**True**), melewati seluruh alur persetujuan |
| `core/serializers.py:41,47` | `entitas_id` | `IntegerField` polos — id tak sahih baru meledak sebagai `IntegrityError`/`DoesNotExist` di service (500) |
| `produksi/serializers.py:45` | `MulaiSesiBarisSerializer.bahan_id` | tidak diverifikasi milik sesi yang bersangkutan |
| `inventory/serializers.py:196-232` | `produk_id`, `grup_bahan_id`, `entitas_id`, `tangki_*_id` | semua `IntegerField` polos; `qty` `DecimalField` tanpa `min_value` (dicek belakangan di service) |

## E. Catatan tambahan pada respons

- `produksi/serializers.py:11` — `satuan_kode` memakai `source='resep.produk_jadi.satuan_kode'`.
  `master.Produk` tidak punya atribut `satuan_kode` (`master/models.py:106` hanya
  punya FK `satuan`). Karena field-nya `read_only=True` (→ `required=False`),
  DRF melempar `SkipField` dan **field itu hilang diam-diam dari respons**,
  bukan menyebabkan 500.
- `produksi/views.py:23-26` — `get_serializer_class()` mengembalikan
  `SesiListSerializer` di kedua cabang (percabangan mati).

---

# CROSS-CHECK: telusur manual vs generator

`django-extensions` tidak terpasang, jadi `show_urls` tidak tersedia.
`drf-spectacular` terpasang dan dijalankan:

```
python manage.py spectacular --file docs/_scan/openapi.yaml   → exit 0
Warnings: 32 (14 unik)   Errors: 48 (11 unik)
```

Sebagai pembanding kedua, URLconf ditelusuri langsung lewat
`django.urls.get_resolver()`.

### Kesimpulan perbandingan

**Himpunan path sama.** 151 kombinasi method+path di `openapi.yaml` cocok
dengan hasil telusur resolver (setelah membuang varian sufiks `.format` dan
`APIRootView` yang memang tidak didokumentasikan spectacular).

### Selisih yang ditemukan

**1. Endpoint tanpa skema request/response (11 view, 48 error generator).**
Path-nya muncul di `openapi.yaml`, tapi tanpa body sama sekali:

`PembayaranView` `akunting/views.py:328` · `DaftarView` `staff_user/views.py:32` ·
`LoginView` `:60` · `LogoutView` `:104` · `PortalView` `:113` ·
`GantiPasswordView` `:134` · `IsiPoolView` `inventory/views.py:141` ·
`SetorKePoolView` `:160` · `KlaimHasilView` `:182` · `OpnameView` `:208` ·
`VerifikasiView` `:234`.

Semuanya `APIView`/`ViewSet` polos tanpa `serializer_class`. Frontend yang
mengandalkan `/api/docs/` tidak akan melihat bentuk payload login sekalipun.

**2. Empat ViewSet gagal menurunkan model** karena `get_queryset()` menyentuh
`request.user.entitas_diizinkan` / `.supervisor` yang tidak ada pada
`AnonymousUser` saat generasi schema:
`FakturPembelianViewSet` `akunting/views.py:226`, `JurnalUmumViewSet` `:69`,
`PurchaseOrderViewSet` `:112`, `DataKepegawaianViewSet` `staff_user/views.py:266`.
Akibat di schema: parameter path `{id}` didokumentasikan bertipe **string**,
bukan integer.

**3. 16 operasi tulis "hantu"** — didokumentasikan sebagai operasi normal di
`openapi.yaml` padahal implementasinya selalu `405`:

| Operasi yang didokumentasikan | Kenyataan |
|---|---|
| `PUT/PATCH/DELETE /akunting/purchase-order/{id}/` | 405 `akunting/views.py:148,156` |
| `POST /akunting/faktur/` + `PUT/PATCH/DELETE /akunting/faktur/{id}/` | 405 `akunting/views.py:244,251,260` |
| `PUT/PATCH/DELETE /warehouse/penerimaan/{id}/` | 405 `warehouse/views.py:120,129` |
| `PUT/PATCH/DELETE /warehouse/laporan-selisih/{id}/` | 405 `warehouse/views.py:183,192` |
| `PUT/PATCH/DELETE /produksi/sesi/{id}/` | 405 `produksi/views.py:33,39` |

Ditambah 3 `DELETE` yang membalas **400** (bukan 405):
`/auth/profil/{id}/` (`staff_user/views.py:165`),
`/master/produk/{id}/` dan `/master/suplier/{id}/` (`master/views.py:24`).

**4. Enum bertabrakan.** Dua peringatan generator tentang nama komponen
`Status5faEnum` / `StatusD25Enum` — beberapa model memakai field `status`
dengan himpunan `choices` berbeda dan `ENUM_NAME_OVERRIDES` tidak diset
(`settings.py:174-178`). Nama tipe di client yang di-generate akan tidak
bermakna.

**5. Tidak terdokumentasi sama sekali:** `GET /api/v1/<app>/` (APIRootView dari
`DefaultRouter`, ada untuk 9 app) dan seluruh varian `?format=`/`.json`.

Berkas mentah: `docs/_scan/openapi.yaml` (187 KB).
Data terstruktur endpoint: `docs/_scan/api-map.json`.
