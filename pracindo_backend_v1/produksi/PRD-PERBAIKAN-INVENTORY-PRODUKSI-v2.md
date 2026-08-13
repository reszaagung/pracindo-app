# PRD — PERBAIKAN INVENTORY, PRODUKSI, KOMPONEN, KLAIM, DAN BATCH

**Versi:** v2  
**Status:** Final  
**Tujuan:** Menjadi spesifikasi perbaikan logika bisnis dan struktur data untuk inventory/production tanpa mengubah prinsip bisnis utama yang telah disepakati.

---

# 1. TUJUAN

Perbaikan harus memastikan bahwa sistem persediaan:

- tidak menciptakan nilai secara diam-diam;
- tidak menghilangkan nilai secara diam-diam;
- mempertahankan nilai riil yang melekat pada stok;
- menghitung nilai keluar secara proporsional;
- menghabiskan seluruh nilai ketika stok benar-benar habis;
- dapat menelusuri produk komposit `X` kembali ke komponen `A/B/C`;
- mempertahankan kepemilikan setiap entitas;
- mengizinkan posisi entitas menjadi negatif;
- dapat menjelaskan saldo negatif sebagai kewajiban antar-entitas;
- mencatat produksi secara lengkap dari input sampai hasil;
- memiliki **Batch sebagai identitas lot/asal yang wajib ditelusuri**;
- menjaga lineage Batch dari bahan masuk sampai hasil produksi dan barang jadi;
- menjaga seluruh operasi kritis tetap atomic, idempotent, dan terlindungi dari race condition.

Prinsip utama:

```text
NILAI TIDAK BOLEH MUNCUL DARI UDARA.
NILAI TIDAK BOLEH HILANG KE UDARA.
SETIAP BARANG HARUS DAPAT DITELUSURI.
SETIAP NILAI HARUS DAPAT DITELUSURI.
SETIAP BATCH HARUS DAPAT DITELUSURI.
```

---

# 2. RUANG LINGKUP PERBAIKAN

PRD ini mencakup:

1. inventory;
2. RAW;
3. POOL;
4. JADI;
5. produksi;
6. formula/komponen;
7. Batch;
8. kepemilikan entitas;
9. klaim;
10. kewajiban antar-entitas;
11. nilai persediaan;
12. pembulatan;
13. opname;
14. rekonsiliasi;
15. locking;
16. idempotency;
17. traceability.

PRD ini **tidak** dimaksudkan untuk mengganti keseluruhan ERP atau UI.

---

# 3. KONSEP DASAR

Persediaan mempunyai minimal empat dimensi:

```text
PRODUK
KUANTITAS
NILAI
BATCH
```

Untuk stok yang memiliki pemilik, terdapat dimensi tambahan:

```text
ENTITAS PEMILIK
```

Dengan demikian satu stok tidak cukup dipahami hanya sebagai:

```text
produk + qty
```

tetapi:

```text
produk
+ qty
+ nilai
+ batch
+ lapis
+ tangki
+ entitas pemilik
```

---

# 4. BATCH — DEFINISI

`Batch` adalah identitas lot yang digunakan untuk mempertahankan asal-usul dan perjalanan suatu barang/material.

Batch bukan sekadar nomor dokumen.

Batch harus dapat digunakan untuk menjawab:

```text
Barang ini berasal dari mana?
Masuk melalui transaksi apa?
Menggunakan bahan/batch apa?
Diproses pada produksi mana?
Menghasilkan batch apa?
Sekarang berada di mana?
Siapa yang memiliki?
Berapa qty yang tersisa?
Berapa nilai yang tersisa?
```

---

# 5. FOREIGN KEY BATCH — ATURAN UTAMA

## 5.1 Batch harus berupa ForeignKey

Relasi Batch pada model yang memang memiliki identitas lot **harus menggunakan ForeignKey Django**, bukan menyimpan `batch_id` sebagai integer biasa.

Contoh:

```python
batch = models.ForeignKey(
    Batch,
    on_delete=models.PROTECT,
    related_name='...',
)
```

Gunakan:

```text
on_delete=PROTECT
```

untuk mencegah Batch yang sudah memiliki transaksi historis dihapus.

---

