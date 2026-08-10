/**
 * features/produksi/_fixtures.dev.js
 * ===================================
 * SEMENTARA. Backend `produksi` Fase 2 belum dibangun — endpoint di §D
 * RANCANGAN-API.md sudah final kontraknya tapi belum ada implementasinya.
 *
 * HAPUS SELURUH FILE INI saat Fase 2 live, bersama flag PAKAI_FIXTURE di
 * kedua composable. Mematikan flag saja sudah cukup membuat seluruh modul
 * memakai API asli — file ini tidak pernah diimpor komponen mana pun.
 *
 * ATURAN BENTUK (jangan dilanggar saat menambah data):
 *   1. Setiap helper mengembalikan { data } supaya baris pemanggilan di
 *      composable identik dengan hasil axios — intercept satu baris, bukan
 *      cabang struktur.
 *   2. Endpoint router (list) membungkus { count, next, previous, results }.
 *      Endpoint @action mengembalikan array / objek polos. Lihat §D kolom
 *      "Catatan" untuk menentukan mana yang mana.
 *   3. Decimal SELALU string — DRF mengirimnya begitu
 *      (COERCE_DECIMAL_TO_STRING = True, API-MAP.md).
 */

const jeda = (ms = 180) => new Promise((r) => setTimeout(r, ms))

/** Bungkus respons terpaginasi DRF (PAGE_SIZE = 25). */
const halaman = (results) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
})

const GRUP_BAHAN = [
  { id: 1, kode: 'PT', nama: 'Pool PT sendiri' },
  { id: 2, kode: 'BERSAMA', nama: 'Pool bersama (CV + Agus + Marsini)' },
]

const ENTITAS = [
  { id: 1, kode: 'PCJM', nama: 'PT Pracindo Jaya Makmur', jenis: 'BADAN_HUKUM', grup_bahan: 1 },
  { id: 2, kode: 'CVSA', nama: 'CV Sumber Alam', jenis: 'BADAN_HUKUM', grup_bahan: 2 },
  { id: 3, kode: 'AGS', nama: 'Agus Santoso', jenis: 'PERORANGAN', grup_bahan: 2 },
  { id: 4, kode: 'MRS', nama: 'Marsini', jenis: 'PERORANGAN', grup_bahan: 2 },
]

const PRODUK = [
  { id: 10, kode: 'TEH-KMS', nama: 'Teh Kemasan 250ml', jenis: 'BARANG_JADI', satuan_kode: 'pcs' },
  { id: 11, kode: 'TEH-CLP', nama: 'Teh Celup', jenis: 'BAHAN_BAKU', satuan_kode: 'pcs' },
  { id: 12, kode: 'GULA', nama: 'Gula Kristal Putih', jenis: 'BAHAN_BAKU', satuan_kode: 'kg' },
  { id: 13, kode: 'SIR-JHE', nama: 'Sirup Jahe (percobaan)', jenis: 'BARANG_JADI', satuan_kode: 'kg' },
  { id: 14, kode: 'JHE-EKS', nama: 'Ekstrak Jahe', jenis: 'BAHAN_BAKU', satuan_kode: 'kg' },
]

const RESEP = [
  {
    id: 1,
    produk_jadi: 10,
    produk_jadi_kode: 'TEH-KMS',
    produk_jadi_nama: 'Teh Kemasan 250ml',
    versi: 3,
    nama: 'Teh kemasan standar',
    hasil_per_batch: '1.000',
    susut_wajar: '0.0500',
    berlaku_sejak: '2026-03-01',
    aktif: true,
    item: [
      { id: 1, bahan: 11, bahan_kode: 'TEH-CLP', bahan_nama: 'Teh Celup', qty: '1.000', satuan_kode: 'pcs' },
      { id: 2, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty: '0.002', satuan_kode: 'kg' },
    ],
  },
  {
    id: 2,
    produk_jadi: 10,
    produk_jadi_kode: 'TEH-KMS',
    produk_jadi_nama: 'Teh Kemasan 250ml',
    versi: 2,
    nama: 'Teh kemasan (versi lama, gula lebih banyak)',
    hasil_per_batch: '1.000',
    susut_wajar: '0.0600',
    berlaku_sejak: '2025-11-01',
    aktif: false,
    item: [
      { id: 3, bahan: 11, bahan_kode: 'TEH-CLP', bahan_nama: 'Teh Celup', qty: '1.000', satuan_kode: 'pcs' },
      { id: 4, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty: '0.003', satuan_kode: 'kg' },
    ],
  },
]

