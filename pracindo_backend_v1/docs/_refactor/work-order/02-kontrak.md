# FASE 2 — KONTRAK & INVARIANT

Ini pagar refactor. Apa pun opsi Fase 3 yang dipilih, seluruh isi dokumen ini
harus tetap benar sesudahnya.

---

## a. Kontrak API yang dipakai frontend

Repo: `pracindo_marshitek_v2/pracindo-frontend`
Berkas tunggal yang memanggil: `src/features/work-order/composables/useWorkOrder.js`
Base URL klien: `api` (`src/utils/api.js`) — path relatif tanpa `/api/v1/`.

**5 dari 10 endpoint dipakai. 5 sisanya bebas diubah/dihapus tanpa menyentuh
frontend.**

### K1 — `GET work-order/mading/`
```
Pemanggil : useWorkOrder.js:32  fetchMading()
Request   : tanpa query param
Response  : ARRAY polos (tanpa paginasi) berisi WorkOrder
Dibaca FE : data.results || data      (useWorkOrder.js:33 — toleran dua bentuk)
```
Field yang benar-benar dibaca UI: `id`, `selesai`, `terlambat`,
`penugasan[].staff`, `dibuat_oleh_username`.

### K2 — `GET work-order/`
```
Pemanggil : useWorkOrder.js:44  fetchSemua()
Request   : ?selesai=<bool|null>&tanggal=<date|null>
Response  : {count, next, previous, results:[...]}  (PageNumberPagination, page_size 25)
Dibaca FE : data.results || data      (useWorkOrder.js:47)
```
> Catatan: `selesai` dan `tanggal` **dikirim sebagai query param tapi tidak
> ada `filterset_fields` di viewset** (`work_order/views.py:13-20`) — jadi
> keduanya diabaikan diam-diam hari ini. Memperbaikinya = menambah kemampuan,
> bukan mematahkan kontrak.

### K3 — `GET work-order/staff/`
```
Pemanggil : useWorkOrder.js:57  fetchStaffList()
Response  : ARRAY polos [{id, nama_lengkap, jabatan}]
Sumber    : ProfilStaffRingkasSerializer (work_order/serializers.py:6-9)
```
**Satu-satunya endpoint `work_order` yang sehat hari ini.** Jangan disentuh.

### K4 — `POST work-order/`
```
Pemanggil : useWorkOrder.js:72  buatWO()
Body      : {judul, deskripsi, tanggal, deadline, staff_ids:[int]}
Response  : 201 + objek WorkOrder lengkap
Dibaca FE : data (dikembalikan sebagai {success:true, wo:data})
```
Frontend **tidak pernah mengirim**: `kategori`, `aturan_penyelesaian`,
`pic_id`, `detail_produksi`. Semua jatuh ke default
(`kategori='UMUM'`, `aturan_penyelesaian='SALAH_SATU'`, `pic_id=None`).

### K5 — `POST work-order/{id}/approve/`
```
Pemanggil : useWorkOrder.js:87  approveWO()
Body      : {catatan: string}
Response  : 200 {detail: "..."}   (FE hanya memeriksa sukses/gagal)
```

### Endpoint yang TIDAK dipakai frontend

`GET|PUT|PATCH|DELETE /work-order/{id}/` dan
`POST /work-order/{id}/kirim_pesan/`.
Bebas diubah bentuknya. `kirim_pesan` bahkan belum pernah berhasil dipanggil
sekali pun (tabelnya tidak ada).

### Kontrak yang RUSAK di kedua sisi — harus diperbaiki serempak

| Sisi | Lokasi | Masalah |
|---|---|---|
| FE | `useWorkOrder.js:17` | membaca `accessCard.profil_staff_id` |
| FE | `WorkOrderPanel.vue:98` | `accessCard` tidak pernah di-*export* `useAuth()` |
| BE | `PortalView` | tidak pernah mengirim `profil_staff_id` |
| BE | `views.py:32,61` · `permissions.py:13` | membaca atribut yang tidak ada |

**Nilai yang benar di kedua sisi: `id` milik `Profil`** (`request.user.id` di
backend, `profil.id` dari `PortalView` di frontend). Ini **bukan** perubahan
kontrak — field `profil_staff_id` tidak pernah ada di respons mana pun, jadi
tidak ada konsumen yang bisa rusak.

---

## b. Invariant domain

### Apakah `work_order` menulis buku besar / stok / klaim?

Diperiksa satu per satu terhadap seluruh `work_order/*.py`:

| Target | Ditulis `work_order`? | Bukti |
|---|---|---|
| `inventory.Stok` (RAW / POOL / JADI) | **TIDAK** | tidak ada `from inventory` di berkas mana pun |
| `inventory.MutasiStok` | **TIDAK** | idem |
| `inventory.SaldoEntitas` | **TIDAK** | idem |
| `inventory.MutasiKlaim` / `PosisiKlaim` | **TIDAK** | idem |
| `akunting.JurnalUmum` / `JurnalDetail` | **TIDAK** | tidak ada `from akunting` |
| `keuangan.MutasiKas` / `RekeningBank` | **TIDAK** | tidak ada `from keuangan` |

Satu-satunya impor lintas app di seluruh `work_order` adalah
`from staff_user.models import Profil` (`views.py:10`, `serializers.py:4`),
dan pemakaiannya **baca saja** (`views.py:50`).

`work_order/services.py:19-24` menjanjikan cek stok ke `warehouse`, tapi
badannya `pass` — tidak menulis apa pun.

> **Kesimpulan: `Σ ΔS_i = 0` dan `Dr = Cr` tidak tersentuh `work_order` hari
> ini.** Itu kabar baik untuk refactor — tapi juga berarti pagar ini bersifat
> *preventif*: tugasnya menjaga agar refactor **tidak** diam-diam menyambungkan
> `work_order` ke buku besar tanpa disadari.

### Assertion yang bisa dijalankan

Bukan kalimat — ini yang harus dieksekusi sebelum & sesudah refactor.

```python
# INV-1  work_order tetap terputus dari buku besar, stok, dan klaim
def test_work_order_tidak_menyentuh_buku_besar():
    import ast, pathlib
    terlarang = {'inventory', 'akunting', 'keuangan', 'warehouse', 'produksi'}
    bocor = []
    for p in pathlib.Path('work_order').rglob('*.py'):
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            if isinstance(n, ast.ImportFrom) and n.module:
                if n.module.split('.')[0] in terlarang:
                    bocor.append(f'{p}:{n.lineno} -> {n.module}')
    assert not bocor, f'work_order menyentuh domain lain: {bocor}'
    # Kalau Opsi 3 dipilih, assertion ini WAJIB diganti INV-1b (lihat bawah),
    # bukan dihapus.

# INV-1b  HANYA kalau Opsi 3 dipilih: penulisan wajib lewat lapis service
def test_penulisan_produksi_lewat_service():
    # dilarang: from produksi.models import ... / Model.objects.create(...)
    # diizinkan: from produksi.services import buat_pesanan
    ...

# INV-2  invariant SZA tidak bergeser gara-gara work_order
@pytest.mark.django_db
def test_saldo_klaim_tidak_bergeser():
    sebelum = list(PosisiKlaim.objects.values_list('id', 'nilai_bersih'))
    _jalankan_seluruh_alur_work_order()          # buat, tag, approve, chat
    assert list(PosisiKlaim.objects.values_list('id', 'nilai_bersih')) == sebelum
    assert MutasiKlaim.objects.count() == 0

# INV-3  buku besar tetap seimbang dan tidak bertambah
@pytest.mark.django_db
def test_jurnal_tidak_tersentuh():
    n = JurnalUmum.objects.count()
    _jalankan_seluruh_alur_work_order()
    assert JurnalUmum.objects.count() == n
    for j in JurnalUmum.objects.all():           # Dr = Cr tetap dijaga trigger
        d = j.detail.aggregate(dr=Sum('debit'), cr=Sum('kredit'))
        assert d['dr'] == d['cr']

# INV-4  kas tidak bergerak
@pytest.mark.django_db
def test_kas_tidak_bergerak():
    n = MutasiKas.objects.count()
    saldo = list(RekeningBank.objects.values_list('id', 'saldo'))
    _jalankan_seluruh_alur_work_order()
    assert MutasiKas.objects.count() == n
    assert list(RekeningBank.objects.values_list('id', 'saldo')) == saldo
```

### Invariant internal `work_order`