# 6. BATCH PADA STOK

`Stok` harus dapat dibedakan berdasarkan Batch apabila barang tersebut dikelola secara batch/lot.

Konsep kunci stok menjadi:

```text
produk
+
grup_bahan
+
lapis
+
tangki
+
batch
```

Bukan hanya:

```text
produk
+
grup_bahan
+
lapis
+
tangki
```

Jika dua Batch berbeda mempunyai produk yang sama, keduanya **tidak boleh digabung menjadi satu saldo stok** apabila Batch wajib ditelusuri.

Contoh:

```text
Produk X
Batch X-001 = 50 kg
Batch X-002 = 70 kg
```

harus tetap menjadi dua sumber stok:

```text
X / X-001 / 50 kg
X / X-002 / 70 kg
```

bukan:

```text
X / 120 kg
```

yang menghilangkan lineage Batch.

---

# 7. KAPAN BATCH WAJIB?

Batch wajib digunakan untuk:

- bahan baku yang diterima dari supplier;
- bahan yang masuk produksi;
- material yang keluar menuju produksi;
- hasil produksi;
- produk jadi apabila produk tersebut menggunakan batch;
- perpindahan stok antar-lokasi/tangki yang membutuhkan traceability;
- opname terhadap stok batch;
- klaim/penarikan barang batch apabila diperlukan oleh proses bisnis.

Jika suatu jenis stok memang secara bisnis tidak menggunakan Batch, field dapat nullable hanya jika aturan master produk secara eksplisit mengizinkannya.

**Nullable tidak boleh menjadi alasan untuk menghilangkan Batch pada transaksi yang secara bisnis wajib batch.**

---

# 8. BATCH PADA PENERIMAAN RAW

Pada:

```python
terima_raw()
```

barang yang diterima harus memiliki Batch.

Alur:

```text
Supplier
   ↓
Penerimaan
   ↓
Batch
   ↓
RAW Stok
   ↓
Tangki/Lokasi
```

Mutasi penerimaan harus dapat ditelusuri ke Batch tersebut.

Jika Batch berasal dari supplier:

```text
batch_internal
+
batch_supplier
```

dapat disimpan terpisah apabila sistem membutuhkan keduanya.

Batch internal menjadi identitas yang digunakan oleh inventory.

---

# 9. BATCH PADA RAW → POOL

Ketika:

```text
RAW → POOL
```

Batch tidak boleh hilang.

Alur:

```text
RAW Batch A
    ↓
POOL Batch A
```

Jika proses bisnis menyatakan bahwa transfer hanya memindahkan barang tanpa transformasi, maka Batch sumber dipertahankan.

Mutasi keluar dan mutasi masuk harus mengacu pada Batch yang sama.

---

# 10. BATCH PADA PRODUKSI

Produksi mempunyai hubungan:

```text
Production/Work Order
        ↓
Input Batch
        ↓
Proses
        ↓
Output Batch
```

Satu proses produksi dapat mempunyai banyak input Batch.

Contoh:

```text
Produksi P-001

Input:
A Batch A-001 = 30 kg
B Batch B-004 = 45 kg
C Batch C-002 = 25 kg

Output:
X Batch X-010 = 95 kg
Rugi = 5 kg
```

Sistem harus menyimpan hubungan tersebut.

---

# 11. BATCH INPUT PRODUKSI

Setiap `pakai_dari_pool()` yang digunakan sebagai input produksi harus dapat menyimpan:

```text
production_id / work_order_id
batch_id
produk_id
qty
nilai
tanggal
referensi
```

Tujuannya agar dapat diketahui:

```text
Batch A-001
→ dipakai pada produksi P-001
→ menghasilkan Batch X-010
```

---

# 12. BATCH OUTPUT PRODUKSI

`hasil_ke_pool()` harus dapat menghasilkan atau menerima Batch hasil.

Contoh:

```python
hasil_ke_pool(
    produk_id=...,
    batch_id=...,
    qty=...,
    nilai_masuk=...,
)
```

Batch hasil harus menjadi identitas baru apabila proses produksi menciptakan lot baru.

Contoh:

```text
Input:
A-001
B-004
C-002

Output:
X-010
```

