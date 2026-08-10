# Papan Tugas — catatan pemasangan

Timpa seluruh berkas di `work_order/`. `models.py` menambah satu tabel
(`wo_counter`) dan dua constraint, jadi migrasi wajib.

```bash
python manage.py makemigrations work_order
python manage.py migrate
python manage.py test work_order
```

## Enam pemblokir, dan apa yang berubah

**1 · `profil_staff_id` tidak pernah ada.** `AUTH_USER_MODEL` sudah
`staff_user.Profil`, dan `WorkOrderPenugasan.staff` menunjuk model yang sama,
jadi `request.user.id` langsung cocok. Karena `getattr` diberi default `None`,
kegagalannya senyap: `approve` selalu 403 untuk semua orang, `mading` hanya
memunculkan PRODUKSI. Sekarang dipusatkan di `services.py`, tidak ada
`getattr` identitas di mana pun.

**2 · `approve` bisa mengembalikan `None`.** Kalau `aturan_penyelesaian`
bernilai di luar tiga pilihan, semua cabang terlewati dan Django menjawab
"view didn't return an HttpResponse". `services.setujui()` sekarang selalu
mengembalikan `(wo, pesan, tuntas)`.

**3 · `mading` mengabaikan penandaan.** Sekarang lewat
`services.wo_terlihat()`, dengan pengurutan `deadline` nulls-last.

**4 · `GET work-order/` membocorkan PRIVATE.** Izin objek DRF tidak berlaku
untuk endpoint list. Penyaringan pindah ke `get_queryset()`.

**5 · PATCH dengan `detail_produksi` menghasilkan 500.**
`ModelSerializer.update()` melempar AssertionError untuk field bersarang.
Sekarang ada `UbahWorkOrderSerializer` + `services.ubah_wo()`, dan penugasan
bisa diubah setelah WO dibuat.

**6 · Nomor rawan tabrakan.** `CounterWorkOrder` dikunci `select_for_update`
saat dinaikkan. Sebelumnya membaca nomor terakhir — dua pembuatan bersamaan
menghasilkan nomor identik, dan `order_by('nomor')` salah mulai WO ke-1000
dalam satu bulan.

## Perbaikan lain

`pesan_chat` keluar dari bentuk daftar; daftar sekarang membawa
`jumlah_pesan` saja. `pengirim_nama` memakai `nama_lengkap`, bukan `username`
— sebelumnya di layar yang sama muncul "Sri Wahyuni" dan "swahyuni".
`ProfilStaffRingkasSerializer` menambah `jabatan_nama`. Permission memakai
`AksesModul` dengan `modul = 'work_order'`, sejalan dengan repo. Seluruh
logika bisnis pindah ke `services.py`. Pesan bersifat append-only di model
dan di admin. Paling banyak satu PIC per WO, dijaga constraint basis data.

## Yang ditambahkan

`buka-kembali/` untuk Supervisor. Tanpa ini, WO yang salah ditutup tidak
punya jalan pulang.

Supervisor bisa menutup paksa tanpa ditandai. Tanpa jalur itu, WO yang
orangnya sudah keluar dari perusahaan menggantung selamanya di papan semua
orang.

Validasi bahwa aturan `PIC` wajib punya PIC. Sebelumnya WO seperti itu tidak
bisa diselesaikan siapa pun, dan baru ketahuan setelah orang mengerjakannya.

`progres`, `saya_ditandai`, dan `saya_sudah_menandai` di respons, supaya
frontend bisa menampilkan "2 dari 3 sudah menandai" dan mengganti label
tombol untuk aturan `SEMUA` — di mode itu tombolnya bukan menutup tugas,
melainkan menandai bagian sendiri.

## Kompatibilitas frontend

Nama aksi lama dipertahankan: `approve/` dan `kirim_pesan/` tetap ada, jadi
`useWorkOrder.js` tidak perlu diubah untuk tetap jalan.

Tiga hal yang tetap perlu disesuaikan di frontend:

**`fetchMading` memanggil endpoint yang salah.** Sekarang menembak
`work-order/` lalu menyaring `selesai === false` di JavaScript. Ganti ke
`work-order/mading/` — penyaringan dan pengurutannya sudah di server, dan
filter klien hanya bekerja pada halaman pertama.

**`approve` mengembalikan bentuk baru:** `{detail, tuntas, work_order}`.
Field `detail` dipertahankan supaya `alert(response.data.detail)` yang ada
sekarang tetap menampilkan pesan yang benar.

**Daftar tidak lagi membawa `pesan_chat`.** Dialog diskusi harus memanggil
`work-order/{id}/pesan/` atau `work-order/{id}/`.

## Satu keputusan yang mungkin ingin kamu ubah

`services.wo_terlihat()` membuat **PRIVATE tetap privat dari Supervisor**.
Kategorinya secara harfiah bernama "Pesan Pribadi / Rahasia", dan kalau
Supervisor bisa membacanya, orang akan kembali memakai WhatsApp — persis
masalah yang mau dipecahkan modul ini. Superuser tetap lolos karena dia
memang bisa membaca basis data langsung.

Kalau kebijakan ini dibalik, ubah di satu fungsi itu saja.

## Yang belum

Notifikasi WhatsApp (`services.kirim_notifikasi_whatsapp` di versi lama)
tidak saya bawa — itu integrasi luar yang butuh keputusan penyedia.

Hubungan WO PRODUKSI dengan `SesiProduksi` masih terbuka, PRD §10.1.
`validasi_stok_pigment()` di versi lama adalah stub untuk pengecekan lintas
modul, dan itu persis titik sambung yang dimaksud opsi (b) di sana.