/**
 * §E.2 JenisPengukuran. `satuan` di sini yang membuat layar Sesi Berjalan
 * cukup dua ketukan — operator tidak pernah mengetik satuan.
 */
const JENIS_PENGUKURAN = [
  { id: 1, kode: 'SUHU', nama: 'Suhu', satuan: '°C', tipe_nilai: 'ANGKA', nilai_min: '40.0000', nilai_max: '120.0000', aktif: true },
  { id: 2, kode: 'DURASI', nama: 'Durasi', satuan: 'menit', tipe_nilai: 'ANGKA', nilai_min: '1.0000', nilai_max: '480.0000', aktif: true },
  { id: 3, kode: 'RPM', nama: 'Kecepatan aduk', satuan: 'rpm', tipe_nilai: 'ANGKA', nilai_min: '0.0000', nilai_max: '1500.0000', aktif: true },
  { id: 4, kode: 'PH', nama: 'pH', satuan: '', tipe_nilai: 'ANGKA', nilai_min: '0.0000', nilai_max: '14.0000', aktif: true },
  { id: 5, kode: 'BRIX', nama: 'Kadar gula', satuan: '°Bx', tipe_nilai: 'ANGKA', nilai_min: '0.0000', nilai_max: '90.0000', aktif: true },
  { id: 6, kode: 'VISKOSITAS', nama: 'Viskositas', satuan: 'cP', tipe_nilai: 'ANGKA', nilai_min: null, nilai_max: null, aktif: true },
  { id: 7, kode: 'WARNA', nama: 'Warna', satuan: '', tipe_nilai: 'TEKS', nilai_min: null, nilai_max: null, aktif: true },
  { id: 8, kode: 'LULUS_UJI', nama: 'Lulus uji organoleptik', satuan: '', tipe_nilai: 'BOOL', nilai_min: null, nilai_max: null, aktif: true },
]

// =========================================================
// SESI
// =========================================================