Batch `X-010` harus mempunyai lineage menuju seluruh Batch input.

---

# 13. SPLIT DAN MERGE BATCH

## 13.1 Split

Satu Batch boleh terbagi menjadi beberapa stok/transaksi.

Contoh:

```text
Batch A-001
100 kg

↓
Tangki T1 = 40 kg
Tangki T2 = 60 kg
```

Batch tetap:

```text
A-001
```

pada kedua lokasi.

---

## 13.2 Merge

Dua Batch berbeda **tidak boleh diam-diam digabung menjadi satu Batch**.

Jika proses bisnis memang membutuhkan pencampuran:

```text
A-001
+
A-002
↓
PROSES MIXING
↓
BATCH BARU
```

maka harus dibuat Batch hasil baru.

Contoh:

```text
A-001 + A-002
        ↓
      MIX
        ↓
     X-003
```

Dengan demikian lineage tetap ada:

```text
X-003
├── A-001
└── A-002
```

---

# 14. BATCH DAN TANGKI

Tangki harus konsisten dengan Batch.

Aturan minimum:

```text
satu stok pada satu tangki
=
satu produk
+
satu Batch
```

Jika tangki berisi Batch tertentu, transaksi yang memasukkan Batch berbeda harus ditolak kecuali transaksi tersebut adalah proses mixing yang secara eksplisit menghasilkan Batch baru.

Tidak boleh:

```text
Tangki T1:
Batch A-001
Batch B-001
```

tanpa mekanisme mixing yang sah.

---

# 15. BATCH DAN PRODUK

Batch harus selalu terkait dengan Produk.

Secara konsep:

```text
Batch
 └── produk
```

Satu Batch tidak boleh berpindah menjadi produk lain hanya dengan mengubah `produk_id`.

Transformasi produk harus melalui proses yang menciptakan hubungan:

```text
input Batch
→ proses
→ output Batch
```

---

# 16. BATCH DAN KEMASAN

Untuk:

```text
POOL CURAH
→
PRODUK JADI/KEMASAN
```

Batch sumber harus tetap dapat dilacak.

Contoh:

```text
Curah X
Batch X-010
50 kg

↓ packing

X 1 KG
Batch X-010-P01
50 pcs
```

Jika proses bisnis menganggap barang kemasan sebagai Batch baru, maka Batch kemasan harus mempunyai parent/source Batch.

Lineage:

```text
X-010
  ↓
X-010-P01
```

---

# 17. METHOD X → A/B/C

Jika:

```text
X = A + B + C
```

maka pengambilan X harus mempunyai rincian komponen.

Contoh:

```text
X = 150 kg

A = 45 kg
B = 67,5 kg
C = 37,5 kg
```

Pengambilan:

```text
100 kg
```

rasio:

```text
100 / 150 = 2/3
```

sehingga:

```text
A = 30 kg
B = 45 kg
C = 25 kg
```

Total:

```text
100 kg
```

---

# 18. BATCH PADA X → A/B/C

Jika X merupakan hasil produksi dari A/B/C, maka pengambilan X harus dapat ditelusuri ke Batch X yang digunakan.

Contoh:

```text
X Batch X-010
150 kg

formula:
A 45 kg
B 67,5 kg
C 37,5 kg
```

Saat X 100 kg diambil:

```text
X-010
   ↓
pengambilan 100 kg
   ↓
A = 30 kg
B = 45 kg
C = 25 kg
```

Jika rincian formula bersumber dari beberapa Batch, sistem harus mempertahankan sumber Batch tersebut.

---

# 19. BATCH DAN KEPEMILIKAN ENTITAS

Batch tidak menghapus konsep kepemilikan.

Sistem tetap membedakan:

```text
Batch
+
Entitas
```

Contoh:

```text
Batch X-010
PT  = 60 kg
CV1 = 40 kg
```

Batch tetap satu:

```text
X-010
```

tetapi kepemilikan tetap dapat berbeda.

---

# 20. SALDO ENTITAS BOLEH NEGATIF

Contoh:

```text
A awal = 13,5 kg
B awal = 6,75 kg
C awal = 37,5 kg
```

Pengambilan:

```text
A = 30 kg
B = 45 kg
C = 25 kg
```