```python
# INV-5  nomor unik dan tidak pernah dipakai ulang  (H7 melanggar ini hari ini)
assert WorkOrder.objects.values('nomor').annotate(n=Count('id')).filter(n__gt=1).count() == 0

# INV-6  satu staf hanya sekali per work order  (sudah dijaga unique_together models.py:120)
assert WorkOrderPenugasan.objects.values('work_order', 'staff') \
        .annotate(n=Count('id')).filter(n__gt=1).count() == 0

# INV-7  status selesai selalu lengkap jejaknya   << HARI INI BISA DILANGGAR
#        Django admin bisa membalik `selesai` tanpa menyentuh dua kolom lain
assert not WorkOrder.objects.filter(selesai=True) \
        .filter(Q(waktu_selesai__isnull=True) | Q(diselesaikan_oleh__isnull=True)).exists()
assert not WorkOrder.objects.filter(selesai=False) \
        .filter(Q(waktu_selesai__isnull=False) | Q(diselesaikan_oleh__isnull=False)).exists()

# INV-8  aturan SEMUA hanya boleh selesai kalau semua anggota sudah ceklis
for wo in WorkOrder.objects.filter(selesai=True, aturan_penyelesaian='SEMUA'):
    assert not wo.penugasan.filter(is_selesai_personal=False).exists()

# INV-9  aturan PIC harus punya tepat satu PIC   << HARI INI SELALU 0 (N2)
for wo in WorkOrder.objects.filter(aturan_penyelesaian='PIC'):
    assert wo.penugasan.filter(is_pic=True).count() == 1
```

**INV-7, INV-8, INV-9 tidak ditegakkan apa pun hari ini** — tidak ada
`CheckConstraint`, tidak ada trigger, tidak ada validasi. Refactor yang baik
menjadikannya ditegakkan; refactor minimum setidaknya tidak boleh
memperburuknya.

---

## c. Ketergantungan `AksesModul` / role

**Tidak ada. Dan itu sendiri adalah temuan.**

| Yang diperiksa | Hasil |
|---|---|
| Atribut `modul` di `WorkOrderViewSet` | **tidak ada** (`work_order/views.py:13-20`) |
| `AksesModul` di `permission_classes` | **tidak ada** — hanya `[IsAuthenticated, CanAksesWorkOrder]` (`:20`) |
| Role apa yang dikunci | **tidak ada satu pun**. Setiap pengguna yang login dan aktif bisa memanggil `list`, `create`, `mading`, `staff` |
| `CanAksesWorkOrder.has_permission` | **tidak diimplementasikan** (`permissions.py` hanya punya `has_object_permission`, `:9`) → endpoint non-objek lolos tanpa pemeriksaan tambahan |
| Penjaga pada objek | `PRODUKSI` terbuka untuk semua (`permissions.py:16-17`); tulis hanya `dibuat_oleh` (`:24`); cabang "saya di-tag" (`:20`) **mati** karena `profil_staff_id` |
| `'work_order'` di `AKSES_MODUL` | **UNKNOWN** — belum diverifikasi. Tidak berpengaruh ke backend karena `AksesModul` memang tidak dipasang |

Frontend menggerbangi rute `/work-order` dengan `meta.modul: 'work_order'`
(`router/index.js:197`) — **tapi rute itu merender `ModulBelumSiap.vue`**.
Panel aslinya dirender di `DashboardView.vue:45` dan `ModulLayout.vue:41`,
yang **tidak digerbangi modul**. Jadi papan tugas tampil untuk semua pengguna
yang login, terlepas dari role.

**Putusan pagar:** menambahkan `modul = 'work_order'` + `AksesModul`
**mengubah perilaku** (sebagian pengguna akan mulai menerima 403). Itu
perbaikan keamanan yang benar, tapi harus diputuskan sadar — bukan efek
samping refactor. Ditandai eksplisit di setiap opsi Fase 3.

---

## d. Data existing yang tidak boleh hilang

| Tabel | Baris | Konsekuensi |
|---|---|---|
| `wo_work_order` | **0** | tidak ada yang perlu diselamatkan |
| `wo_penugasan` | **0** | tidak ada yang perlu diselamatkan |
| `wo_pesan` | **tabel tidak ada** | tidak ada yang perlu diselamatkan |
| `wo_detail_produksi` | **tabel tidak ada** | tidak ada yang perlu diselamatkan |

**Tidak ada satu baris data pun yang harus diselamatkan.** Ini mengubah
kalkulus Fase 3 secara mendasar: biaya migrasi data adalah **nol** untuk
setiap opsi, termasuk yang paling radikal. Yang membedakan opsi bukan risiko
data, melainkan risiko kontrak frontend dan biaya perawatan jangka panjang.

Yang tetap harus dijaga:

1. **Nama tabel** `wo_work_order` dan `wo_penugasan` **sudah ada di DB**.
   Mengganti `db_table` = perlu `AlterModelTable`, bukan sekadar edit model.
2. **`0001_initial` sudah tercatat ter-*apply***. Perbaikan apa pun **wajib
   lewat migrasi baru (`0002_…`)**. Mengedit `0001_initial` lagi akan
   mengulang persis kesalahan yang membuat keadaan ini (lihat `00-status.md` §1).
3. **`django_migrations` tidak boleh disunting manual** untuk "memaksa" ulang.