const SESI = [
  {
    id: 1,
    nomor: 'SESI/PCJM/2026/VIII/001',
    tanggal: '2026-08-04',
    jenis_sesi: 'PRODUKSI',
    status: 'BERJALAN',
    grup_bahan: 1,
    grup_bahan_kode: 'PT',
    resep: 1,
    resep_label: 'TEH-KMS v3',
    produk_jadi: 10,
    produk_jadi_kode: 'TEH-KMS',
    produk_jadi_nama: 'Teh Kemasan 250ml',
    qty_target: '2000.000',
    qty_hasil: '0.000',
    susut: '2000.000',
    rendemen: '0.000',
    satuan_kode: 'pcs',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: null,
    entitas_penanggung_kode: null,
    entitas_penanggung_nama: null,
    hasil_masuk_pool: true,
    catatan: '',
    dimulai_pada: new Date(Date.now() - 74 * 60_000).toISOString(),
    dibuat_oleh_nama: 'Rudi Hartono',
    dibuat_pada: '2026-08-04T06:10:00+07:00',
    input: [
      { id: 1, bahan: 11, bahan_kode: 'TEH-CLP', bahan_nama: 'Teh Celup', qty_rencana: '2000.000', qty_aktual: '2000.000', selisih: '0.000', satuan_kode: 'pcs', tangki: null, tangki_kode: null },
      { id: 2, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '4.000', qty_aktual: '4.120', selisih: '0.120', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 2,
    nomor: 'SESI/CVSA/2026/VIII/002',
    tanggal: '2026-08-03',
    jenis_sesi: 'RND',
    status: 'BERJALAN',
    grup_bahan: 2,
    grup_bahan_kode: 'BERSAMA',
    resep: null,
    resep_label: null,
    produk_jadi: 13,
    produk_jadi_kode: 'SIR-JHE',
    produk_jadi_nama: 'Sirup Jahe (percobaan)',
    qty_target: '5.000',
    qty_hasil: '0.000',
    susut: '5.000',
    rendemen: '0.000',
    satuan_kode: 'kg',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: 2,
    entitas_penanggung_kode: 'CVSA',
    entitas_penanggung_nama: 'CV Sumber Alam',
    hasil_masuk_pool: false,
    catatan: 'Percobaan rasio jahe : gula 1 : 3, target lebih pekat dari trial sebelumnya.',
    dimulai_pada: new Date(Date.now() - 26 * 60_000).toISOString(),
    dibuat_oleh_nama: 'Sri Wahyuni',
    dibuat_pada: '2026-08-03T08:00:00+07:00',
    input: [
      { id: 3, bahan: 14, bahan_kode: 'JHE-EKS', bahan_nama: 'Ekstrak Jahe', qty_rencana: '1.500', qty_aktual: '1.480', selisih: '-0.020', satuan_kode: 'kg', tangki: null, tangki_kode: null },
      { id: 4, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '4.500', qty_aktual: '4.500', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 3,
    nomor: 'SESI/CVSA/2026/VIII/003',
    tanggal: '2026-08-01',
    jenis_sesi: 'RND',
    status: 'SELESAI',
    grup_bahan: 2,
    grup_bahan_kode: 'BERSAMA',
    resep: null,
    resep_label: null,
    produk_jadi: 13,
    produk_jadi_kode: 'SIR-JHE',
    produk_jadi_nama: 'Sirup Jahe (percobaan)',
    qty_target: '5.000',
    qty_hasil: '5.400',
    susut: '-0.400',
    rendemen: '1.080',
    satuan_kode: 'kg',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: 2,
    entitas_penanggung_kode: 'CVSA',
    entitas_penanggung_nama: 'CV Sumber Alam',
    hasil_masuk_pool: false,
    catatan: 'Trial berhasil. Kandidat kuat untuk dipromosikan jadi resep.',
    dimulai_pada: '2026-08-01T07:30:00+07:00',
    dibuat_oleh_nama: 'Sri Wahyuni',
    dibuat_pada: '2026-08-01T07:05:00+07:00',
    input: [
      { id: 5, bahan: 14, bahan_kode: 'JHE-EKS', bahan_nama: 'Ekstrak Jahe', qty_rencana: '1.200', qty_aktual: '1.250', selisih: '0.050', satuan_kode: 'kg', tangki: null, tangki_kode: null },
      { id: 6, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '4.000', qty_aktual: '4.000', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 4,
    nomor: 'SESI/CVSA/2026/VII/018',
    tanggal: '2026-07-28',
    jenis_sesi: 'RND',
    status: 'GAGAL',
    grup_bahan: 2,
    grup_bahan_kode: 'BERSAMA',
    resep: null,
    resep_label: null,
    produk_jadi: 13,
    produk_jadi_kode: 'SIR-JHE',
    produk_jadi_nama: 'Sirup Jahe (percobaan)',
    qty_target: '5.000',
    qty_hasil: '0.000',
    susut: '5.000',
    rendemen: '0.000',
    satuan_kode: 'kg',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: 2,
    entitas_penanggung_kode: 'CVSA',
    entitas_penanggung_nama: 'CV Sumber Alam',
    hasil_masuk_pool: false,
    catatan: 'Karamelisasi berlebih, seluruh batch gosong.\n[GAGAL] Suhu naik tak terkendali saat pengaduk mati.',
    dimulai_pada: '2026-07-28T09:00:00+07:00',
    dibuat_oleh_nama: 'Sri Wahyuni',
    dibuat_pada: '2026-07-28T08:40:00+07:00',
    nilai_kerugian: '1875000.00',
    kategori_kegagalan: 'PROSES',
    input: [
      { id: 7, bahan: 14, bahan_kode: 'JHE-EKS', bahan_nama: 'Ekstrak Jahe', qty_rencana: '1.500', qty_aktual: '1.500', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
      { id: 8, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '4.500', qty_aktual: '4.500', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 5,
    nomor: 'SESI/PCJM/2026/VIII/004',
    tanggal: '2026-08-04',
    jenis_sesi: 'PRODUKSI',
    status: 'DRAFT',
    grup_bahan: 1,
    grup_bahan_kode: 'PT',
    resep: 1,
    resep_label: 'TEH-KMS v3',
    produk_jadi: 10,
    produk_jadi_kode: 'TEH-KMS',
    produk_jadi_nama: 'Teh Kemasan 250ml',
    qty_target: '1500.000',
    qty_hasil: '0.000',
    susut: '1500.000',
    rendemen: '0.000',
    satuan_kode: 'pcs',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: null,
    entitas_penanggung_kode: null,
    entitas_penanggung_nama: null,
    hasil_masuk_pool: true,
    catatan: '',
    dimulai_pada: null,
    dibuat_oleh_nama: 'Rudi Hartono',
    dibuat_pada: '2026-08-04T07:50:00+07:00',
    input: [
      { id: 9, bahan: 11, bahan_kode: 'TEH-CLP', bahan_nama: 'Teh Celup', qty_rencana: '1500.000', qty_aktual: '1500.000', selisih: '0.000', satuan_kode: 'pcs', tangki: null, tangki_kode: null },
      { id: 10, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '3.000', qty_aktual: '3.000', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 6,
    nomor: 'SESI/PCJM/2026/VIII/005',
    tanggal: '2026-08-02',
    jenis_sesi: 'PRODUKSI',
    status: 'SELESAI',
    grup_bahan: 1,
    grup_bahan_kode: 'PT',
    resep: 1,
    resep_label: 'TEH-KMS v3',
    produk_jadi: 10,
    produk_jadi_kode: 'TEH-KMS',
    produk_jadi_nama: 'Teh Kemasan 250ml',
    qty_target: '3000.000',
    qty_hasil: '2880.000',
    susut: '120.000',
    rendemen: '0.960',
    satuan_kode: 'pcs',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: null,
    entitas_penanggung_kode: null,
    entitas_penanggung_nama: null,
    hasil_masuk_pool: true,
    catatan: '',
    dimulai_pada: '2026-08-02T07:15:00+07:00',
    dibuat_oleh_nama: 'Rudi Hartono',
    dibuat_pada: '2026-08-02T07:00:00+07:00',
    input: [
      { id: 11, bahan: 11, bahan_kode: 'TEH-CLP', bahan_nama: 'Teh Celup', qty_rencana: '3000.000', qty_aktual: '3000.000', selisih: '0.000', satuan_kode: 'pcs', tangki: null, tangki_kode: null },
      { id: 12, bahan: 12, bahan_kode: 'GULA', bahan_nama: 'Gula Kristal Putih', qty_rencana: '6.000', qty_aktual: '6.050', selisih: '0.050', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
  {
    id: 7,
    nomor: 'SESI/CVSA/2026/VII/012',
    tanggal: '2026-07-20',
    jenis_sesi: 'RND',
    status: 'BATAL',
    grup_bahan: 2,
    grup_bahan_kode: 'BERSAMA',
    resep: null,
    resep_label: null,
    produk_jadi: 13,
    produk_jadi_kode: 'SIR-JHE',
    produk_jadi_nama: 'Sirup Jahe (percobaan)',
    qty_target: '3.000',
    qty_hasil: '0.000',
    susut: '3.000',
    rendemen: '0.000',
    satuan_kode: 'kg',
    tangki_hasil: null,
    tangki_hasil_kode: null,
    entitas_penanggung: 3,
    entitas_penanggung_kode: 'AGS',
    entitas_penanggung_nama: 'Agus Santoso',
    hasil_masuk_pool: false,
    catatan: '[BATAL] Ekstrak jahe belum datang, dijadwalkan ulang.',
    dimulai_pada: null,
    dibuat_oleh_nama: 'Sri Wahyuni',
    dibuat_pada: '2026-07-20T08:00:00+07:00',
    input: [
      { id: 13, bahan: 14, bahan_kode: 'JHE-EKS', bahan_nama: 'Ekstrak Jahe', qty_rencana: '0.900', qty_aktual: '0.900', selisih: '0.000', satuan_kode: 'kg', tangki: null, tangki_kode: null },
    ],
  },
]

const ringkas = (s) => ({
  id: s.id, nomor: s.nomor, tanggal: s.tanggal, jenis_sesi: s.jenis_sesi,
  status: s.status, grup_bahan_kode: s.grup_bahan_kode,
  produk_jadi_kode: s.produk_jadi_kode, produk_jadi_nama: s.produk_jadi_nama,
  qty_target: s.qty_target, qty_hasil: s.qty_hasil, rendemen: s.rendemen,
  satuan_kode: s.satuan_kode, hasil_masuk_pool: s.hasil_masuk_pool,
  entitas_penanggung_kode: s.entitas_penanggung_kode,
  dibuat_oleh_nama: s.dibuat_oleh_nama,
})

// =========================================================
// PENGUKURAN & CATATAN
// =========================================================

const jam = (h, m) => `2026-08-0${h}T${String(m).padStart(2, '0')}:00+07:00`

const PENGUKURAN = [
  // Sesi 2 — RND berjalan
  { id: 1, sesi: 2, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '78.0000', nilai_teks: '', urutan: 0, waktu: jam(3, 15), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 2, sesi: 2, tahap: 'PROSES', nama: 3, nama_kode: 'RPM', nama_label: 'Kecepatan aduk', satuan: 'rpm', nilai: '400.0000', nilai_teks: '', urutan: 0, waktu: jam(3, 16), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 3, sesi: 2, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '86.5000', nilai_teks: '', urutan: 1, waktu: jam(3, 42), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 4, sesi: 2, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '84.0000', nilai_teks: '', urutan: 2, waktu: jam(3, 44), catatan: 'Salah baca termometer, yang benar 84.', mengoreksi: 3, dicatat_oleh_nama: 'Sri Wahyuni' },

  // Sesi 3 — RND selesai, berhasil
  { id: 10, sesi: 3, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '82.0000', nilai_teks: '', urutan: 0, waktu: jam(1, 45), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 11, sesi: 3, tahap: 'PROSES', nama: 2, nama_kode: 'DURASI', nama_label: 'Durasi', satuan: 'menit', nilai: '95.0000', nilai_teks: '', urutan: 0, waktu: jam(1, 50), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 12, sesi: 3, tahap: 'PROSES', nama: 3, nama_kode: 'RPM', nama_label: 'Kecepatan aduk', satuan: 'rpm', nilai: '400.0000', nilai_teks: '', urutan: 0, waktu: jam(1, 52), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 13, sesi: 3, tahap: 'UJI', nama: 5, nama_kode: 'BRIX', nama_label: 'Kadar gula', satuan: '°Bx', nilai: '64.0000', nilai_teks: '', urutan: 0, waktu: jam(2, 10), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Lab QC' },
  { id: 14, sesi: 3, tahap: 'UJI', nama: 4, nama_kode: 'PH', nama_label: 'pH', satuan: '', nilai: '4.2000', nilai_teks: '', urutan: 0, waktu: jam(2, 12), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Lab QC' },
  { id: 15, sesi: 3, tahap: 'UJI', nama: 7, nama_kode: 'WARNA', nama_label: 'Warna', satuan: '', nilai: null, nilai_teks: 'Kuning keemasan jernih', urutan: 0, waktu: jam(2, 14), catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Lab QC' },

  // Sesi 4 — RND gagal
  { id: 20, sesi: 4, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '104.0000', nilai_teks: '', urutan: 0, waktu: '2026-07-28T10:20:00+07:00', catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 21, sesi: 4, tahap: 'PROSES', nama: 2, nama_kode: 'DURASI', nama_label: 'Durasi', satuan: 'menit', nilai: '120.0000', nilai_teks: '', urutan: 0, waktu: '2026-07-28T11:00:00+07:00', catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 22, sesi: 4, tahap: 'PROSES', nama: 3, nama_kode: 'RPM', nama_label: 'Kecepatan aduk', satuan: 'rpm', nilai: '0.0000', nilai_teks: '', urutan: 0, waktu: '2026-07-28T10:35:00+07:00', catatan: 'Pengaduk mati.', mengoreksi: null, dicatat_oleh_nama: 'Sri Wahyuni' },
  { id: 23, sesi: 4, tahap: 'UJI', nama: 7, nama_kode: 'WARNA', nama_label: 'Warna', satuan: '', nilai: null, nilai_teks: 'Coklat gelap, gosong', urutan: 0, waktu: '2026-07-28T12:00:00+07:00', catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Lab QC' },

  // Sesi 6 — produksi rutin, QC juga dicatat
  { id: 30, sesi: 6, tahap: 'PROSES', nama: 1, nama_kode: 'SUHU', nama_label: 'Suhu', satuan: '°C', nilai: '90.0000', nilai_teks: '', urutan: 0, waktu: '2026-08-02T07:40:00+07:00', catatan: '', mengoreksi: null, dicatat_oleh_nama: 'Rudi Hartono' },
]

const CATATAN = [
  { id: 1, sesi: 2, waktu: jam(3, 20), teks: 'Aroma jahe mulai keluar lebih cepat dari trial sebelumnya.', penulis_nama: 'Sri Wahyuni' },
  { id: 2, sesi: 2, waktu: jam(3, 45), teks: 'Warna masih terlalu pucat dibanding target. Pertimbangkan menaikkan durasi.', penulis_nama: 'Sri Wahyuni' },
  { id: 10, sesi: 3, waktu: jam(1, 55), teks: 'Konsistensi pas, tidak menggumpal sama sekali di menit 90.', penulis_nama: 'Sri Wahyuni' },
  { id: 11, sesi: 3, waktu: jam(2, 20), teks: 'Panel uji rasa: 4 dari 5 memilih batch ini dibanding trial 2026/VII/018.', penulis_nama: 'Lab QC' },
  { id: 20, sesi: 4, waktu: '2026-07-28T10:40:00+07:00', teks: 'Pengaduk berhenti, suhu melonjak dalam 5 menit. Tidak sempat diselamatkan.', penulis_nama: 'Sri Wahyuni' },
]

// =========================================================
// HELPER — dipanggil composable, satu per fungsi
// =========================================================

let urutBaru = 900

export const fxSesiList = async (params = {}) => {
  await jeda()
  let hasil = SESI.map(ringkas)
  if (params.status) hasil = hasil.filter((s) => s.status === params.status)
  if (params.jenis_sesi) hasil = hasil.filter((s) => s.jenis_sesi === params.jenis_sesi)
  if (params.search) {
    const q = String(params.search).toLowerCase()
    hasil = hasil.filter((s) =>
      s.nomor.toLowerCase().includes(q) || s.produk_jadi_kode.toLowerCase().includes(q))
  }
  return { data: halaman(hasil) }
}

export const fxSesiDetail = async (id) => {
  await jeda()
  const s = SESI.find((x) => x.id === Number(id))
  if (!s) throw Object.assign(new Error('404'), { response: { status: 404, data: {} } })
  return { data: s }
}

export const fxSesiBuat = async (payload) => {
  await jeda(320)
  return {
    data: {
      ...SESI[4],
      id: ++urutBaru,
      nomor: `SESI/PCJM/2026/VIII/${String(urutBaru).slice(-3)}`,
      status: 'DRAFT',
      jenis_sesi: payload.jenis_sesi ?? 'PRODUKSI',
      qty_target: String(payload.qty_target ?? '0'),
      catatan: payload.catatan ?? '',
    },
  }
}

export const fxSesiAksi = async (id, aksi, payload = {}) => {
  await jeda(320)
  const s = SESI.find((x) => x.id === Number(id))
  const peta = { mulai: 'BERJALAN', selesaikan: 'SELESAI', gagalkan: 'GAGAL', batalkan: 'BATAL' }
  return {
    data: {
      ...s,
      status: peta[aksi] ?? s.status,
      qty_hasil: aksi === 'selesaikan' ? String(payload.qty_hasil ?? '0') : s.qty_hasil,
      dimulai_pada: aksi === 'mulai' ? new Date().toISOString() : s.dimulai_pada,
    },
  }
}

export const fxPratinjauKerugian = async (id) => {
  await jeda()
  const s = SESI.find((x) => x.id === Number(id))
  const rincian = (s?.input ?? []).map((i) => ({
    bahan_kode: i.bahan_kode,
    bahan_nama: i.bahan_nama,
    qty: i.qty_aktual,
    satuan_kode: i.satuan_kode,
    tarif: i.bahan_kode === 'JHE-EKS' ? '950000.00' : '18000.00',
    nilai: i.bahan_kode === 'JHE-EKS'
      ? (parseFloat(i.qty_aktual) * 950000).toFixed(2)
      : (parseFloat(i.qty_aktual) * 18000).toFixed(2),
  }))
  return {
    data: {
      nilai_kerugian: rincian.reduce((t, r) => t + parseFloat(r.nilai), 0).toFixed(2),
      entitas_penanggung: s?.entitas_penanggung
        ? { id: s.entitas_penanggung, kode: s.entitas_penanggung_kode, nama: s.entitas_penanggung_nama }
        : null,
      rincian,
    },
  }
}

export const fxBanding = async (ids = []) => {
  await jeda(260)
  const dipilih = SESI.filter((s) => ids.includes(String(s.id)) || ids.includes(s.id))

  // Baris parameter: union nama pengukuran dari semua sesi terpilih.
  const jenisTerpakai = []
  for (const s of dipilih) {
    for (const p of PENGUKURAN.filter((x) => x.sesi === s.id)) {
      if (!jenisTerpakai.some((j) => j.kode === p.nama_kode)) {
        jenisTerpakai.push({ kode: p.nama_kode, label: p.nama_label, satuan: p.satuan, tahap: p.tahap })
      }
    }
  }

  const nilaiTerakhir = (sesiId, kode) => {
    const cocok = PENGUKURAN
      .filter((p) => p.sesi === sesiId && p.nama_kode === kode)
      .sort((a, b) => new Date(a.waktu) - new Date(b.waktu))
    const p = cocok[cocok.length - 1]
    if (!p) return null
    return p.nilai !== null ? p.nilai : p.nilai_teks
  }

  // Baris bahan dinormalkan per unit hasil, supaya batch beda ukuran sebanding.
  const bahanTerpakai = []
  for (const s of dipilih) {
    for (const i of s.input) {
      if (!bahanTerpakai.some((b) => b.kode === i.bahan_kode)) {
        bahanTerpakai.push({ kode: i.bahan_kode, label: i.bahan_nama, satuan: i.satuan_kode })
      }
    }
  }
  const bahanPerUnit = (s, kode) => {
    const i = s.input.find((x) => x.bahan_kode === kode)
    if (!i) return null
    const hasil = parseFloat(s.qty_hasil) || parseFloat(s.qty_target)
    return hasil ? (parseFloat(i.qty_aktual) / hasil).toFixed(4) : null
  }

  return {
    data: {
      sesi: dipilih.map((s) => ({
        id: s.id, nomor: s.nomor, tanggal: s.tanggal, jenis_sesi: s.jenis_sesi,
        status: s.status, produk_jadi_kode: s.produk_jadi_kode,
        qty_target: s.qty_target, qty_hasil: s.qty_hasil,
        rendemen: s.rendemen, satuan_kode: s.satuan_kode,
      })),
      pengukuran: jenisTerpakai.map((j) => ({
        kode: j.kode, label: j.label, satuan: j.satuan, tahap: j.tahap,
        nilai: dipilih.map((s) => nilaiTerakhir(s.id, j.kode)),
      })),
      bahan_per_unit: bahanTerpakai.map((b) => ({
        kode: b.kode, label: b.label, satuan: b.satuan,
        nilai: dipilih.map((s) => bahanPerUnit(s, b.kode)),
      })),
    },
  }
}

export const fxKapasitas = async (params = {}) => {
  await jeda()
  const resep = RESEP.find((r) => r.produk_jadi === Number(params.produk) && r.aktif) ?? RESEP[0]
  const stok = { 'TEH-CLP': '4200.000', GULA: '52.400', 'JHE-EKS': '8.200' }
  const rincian = resep.item.map((i) => {
    const tersedia = parseFloat(stok[i.bahan_kode] ?? '0')
    const perUnit = parseFloat(i.qty) / parseFloat(resep.hasil_per_batch)
    return {
      bahan: i.bahan_kode, bahan_id: i.bahan, satuan_kode: i.satuan_kode,
      tersedia: tersedia.toFixed(3),
      per_unit: perUnit.toFixed(4),
      cukup_untuk: perUnit ? Math.floor(tersedia / perUnit).toFixed(3) : '0.000',
    }
  })
  const maksimum = Math.min(...rincian.map((r) => parseFloat(r.cukup_untuk)))
  return {
    data: {
      resep: `${resep.produk_jadi_kode} v${resep.versi}`,
      maksimum: maksimum.toFixed(3),
      pembatas: rincian.filter((r) => parseFloat(r.cukup_untuk) === maksimum).map((r) => r.bahan),
      rincian,
      sisa_bila_maksimum: Object.fromEntries(
        rincian.map((r) => [r.bahan, (parseFloat(r.tersedia) - maksimum * parseFloat(r.per_unit)).toFixed(3)]),
      ),
    },
  }
}

export const fxResepList = async () => {
  await jeda()
  return { data: halaman(RESEP.filter((r) => r.aktif)) }
}

export const fxJenisPengukuran = async () => {
  await jeda()
  return { data: halaman(JENIS_PENGUKURAN.filter((j) => j.aktif)) }
}

export const fxPengukuranList = async (sesiId) => {
  await jeda()
  return { data: PENGUKURAN.filter((p) => p.sesi === Number(sesiId)) }
}

export const fxPengukuranBuat = async (sesiId, payload) => {
  await jeda(220)
  const jenis = JENIS_PENGUKURAN.find((j) => j.id === Number(payload.nama))
  const baris = {
    id: ++urutBaru,
    sesi: Number(sesiId),
    tahap: payload.tahap ?? 'PROSES',
    nama: Number(payload.nama),
    nama_kode: jenis?.kode ?? '?',
    nama_label: jenis?.nama ?? '?',
    satuan: jenis?.satuan ?? '',
    nilai: payload.nilai != null && payload.nilai !== '' ? Number(payload.nilai).toFixed(4) : null,
    nilai_teks: payload.nilai_teks ?? '',
    urutan: PENGUKURAN.filter((p) => p.sesi === Number(sesiId) && p.nama === Number(payload.nama)).length,
    waktu: payload.waktu ?? new Date().toISOString(),
    catatan: payload.catatan ?? '',
    mengoreksi: payload.mengoreksi ?? null,
    dicatat_oleh_nama: 'Anda',
  }
  PENGUKURAN.push(baris)
  return { data: baris }
}

export const fxCatatanList = async (sesiId) => {
  await jeda()
  return { data: CATATAN.filter((c) => c.sesi === Number(sesiId)) }
}

export const fxCatatanBuat = async (sesiId, payload) => {
  await jeda(220)
  const baris = {
    id: ++urutBaru,
    sesi: Number(sesiId),
    waktu: payload.waktu ?? new Date().toISOString(),
    teks: payload.teks,
    penulis_nama: 'Anda',
  }
  CATATAN.push(baris)
  return { data: baris }
}

export const fxGrupBahan = async () => {
  await jeda()
  return { data: halaman(GRUP_BAHAN) }
}

export const fxEntitas = async () => {
  await jeda()
  return { data: halaman(ENTITAS) }
}

export const fxProduk = async (params = {}) => {
  await jeda()
  const hasil = params.jenis ? PRODUK.filter((p) => p.jenis === params.jenis) : PRODUK
  return { data: halaman(hasil) }
}