hasil:

```text
A = -16,5 kg
B = -38,25 kg
C = +12,5 kg
```

Nilai negatif **tidak boleh dipaksa menjadi nol**.

Nilai negatif berarti:

```text
hak yang telah digunakan
>
hak yang telah disetor
```

---

# 21. AWAN / KEWAJIBAN ANTAR-ENTITAS

Jika saldo negatif muncul, sistem harus dapat menjelaskan:

```text
entitas debitur
→ entitas kreditur
→ batch
→ produk
→ qty
→ nilai
→ transaksi sumber
```

Tidak cukup hanya menyimpan:

```text
PT = -Rp100.000
CV = +Rp100.000
```

tanpa lineage.

Kewajiban harus dapat ditelusuri kembali ke transaksi yang menyebabkan pengambilan tersebut.

---

# 22. NILAI STOK

Untuk:

```text
stok.qty = Q
stok.nilai = N
```

pengambilan:

```text
q
```

menghasilkan:

```text
nilai_keluar = N × q / Q
```

Jika:

```text
q >= Q
```

maka:

```text
nilai_keluar = N
```

Contoh:

```text
X:
150 kg
Rp2.212.500

keluar:
100 kg

nilai:
Rp1.475.000

sisa:
50 kg
Rp737.500
```

---

# 23. STOK HABIS

Jika:

```text
qty keluar = qty tersedia
```

maka:

```text
qty akhir = 0
nilai akhir = 0
```

Tidak boleh tersisa:

```text
0 kg / Rp500
```

atau:

```text
0 kg / Rp0,01
```

Jika kondisi tersebut terjadi akibat pembulatan, seluruh sisa nilai harus ikut keluar pada transaksi yang menghabiskan stok.

---

# 24. NILAI NEGATIF

Nilai stok tidak boleh negatif.

Jika operasi menghasilkan:

```text
stok.nilai < 0
```

transaksi harus gagal.

Jangan melakukan:

```python
stok.nilai = NOL
```

untuk menutupi kesalahan.

Khusus saldo hak entitas, nilai negatif diperbolehkan karena mempunyai makna bisnis sebagai kewajiban.

---

# 25. RAW → POOL

Perpindahan:

```text
RAW → POOL
```

tidak boleh menghilangkan Batch.

Nilai yang berpindah harus ditentukan secara eksplisit.

Jika nilai riil inventory digunakan:

```text
nilai RAW keluar
=
nilai POOL masuk
```

Jika digunakan konsep nilai ekuivalen untuk hak entitas, nilai ekuivalen harus dipisahkan secara konseptual dari nilai riil inventory dan tidak boleh menciptakan nilai fiktif.

---

# 26. POOL → PRODUKSI

`pakai_dari_pool()` menghasilkan:

```python
mutasi, nilai_keluar
```

Nilai tersebut adalah nilai yang benar-benar keluar dari POOL.

Transaksi produksi wajib mengikat penggunaan tersebut ke:

```text
Batch
+
Production/Work Order
```

Klaim entitas tidak berubah hanya karena material masuk proses produksi.

---

# 27. PRODUKSI

Untuk satu sesi produksi:

```text
TOTAL NILAI INPUT
=
TOTAL NILAI OUTPUT
+
TOTAL NILAI RUGI
```

Contoh:

```text
Input  = Rp50.000
Output = Rp47.142,86
Rugi   = Rp2.857,14
```

Maka:

```text
Rp47.142,86 + Rp2.857,14
=
Rp50.000
```

---

# 28. PRODUKSI MULTI-BATCH

Jika produksi memakai:

```text
A-001
A-002
B-001
```

maka seluruh Batch harus dicatat.

Output:

```text
X-010
```

harus memiliki hubungan:

```text
X-010
├── A-001
├── A-002
└── B-001
```

Tidak boleh hanya menyimpan:

```text
input_produk = A
input_qty = 100
```

tanpa rincian Batch apabila Batch wajib.

---

# 29. RUGI/SUSUT

Jika produksi kehilangan nilai:

```text
nilai_rugi = nilai_input - nilai_output
```

nilai rugi harus dicatat melalui mekanisme `RUGI`.

Batch sumber harus tetap diketahui.

Contoh:

```text
Batch A-001
→ produksi P-001
→ output X-010
→ susut
```

Dengan demikian audit dapat mengetahui dari Batch mana kerugian berasal.

---

# 30. PEMBULATAN

Gunakan:

```python
Decimal
```

bukan `float`.

Kuantitas:

```python
Q3 = Decimal("0.001")
```

Nilai:

```python
Q2 = Decimal("0.01")
```

Pembulatan harus deterministik.

Residual pembulatan harus dialokasikan secara eksplisit.

---

# 31. IDENTITY DAN IDEMPOTENCY

Semua mutasi wajib memiliki:

```text
idempotency_key
```

Pemanggilan ulang tidak boleh menciptakan transaksi kedua.

Idempotency harus mempertimbangkan:

```text
Batch
+
produk
+
stok
+
referensi
+
jenis transaksi
```

sesuai kebutuhan implementasi.

---

# 32. TRANSACTION DAN LOCKING

Operasi mutasi wajib:

```python
@transaction.atomic
```

dan menggunakan:

```python
select_for_update()
```

untuk baris yang menjadi sumber saldo.

Minimal:

```text
Stok
SaldoEntitas
PosisiKlaim
Tangki
Batch
```

harus dilindungi apabila datanya diubah dalam transaksi.

Tujuan:

```text
dua transaksi simultan
→ tidak boleh mengambil stok yang sama secara tidak sah
→ tidak boleh membuat nilai negatif
→ tidak boleh merusak lineage Batch
```

---

# 33. PERBAIKAN `_geser_pemilik()`

Tidak boleh:

```python
if saldo.nilai < 0:
    saldo.nilai = NOL
```

Harus:

```python
if saldo.qty == 0:
    saldo.nilai = NOL
elif saldo.nilai < 0:
    raise ValidationError(...)
```

Untuk posisi hak/klaim entitas, negatif diperbolehkan dan harus masuk ke ledger kewajiban.

---

# 34. PERBAIKAN `_catat()`

Setiap mutasi harus memenuhi:

```text
saldo_qty_baru
=
saldo_qty_lama + masuk - keluar
```

dan:

```text
saldo_nilai_baru
=
saldo_nilai_lama + nilai_masuk - nilai_keluar
```

Jika:

```text
saldo_qty_baru = 0
```

maka:

```text
saldo_nilai_baru = 0
```

Batch pada mutasi harus konsisten dengan Batch pada stok.

---

# 35. OPname

## 35.1 POOL kurang

Jika:

```text
qty_fisik < qty_catatan
```

maka nilai yang hilang dihitung proporsional.

Nilai tersebut harus dicatat sebagai:

```text
RUGI
```

dengan Batch yang sesuai.

## 35.2 POOL lebih

Jika tidak ada dasar nilai:

```text
nilai masuk = 0
```

Jika terdapat dokumen pendukung:

```text
nilai_penyesuaian
```

boleh digunakan.

Batch harus ditentukan atau dibuat sesuai asal barang.

## 35.3 RAW/JADI

Selisih harus dikaitkan dengan:

```text
entitas
+
batch
```

jika Batch wajib.

---

# 36. PELUNASAN ANTAR-ENTITAS

Pelunasan tidak mengubah stok fisik.

Contoh:

```text
A = -Rp30.000
B = +Rp30.000
```

A membayar B:

```text
A +Rp30.000
B -Rp30.000
```

Total klaim grup tetap.

Jika kewajiban berasal dari Batch tertentu, referensi kewajiban harus mempertahankan lineage Batch tersebut atau referensi transaksi asal.

---

# 37. REKONSILIASI

## 37.1 Kepemilikan

Untuk stok yang memiliki pemilik:

```text
Σ SaldoEntitas.qty
=
Stok.qty
```

dan:

```text
Σ SaldoEntitas.nilai
=
Stok.nilai
```

## 37.2 POOL

Jika menggunakan ledger klaim:

```text
Σ PosisiKlaim.nilai_bersih
=
Σ Stok.nilai POOL
```

## 37.3 Cache

```text
PosisiKlaim
=
Σ MutasiKlaim
```

## 37.4 Mutasi

```text
saldo sebelumnya
+ masuk
- keluar
=
saldo sesudah
```

untuk qty dan nilai.

## 37.5 Batch

Untuk setiap Batch:

```text
total stok batch
=
total mutasi batch yang masih relevan
```

dan seluruh input/output produksi Batch harus mempunyai lineage yang valid.

---

# 38. VERIFIKASI BATCH

Sistem harus menyediakan pemeriksaan yang dapat menemukan:

- stok tanpa Batch padahal wajib Batch;
- mutasi dengan Batch berbeda dari stok;
- Batch mengacu ke produk yang salah;
- Batch dihapus/diubah padahal memiliki transaksi;
- output Batch tanpa input/source;
- input produksi tanpa Batch;
- Batch yang berpindah produk tanpa proses transformasi;
- tangki mencampur Batch tanpa proses mixing;
- lineage Batch terputus.

---

# 39. QUERY TRACEABILITY

Sistem harus dapat melakukan penelusuran dua arah.

## Forward trace

```text
Batch bahan
→ penerimaan
→ RAW
→ POOL
→ produksi
→ output
→ packaging
→ JADI
→ distribusi
```

## Backward trace

```text
Batch JADI
→ Batch hasil produksi
→ produksi
→ Batch input
→ penerimaan supplier
```

---

# 40. CONTOH TRACEABILITY

```text
Supplier
  ↓
Receipt R-001
  ↓
Batch A-001
  ↓
RAW A
  ↓
POOL A
  ↓
Production P-001
  ↓
Batch X-010
  ↓
POOL X
  ↓
Packing PCK-001
  ↓
Batch X-010-P01
  ↓
JADI
```

Sistem harus dapat menampilkan seluruh rantai tersebut.

---

# 41. ACCEPTANCE TEST — NILAI

Input:

```text
X = 150 kg
Rp2.212.500
```

Ambil:

```text
100 kg
```

Expected:

```text
keluar = 100 kg
nilai keluar = Rp1.475.000

sisa = 50 kg
nilai sisa = Rp737.500
```

---

# 42. ACCEPTANCE TEST — KOMPONEN

Formula:

```text
X = A 45 kg
  + B 67,5 kg
  + C 37,5 kg
```

Ambil:

```text
100 kg
```

Expected:

```text
A = 30 kg
B = 45 kg
C = 25 kg
```

Total:

```text
100 kg
```

---

# 43. ACCEPTANCE TEST — SALDO ENTITAS

Saldo awal:

```text
A = 13,5 kg
B = 6,75 kg
C = 37,5 kg
```

Penggunaan:

```text
A = 30 kg
B = 45 kg
C = 25 kg
```

Expected:

```text
A = -16,5 kg
B = -38,25 kg
C = +12,5 kg
```

Negatif tidak boleh dinormalisasi menjadi nol.

---

# 44. ACCEPTANCE TEST — BATCH

Input:

```text
A-001 = 100 kg
A-002 = 100 kg
```

Produksi hanya memakai:

```text
A-001 = 30 kg
```

Expected:

```text
A-001 tersisa = 70 kg
A-002 tersisa = 100 kg
```

Tidak boleh menghasilkan:

```text
A total = 170 kg
```

tanpa Batch.

---

# 45. ACCEPTANCE TEST — OUTPUT BATCH

Input:

```text
A-001
B-004
C-002
```

Produksi:

```text
P-001
```

Output:

```text
X-010
```

Expected lineage:

```text
X-010
├── P-001
├── A-001
├── B-004
└── C-002
```

---

# 46. ACCEPTANCE TEST — SPLIT

```text
Batch A-001 = 100 kg
```

dipindahkan:

```text
T1 = 40 kg
T2 = 60 kg
```

Expected:

```text
T1 Batch A-001 = 40 kg
T2 Batch A-001 = 60 kg
```

Batch tidak berubah.

---

# 47. ACCEPTANCE TEST — MIXING

Input:

```text
A-001
A-002
```

Jika dicampur:

```text
Output Batch MIX-001
```

Expected:

```text
MIX-001
├── A-001
└── A-002
```

Tidak boleh mengganti Batch A-001 menjadi A-002 atau sebaliknya.

---

# 48. ACCEPTANCE TEST — PRODUKSI

```text
Input  = Rp50.000
Output = Rp47.142,86
Rugi   = Rp2.857,14
```

Expected:

```text
Output + Rugi = Input
```

dan Batch input tetap dapat ditelusuri.

---

# 49. ACCEPTANCE TEST — STOK HABIS

```text
10 kg / Rp10.000
```

keluar:

```text
10 kg
```

Expected:

```text
0 kg / Rp0
```

---

# 50. ACCEPTANCE TEST — IDEMPOTENCY

Kirim transaksi yang sama dua kali:

```text
idempotency_key = ABC-001
```

Expected:

```text
mutasi hanya satu kali
stok berubah hanya satu kali
Batch lineage hanya satu kali
```

---

# 51. NON-GOALS

Perbaikan ini tidak bertujuan untuk:

- mengganti keseluruhan arsitektur ERP;
- mengganti UI;
- menghapus histori;
- menghilangkan saldo negatif entitas;
- menggabungkan Batch berbeda tanpa proses;
- mengganti nilai aktual dengan tarif sintetis;
- mengizinkan silent correction;
- menghapus lineage untuk menyederhanakan query.

---

# 52. DEFINITION OF DONE

Implementasi dianggap selesai apabila:

1. `X → A/B/C` berjalan proporsional.
2. Pengambilan sebagian X menyisakan qty dan nilai yang benar.
3. Saldo entitas boleh negatif.
4. Nilai negatif stok tidak pernah disembunyikan.
5. Produksi memenuhi:
   ```text
   input = output + rugi
   ```
6. Semua mutasi memiliki idempotency.
7. Semua mutasi kritis atomic.
8. Row locking diterapkan.
9. Batch menggunakan ForeignKey yang benar.
10. Batch tidak dapat dihapus jika sudah digunakan.
11. Stok batch tidak tercampur secara diam-diam.
12. RAW → POOL mempertahankan Batch.
13. Input produksi mempertahankan Batch.
14. Output produksi mempunyai Batch.
15. Output Batch mempunyai lineage input.
16. Packing mempertahankan lineage Batch.
17. Split Batch dapat ditelusuri.
18. Mixing menghasilkan Batch baru.
19. Rekonsiliasi qty lulus.
20. Rekonsiliasi nilai lulus.
21. Rekonsiliasi klaim lulus.
22. Rekonsiliasi Batch lulus.
23. Forward trace Batch lulus.
24. Backward trace Batch lulus.
25. Acceptance test seluruhnya lulus.

---

# 53. PRINSIP FINAL

Sistem inventory harus dapat menjawab:

```text
APA?
→ Produk apa?

BERAPA?
→ Berapa qty?

BERAPA NILAINYA?
→ Berapa rupiah?

BATCH MANA?
→ Dari lot mana?

MILIK SIAPA?
→ Entitas mana?

ASALNYA DARI MANA?
→ Transaksi/Batch sumber apa?

DIPAKAI UNTUK APA?
→ Produksi/transaksi apa?

MENJADI APA?
→ Output/Batch apa?

SIAPA YANG MENANGGUNG?
→ Entitas mana?

KE MANA NILAINYA?
→ Stok lain atau RUGI?
```

Untuk produk komposit:

```text
X bukan hanya stok 150 kg.

X adalah:

produk
+ formula
+ komponen
+ Batch
+ qty
+ nilai
+ kepemilikan
+ transaksi
+ lineage
```

Dengan demikian sistem tidak sekadar menghitung saldo.

Sistem membangun **rantai bukti persediaan**:

```text
SOURCE
  ↓
BATCH
  ↓
STOCK
  ↓
MOVEMENT
  ↓
PRODUCTION
  ↓
OUTPUT BATCH
  ↓
PACKAGING
  ↓
FINISHED GOODS
  ↓
CLAIM / DISTRIBUTION
```

Tidak boleh ada titik dalam rantai tersebut yang kehilangan:

```text
nilai
qty
kepemilikan
atau Batch lineage
```

tanpa transaksi yang secara eksplisit menjelaskan mengapa perubahan tersebut terjadi.
